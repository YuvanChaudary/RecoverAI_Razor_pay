# REST API Contract Specification: AI Revenue Recovery Agent
**Project:** Razorpay AI Buildathon (Track 3)  
**Document ID:** `docs/05-api-contract.md`  
**Status:** Approved Architectural Baseline  

---

## Executive Summary

This document specifies the REST API contract for the **AI Revenue Recovery Agent**. It details the endpoint schemas, request/response models, authentication headers, error envelopes, and data structures interfacing the FastAPI backend, the React + Vite frontend dashboard, and external Razorpay webhooks.

---

## 1. Overview & General Standards

### 1.1 Base URL & Environment
* **Production Base URL:** `https://api.recovery.merchant.com/api/v1`
* **Webhook Endpoint Base:** `https://api.recovery.merchant.com/webhooks`

### 1.2 Authentication & Security
1. **External Webhooks (`/webhooks/*`):** Authenticated using Razorpay HMAC SHA256 signature verification via the `X-Razorpay-Signature` request header.
2. **Internal Management APIs (`/api/v1/*`):** Authenticated using standard HTTP Bearer JWT tokens via `Authorization: Bearer <token>`.

### 1.3 Standard Response Envelope
All API responses adhere to a consistent JSON envelope:

#### Success Response Envelope (HTTP 200 / 201 / 202)
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "timestamp": 1724180400,
    "request_id": "req_01J8A9X4K2M3N4P5"
  }
}
```

#### Error Response Envelope (HTTP 4xx / 5xx)
```json
{
  "success": false,
  "error": {
    "code": "INVALID_SIGNATURE",
    "message": "The provided HMAC signature did not match the computed body hash.",
    "details": []
  },
  "metadata": {
    "timestamp": 1724180400,
    "request_id": "req_01J8A9X4K2M3N4P5"
  }
}
```

---

## 2. Webhook Ingestion API

### `POST /webhooks/razorpay`
Ingests real-time webhook events dispatched by Razorpay (`payment.failed`, `subscription.halted`, `mandate.paused`).

* **Authentication:** Webhook HMAC SHA256 Verification
* **Target SLA:** $< 50\text{ms}$ execution time (Enqueues payload to Redpanda asynchronously and returns `200 OK`).

#### Request Headers
| Header Name | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `Content-Type` | `string` | Yes | Must be `application/json` |
| `X-Razorpay-Signature` | `string` | Yes | SHA256 HMAC signature of raw request body |

#### Request Body Example (`payment.failed`)
```json
{
  "entity": "event",
  "account_id": "acc_PZ000000000001",
  "event": "payment.failed",
  "contains": ["payment", "subscription"],
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
    }
  }
}
```

#### Response Body (200 OK)
```json
{
  "success": true,
  "data": {
    "received": true,
    "event_id": "evt_01J8A9X4K2M3N4P5Q6R7S8T9U0",
    "status": "QUEUED"
  },
  "metadata": {
    "timestamp": 1724180400,
    "request_id": "req_01J8A9X4K2M3N4P5"
  }
}
```

#### Response Body (401 Unauthorized - Invalid Signature)
```json
{
  "success": false,
  "error": {
    "code": "HMAC_VERIFICATION_FAILED",
    "message": "Signature verification failed. X-Razorpay-Signature header mismatch.",
    "details": []
  },
  "metadata": {
    "timestamp": 1724180400,
    "request_id": "req_01J8A9X4K2M3N4P5"
  }
}
```

---

## 3. Dashboard & Metrics APIs (React Frontend)

### 3.1 `GET /api/v1/metrics/overview`
Returns high-level aggregate financial recovery metrics for the Finance Controller Dashboard.

* **Authentication:** Bearer JWT

#### Request Headers
| Header Name | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `Authorization` | `string` | Yes | `Bearer <jwt_token>` |

#### Query Parameters
* `timeframe` (optional, enum: `24h`, `7d`, `30d`, `all`; default: `30d`)

#### Response Body (200 OK)
```json
{
  "success": true,
  "data": {
    "timeframe": "30d",
    "total_revenue_at_risk_inr": 4850000.00,
    "total_recovered_revenue_inr": 3152500.00,
    "recovery_rate_percentage": 65.00,
    "baseline_recovery_rate_percentage": 18.20,
    "recovery_lift_percentage": 257.14,
    "active_recovery_sagas": 42,
    "total_cases_processed": 500,
    "total_opa_compliance_violations": 0,
    "net_roi_multiplier": 8.4
  },
  "metadata": {
    "timestamp": 1724180400,
    "request_id": "req_01J8A9X4K2M3N4P6"
  }
}
```

---

### 3.2 `GET /api/v1/metrics/breakdown`
Returns recovery performance broken down by diagnostic failure category.

* **Authentication:** Bearer JWT

#### Response Body (200 OK)
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "category": "LIQUIDITY_FRICTION",
        "description": "Insufficient Funds (NSF)",
        "cases_count": 225,
        "revenue_at_risk_inr": 2250000.00,
        "recovered_revenue_inr": 1687500.00,
        "recovery_rate_percentage": 75.00,
        "avg_time_to_recovery_hours": 44.5
      },
      {
        "category": "TRANSIENT_INFRASTRUCTURE",
        "description": "Bank CBS / Switch Timeout",
        "cases_count": 125,
        "revenue_at_risk_inr": 1250000.00,
        "recovered_revenue_inr": 1125000.00,
        "recovery_rate_percentage": 90.00,
        "avg_time_to_recovery_hours": 3.2
      },
      {
        "category": "INSTRUMENT_INVALIDATION",
        "description": "Expired / Cancelled Card Token",
        "cases_count": 75,
        "revenue_at_risk_inr": 750000.00,
        "recovered_revenue_inr": 300000.00,
        "recovery_rate_percentage": 40.00,
        "avg_time_to_recovery_hours": 78.0
      },
      {
        "category": "MANDATE_COMPLIANCE_LOCK",
        "description": "Pre-debit Notice Missing / Cap Breached",
        "cases_count": 75,
        "revenue_at_risk_inr": 600000.00,
        "recovered_revenue_inr": 40000.00,
        "recovery_rate_percentage": 6.67,
        "avg_time_to_recovery_hours": 12.0
      }
    ]
  },
  "metadata": {
    "timestamp": 1724180400,
    "request_id": "req_01J8A9X4K2M3N4P7"
  }
}
```

