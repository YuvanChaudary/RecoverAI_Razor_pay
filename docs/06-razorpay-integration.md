# Razorpay API & Webhook Integration Specification
**Project:** Razorpay AI Buildathon (Track 3)  
**Document ID:** `docs/06-razorpay-integration.md`  
**Status:** Approved Architectural Baseline  

---

## Executive Summary

This document specifies the integration specification between the **AI Revenue Recovery Agent** and Razorpay's payment infrastructure. Operating within the Razorpay Test Environment, the system consumes subscription and payment failure webhooks, parses raw decline telemetry, maps error codes to a deterministic failure taxonomy, and executes bounded recovery actions via Razorpay REST APIs using strict idempotency and rate-limiting controls.

---

## 1. Environment & Authentication

### 1.1 Operating Environment
The integration operates strictly in the **Razorpay Test Environment** (`https://api.razorpay.com/v1`). All payment instruments, subscription mandates, and webhooks use synthetic test credentials provided by Razorpay.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         AUTHENTICATION SCHEME                            │
├──────────────────────────┬───────────────────────────────────────────────┤
│ Direction                │ Authentication Mechanism                      │
├──────────────────────────┼───────────────────────────────────────────────┤
│ Outbound (Agent ──► RZP) │ HTTP Basic Auth (`Key_ID:Key_Secret`)         │
│ Inbound  (RZP ──► Agent) │ HMAC SHA256 Header (`X-Razorpay-Signature`)   │
└──────────────────────────┴───────────────────────────────────────────────┘
```

### 1.2 Outbound API Authentication (Basic Auth)
Every outbound request from the Agent's Action Dispatcher to Razorpay APIs uses HTTP Basic Authentication over TLS:
```http
Authorization: Basic <base64(KEY_ID:KEY_SECRET)>
```
* **Environment Variables:** `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`

### 1.3 Inbound Webhook Authentication (HMAC SHA256)
Every inbound HTTP POST received at `/webhooks/razorpay` is verified against spoofing:
1. Extract raw request payload bytes.
2. Compute SHA256 HMAC digest using `RAZORPAY_WEBHOOK_SECRET`.
3. Compare against `X-Razorpay-Signature` using constant-time string comparison (`hmac.compare_digest`).

```python
import hmac
import hashlib

def verify_razorpay_webhook(raw_payload: bytes, signature: str, secret: str) -> bool:
    expected_sig = hmac.new(
        key=secret.encode('utf-8'),
        msg=raw_payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, signature)