---

## 4. Case Management & Audit APIs

### 4.1 `GET /api/v1/cases`
Returns a paginated list of failed subscription cases with filter capabilities.

* **Authentication:** Bearer JWT

#### Query Parameters
* `page` (integer, default: `1`)
* `limit` (integer, default: `20`, max: `100`)
* `status` (optional, enum: `PENDING`, `IN_RECOVERY`, `RECOVERED`, `GOVERNANCE_BLOCKED`, `FAILED`)
* `category` (optional, enum: `LIQUIDITY_FRICTION`, `TRANSIENT_INFRASTRUCTURE`, `INSTRUMENT_INVALIDATION`, `MANDATE_COMPLIANCE_LOCK`)

#### Response Body (200 OK)
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "case_id": "case_rec_01J8A9X4K2M3N4P5",
        "subscription_id": "sub_PZ100s1T2u3V4W",
        "customer_id": "cust_PZ088x9Y0z1A2B",
        "amount_inr": 2999.00,
        "status": "RECOVERED",
        "error_category": "LIQUIDITY_FRICTION",
        "retry_count": 1,
        "created_at": 1724180400,
        "updated_at": 1724439612
      }
    ],
    "pagination": {
      "total_items": 500,
      "total_pages": 25,
      "current_page": 1,
      "limit": 20
    }
  },
  "metadata": {
    "timestamp": 1724180400,
    "request_id": "req_01J8A9X4K2M3N4P8"
  }
}
```

---

### 4.2 `GET /api/v1/cases/{case_id}`
Returns full technical drill-down for a case, including the 7-phase payload evolution, OPA verification tokens, Langfuse trace links, and `immudb` cryptographic proofs.

* **Authentication:** Bearer JWT

#### Response Body (200 OK)
```json
{
  "success": true,
  "data": {
    "case_id": "case_rec_01J8A9X4K2M3N4P5",
    "subscription_id": "sub_PZ100s1T2u3V4W",
    "customer_id": "cust_PZ088x9Y0z1A2B",
    "status": "RECOVERED",
    "telemetry": {
      "original_payment_id": "pay_PZ182x9A7kL3mQ",
      "settled_payment_id": "pay_PZ999_RECOVERED",
      "langfuse_trace_id": "trc_langfuse_9988776655443322",
      "immudb_transaction_id": 4820194,
      "immudb_payload_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "risk_analysis": {
      "immediate_amount_inr": 2999.00,
      "remaining_ltv_inr": 20993.00,
      "total_revenue_at_risk_inr": 23992.00,
      "priority_score": 0.89
    },
    "diagnosis": {
      "error_category": "LIQUIDITY_FRICTION",
      "decline_code": "INSUFFICIENT_FUNDS",
      "payday_window_detected": true
    },
    "ai_decision": {
      "action_type": "SCHEDULED_RETRY_WITH_DUNNING",
      "channel": "WHATSAPP",
      "scheduled_time": 1724439600,
      "reasoning": "Subscriber failed due to NSF. Historical salary credit pattern indicates replenishment on 23rd."
    },
    "governance": {
      "opa_status": "APPROVED",
      "applied_rules": ["rule_rbi_predebit_notice_24h_pass", "rule_cooldown_window_48h_pass"],
      "verification_token": "tok_opa_APPROVED_987654321"
    },
    "execution_audit_trail": [
      { "step": "INGESTION", "timestamp": 1724180400, "status": "COMPLETED" },
      { "step": "RISK_EVALUATION", "timestamp": 1724180401, "status": "COMPLETED" },
      { "step": "DIAGNOSIS", "timestamp": 1724180402, "status": "COMPLETED" },
      { "step": "AI_REASONING", "timestamp": 1724180404, "status": "COMPLETED" },
      { "step": "OPA_GOVERNANCE", "timestamp": 1724180405, "status": "APPROVED" },
      { "step": "ACTION_DISPATCH", "timestamp": 1724439610, "status": "COMPLETED" },
      { "step": "IMMUDB_LEDGER_COMMIT", "timestamp": 1724439612, "status": "COMMITTED" }
    ]
  },
  "metadata": {
    "timestamp": 1724180400,
    "request_id": "req_01J8A9X4K2M3N4P9"
  }
}
```

---

## 5. Simulator API (The Batch Evaluator)

### 5.1 `POST /api/v1/simulator/batch`
Triggers an asynchronous synthetic benchmark simulation run across $N$ failed subscription cases to test AI Recovery Agent performance against baseline cron logic.

* **Authentication:** Bearer JWT

#### Request Body
```json
{
  "count": 500,
  "failure_distribution": {
    "liquidity_friction_pct": 45,
    "transient_infrastructure_pct": 25,
    "instrument_invalidation_pct": 15,
    "mandate_compliance_lock_pct": 15
  },
  "compare_against_baseline": true
}
```

#### Response Body (202 Accepted)
```json
{
  "success": true,
  "data": {
    "job_id": "sim_job_01J8B000000000000000000000",
    "status": "PROCESSING",
    "total_cases": 500,
    "estimated_completion_seconds": 15
  },
  "metadata": {
    "timestamp": 1724180400,
    "request_id": "req_01J8A9X4K2M3N5P0"
  }
}
```

---

### 5.2 `GET /api/v1/simulator/batch/{job_id}`
Polls the execution status and retrieves comparative benchmark results for a simulation run.

* **Authentication:** Bearer JWT

#### Response Body (200 OK - Job Complete)
```json
{
  "success": true,
  "data": {
    "job_id": "sim_job_01J8B000000000000000000000",
    "status": "COMPLETED",
    "total_cases": 500,
    "ai_agent_results": {
      "total_revenue_at_risk_inr": 5000000.00,
      "total_recovered_revenue_inr": 3250000.00,
      "recovery_rate_pct": 65.00,
      "compliance_violations": 0,
      "total_api_cost_inr": 4250.00,
      "net_recovered_revenue_inr": 3245750.00
    },
    "baseline_cron_results": {
      "total_revenue_at_risk_inr": 5000000.00,
      "total_recovered_revenue_inr": 910000.00,
      "recovery_rate_pct": 18.20,
      "compliance_violations": 14,
      "total_api_cost_inr": 1500.00,
      "net_recovered_revenue_inr": 908500.00
    },
    "comparative_summary": {
      "net_revenue_lift_inr": 2337250.00,
      "percentage_lift": 257.26,
      "compliance_delta": -14
    }
  },
  "metadata": {
    "timestamp": 1724180415,
    "request_id": "req_01J8A9X4K2M3N5P1"
  }
}
```

---

## 6. Standard Error Codes Reference

| Error Code | HTTP Status | Description |
| :--- | :--- | :--- |
| `HMAC_VERIFICATION_FAILED` | `401 Unauthorized` | Webhook signature header `X-Razorpay-Signature` validation failed. |
| `UNAUTHORIZED` | `401 Unauthorized` | Missing or invalid Bearer JWT authorization token. |
| `CASE_NOT_FOUND` | `404 Not Found` | The requested `case_id` does not exist in PostgreSQL or `immudb`. |
| `INVALID_SIMULATOR_PARAMS` | `400 Bad Request` | Batch count must be between 1 and 10,000. |
| `GOVERNANCE_EXECUTION_BLOCKED`| `422 Unprocessable` | OPA policy engine blocked the requested recovery action. |
| `INTERNAL_SERVER_ERROR` | `500 Server Error` | Unexpected backend or database exception. |

---

## 7. Document Metadata & Sign-off

* **Author:** Fintech System Architect / Track 3 Engineering Team  
* **Target Buildathon:** Razorpay AI Buildathon — Track 3 (AI Revenue Recovery)  
* **Upstream Specification:** `docs/01-problem-statement.md`, `docs/03-system-architecture.md`, `docs/04-data-flow.md`  
* **Implementation Artifacts:** `docs/05-api-contract.md`  