```

---

## 2. Webhook Ingestion (The Triggers)

The system listens for specific Razorpay events that indicate subscription charge failures or mandate halts:

1. `subscription.charged.failed`: Dispatched when an automated recurring auto-debit attempt fails.
2. `payment.failed`: Dispatched when an individual payment transaction is declined.
3. `subscription.halted`: Dispatched when a subscription reaches maximum automatic retry attempts and is paused by Razorpay.

### Realistic Webhook Payload Example (`subscription.charged.failed`)

```json
{
  "entity": "event",
  "account_id": "acc_PZ000000000001",
  "event": "subscription.charged.failed",
  "contains": ["payment", "subscription", "invoice"],
  "created_at": 1724180400,
  "payload": {
    "payment": {
      "entity": {
        "id": "pay_PZ182x9A7kL3mQ",
        "amount": 299900,
        "currency": "INR",
        "status": "failed",
        "order_id": "order_PZ177a8B9cD0eF",
        "invoice_id": "inv_PZ166x1Y2z3A4B",
        "international": false,
        "method": "card",
        "card_id": "card_PZ155m6N7o8P9Q",
        "bank": "HDFC",
        "error_code": "BAD_REQUEST_ERROR",
        "error_description": "Payment failed due to insufficient funds in customer account",
        "error_source": "issuing_bank",
        "error_step": "payment_authorization",
        "error_reason": "insufficient_funds"
      }
    },
    "subscription": {
      "entity": {
        "id": "sub_PZ100s1T2u3V4W",
        "plan_id": "plan_PZ099a8B7c6D5E",
        "customer_id": "cust_PZ088x9Y0z1A2B",
        "status": "active",
        "current_start": 1724180400,
        "current_end": 1726858800,
        "charge_at": 1724180400,
        "paid_count": 5,
        "remaining_count": 7
      }
    },
    "invoice": {
      "entity": {
        "id": "inv_PZ166x1Y2z3A4B",
        "subscription_id": "sub_PZ100s1T2u3V4W",
        "amount": 299900,
        "status": "issued",
        "billing_start": 1724180400,
        "billing_end": 1726858800
      }
    }
  }
}
```

#### Key Parsed Diagnostic Telemetry Fields
* `payload.payment.entity.error_code`: High-level error classification (`BAD_REQUEST_ERROR`, `GATEWAY_ERROR`).
* `payload.payment.entity.error_source`: Entity originating the decline (`issuing_bank`, `gateway`, `network`).
* `payload.payment.entity.error_step`: Processing stage where failure occurred (`payment_authorization`, `pre_debit_notification`).
* `payload.payment.entity.error_reason`: Specific granular failure reason (`insufficient_funds`, `expired_card`, `payment_declined_by_bank`).

---

## 3. Decline Code Taxonomy Mapping

The Diagnosis Engine maps raw Razorpay telemetry into standardized root-cause categories:

| Raw Razorpay `error_code` | Raw `error_reason` | `error_source` | Internal Root Cause Category | Strategic Diagnosis & Action Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `BAD_REQUEST_ERROR` | `insufficient_funds` | `issuing_bank` | `LIQUIDITY_FRICTION` | Soft decline. Schedule payday-aligned retry (72h delay) + gentle Hinglish WhatsApp reminder. |
| `GATEWAY_ERROR` | `gateway_timeout` | `gateway` | `TRANSIENT_INFRASTRUCTURE` | Soft decline. Immediate short delay retry (2–4 hours) after CBS/switch recovery. |
| `BAD_REQUEST_ERROR` | `expired_card` | `issuing_bank` | `INSTRUMENT_INVALIDATION` | Hard decline. Automated retries halted. Dispatch Razorpay Payment Link to update instrument. |
| `BAD_REQUEST_ERROR` | `card_expired` | `network` | `INSTRUMENT_INVALIDATION` | Hard decline. Halt retries. Trigger mandate repair / payment link workflow. |
| `BAD_REQUEST_ERROR` | `payment_declined_by_bank`| `issuing_bank` | `BANK_RISK_BLOCK` | Soft/Hard decline. Delay retry 48 hours + issue direct customer notification link. |
| `BAD_REQUEST_ERROR` | `pre_debit_notice_failed` | `razorpay` | `MANDATE_COMPLIANCE_LOCK` | Regulatory block. Pre-debit notice must be re-issued; wait 24h prior to retry. |
| `BAD_REQUEST_ERROR` | `mandate_limit_exceeded` | `issuing_bank` | `MANDATE_COMPLIANCE_LOCK` | Compliance lock. Amount exceeds mandate cap. Issue manual Razorpay Payment Link. |

---

## 4. Action Execution APIs

Upon OPA policy approval, the Action Dispatcher executes recoveries via the following Razorpay REST APIs:

### 4.1 Retry Subscription Invoice Charge
Triggers a manual retry execution for a failed subscription invoice.

* **HTTP Method & Path:** `POST /v1/invoices/{invoice_id}/retry`
* **Headers:** 
  * `Authorization: Basic <credentials>`
  * `Content-Type: application/json`
  * `X-Razorpay-Idempotency-Key: <unique_saga_execution_id>`

#### Request Body
```json
{
  "payment_method": "card"
}
```

#### Response Body (200 OK - Charge Initiated)
```json
{
  "id": "inv_PZ166x1Y2z3A4B",
  "entity": "invoice",
  "subscription_id": "sub_PZ100s1T2u3V4W",
  "status": "pending",
  "amount": 299900,
  "paid_amount": 0,
  "payment_id": "pay_PZ999_RECOVERED",
  "attempts": 2
}
```

---

### 4.2 Create Razorpay Payment Link (Instrument Swap / Mandate Repair)
Generates an explicit, customer-facing payment link for manual recovery when automated card retries fail or instrument is expired.

* **HTTP Method & Path:** `POST /v1/payment_links`
* **Headers:**
  * `Authorization: Basic <credentials>`
  * `Content-Type: application/json`
  * `X-Razorpay-Idempotency-Key: <unique_saga_execution_id>`

#### Request Body
```json
{
  "amount": 299900,
  "currency": "INR",
  "accept_partial": false,
  "description": "Subscription Payment Recovery for Invoice #inv_PZ166x1Y2z3A4B",
  "customer": {
    "name": "Rajesh Sharma",
    "contact": "+919876543210",
    "email": "rajesh.sharma@example.com"
  },
  "notify": {
    "sms": false,
    "email": false
  },
  "reminder_enable": true,
  "notes": {
    "subscription_id": "sub_PZ100s1T2u3V4W",
    "recovery_case_id": "case_rec_01J8A9X4K2M3N4P5"
  },
  "callback_url": "https://merchant.com/subscription/success",
  "callback_method": "get"
}
```

#### Response Body (200 OK - Link Created)
```json
{
  "id": "plink_PZ888_LINK_ID",
  "entity": "payment_link",
  "short_url": "https://rzp.io/i/rec_demo123",
  "status": "created",
  "amount": 299900,
  "amount_paid": 0,
  "customer": {
    "name": "Rajesh Sharma",
    "contact": "+919876543210",
    "email": "rajesh.sharma@example.com"
  },
  "created_at": 1724180410
}
```

---

## 5. Idempotency & Rate Limiting Controls

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      IDEMPOTENCY & RATE LIMITING                         │
├──────────────────────────────────────────────────────────────────────────┤
│ Idempotency Header : X-Razorpay-Idempotency-Key: <event_id>_<attempt>   │
│ Rate Limit Handling: HTTP 429 ──► Temporal Exponential Jitter Backoff    │
└──────────────────────────────────────────────────────────────────────────┘
```

### 5.1 Strict Idempotency Guarantees
To prevent double-charging a subscriber under network retries or process restarts:
1. Every outbound write request (`POST /v1/invoices/{id}/retry`, `POST /v1/payment_links`) includes the idempotency header:
   ```http
   X-Razorpay-Idempotency-Key: rec_idemp_evt_01J8A9X4K2M3N4P5_attempt_1
   ```
2. The idempotency key is derived deterministically from `event_id` + `retry_attempt_number`.
3. If a network timeout occurs and Temporal re-executes the API activity, Razorpay returns the cached original response without creating duplicate invoices or double charges.

### 5.2 Rate Limiting & Backoff Policy (HTTP 429)
Razorpay enforces API rate limits per merchant key. If the system encounters an `HTTP 429 Too Many Requests` response:
* **Rate Limit Response Headers:**
  * `X-RateLimit-Limit`: Maximum requests per window.
  * `X-RateLimit-Remaining`: Remaining request quota.
  * `X-RateLimit-Reset`: UTC epoch timestamp when quota resets.
* **Temporal Retry Policy:**
  * **Initial Interval:** 2 seconds.
  * **Backoff Coefficient:** 2.0 (Exponential backoff).
  * **Maximum Interval:** 60 seconds.
  * **Jitter:** 15% randomized jitter to prevent thundering herd spikes.

---

## 6. Document Metadata & Sign-off

* **Author:** Fintech System Architect / Track 3 Engineering Team  
* **Target Buildathon:** Razorpay AI Buildathon — Track 3 (AI Revenue Recovery)  
* **Upstream Specification:** `docs/01-problem-statement.md`, `docs/03-system-architecture.md`, `docs/05-api-contract.md`  
* **Implementation Artifacts:** `docs/06-razorpay-integration.md`  
