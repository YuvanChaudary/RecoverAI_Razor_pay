# Real-Time Revenue-Risk Detection Engine Specification
**Project:** RecoverAI — Autonomous Revenue Recovery Agent  
**Target Buildathon:** Razorpay AI Buildathon (Track 3: AI Revenue Recovery)  
**Document ID:** `docs/19-real-time-revenue-risk-detection.md`  
**Status:** Approved Architectural Baseline  

---

## Executive Summary

This document specifies how **RecoverAI** ingests real-time business and payment telemetry, detects financial exposure, classifies distinct revenue-loss situations, initializes structured recovery cases, and routes them into the **Diagnose $\rightarrow$ Decide $\rightarrow$ Govern $\rightarrow$ Act $\rightarrow$ Audit** workflow pipeline. RecoverAI is not a passive AI chatbot that waits for user prompts; it is an event-driven, real-time revenue recovery system engineered for enterprise payment infrastructure.

---

## 1. Real-Time Detection Principle

RecoverAI does not continuously poll end-users or ask conversational questions. Instead, it operates as an event listener that converts business telemetry into actionable financial signals.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   REAL-TIME DETECTION PIPELINE                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [ External Business / Gateway Event ] (Razorpay Webhook / Telemetry)   │
│                   │                                                      │
│                   ▼                                                      │
│  [ Webhook Ingestion & Signature Verification ] (SHA256 HMAC Check)      │
│                   │                                                      │
│                   ▼                                                      │
│  [ Event Normalization ] (Transform into canonical RevenueRiskEvent)     │
│                   │                                                      │
│                   ▼                                                      │
│  [ Revenue Risk Detection & Classification ] (Calculate Exposure ₹)       │
│                   │                                                      │
│                   ▼                                                      │
│  [ Recovery Case Initialization ] (Create DB Case Record)                │
│                   │                                                      │
│                   ▼                                                      │
│  [ Root-Cause Diagnosis ] (Error Code Taxonomy Mapping)                  │
│                   │                                                      │
│                   ▼                                                      │
│  [ AI Decision Agent ] (Propose Contextual Intervention)                 │
│                   │                                                      │
│                   ▼                                                      │
│  [ OPA Governance Firewall ] (Deterministic Hard Brakes)                 │
│                   │                                                      │
│                   ▼                                                      │
│  [ Temporal Workflow ] (Durable Saga & Sleep Timers)                     │
│                   │                                                      │
│                   ▼                                                      │
│  [ Action Execution ] (Razorpay API / Novu Notification)                 │
│                   │                                                      │
│                   ▼                                                      │
│  [ Terminal Outcome ] (RECOVERED / STILL_FAILED)                         │
│                   │                                                      │
│                   ▼                                                      │
│  [ Cryptographic Audit ] (Commit SHA-256 Receipt to immudb)              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. What Is the System Input?

RecoverAI distinguishes between five distinct categories of input:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       INPUT CATEGORY TAXONOMY                            │
├─────────────────────────┬────────────────────────────────────────────────┤
│ Input Category          │ Description & Payload Source                   │
├─────────────────────────┼────────────────────────────────────────────────┤
│ A. Payment Provider     │ Structured Webhook POST (`payment.failed`,     │
│    Telemetry            │ `subscription.charged.failed`)                 │
│ B. Merchant/System      │ Internal invoice events (`invoice.overdue`,    │
│    Telemetry            │ `checkout.abandoned`)                          │
│ C. Customer Interaction │ Re-authorization link click, payment link pay  │
│ D. Historical Context   │ Subscription billing history, prior retries    │
│ E. AI Candidate Output  │ Structured `ProposedRecoveryPlan` (Pydantic)   │
└─────────────────────────┴────────────────────────────────────────────────┘
```

The primary input is **never** a free-form natural language user prompt. It is a structured JSON event payload emitted by payment gateways or business engines.

### Example Inbound Gateway Event Payload (`payment.failed`)
```json
{
  "event_id": "evt_rzp_test_998877",
  "event_type": "payment.failed",
  "payment_id": "pay_test_9876543210",
  "subscription_id": "sub_test_1234567890",
  "amount": 249900,
  "currency": "INR",
  "timestamp": "2026-08-20T14:32:11+05:30",
  "error": {
    "code": "BAD_REQUEST_ERROR",
    "reason": "insufficient_funds",
    "source": "customer",
    "step": "payment_authorization"
  }
}
```

*Note: Provider-dependent fields (such as `error.source` or `error.step`) are mapped into a standardized internal schema upon ingestion.*

---

## 3. Supported Revenue Risk Signals

RecoverAI supports 8 distinct revenue risk signals across payment and billing workflows:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     SUPPORTED REVENUE RISK SIGNALS                       │
├───────────────────────────────┬──────────────────────────────────────────┤
│ Risk Signal                   │ Primary Trigger Condition                │
├───────────────────────────────┼──────────────────────────────────────────┤
│ 1. Payment Failure            │ Single transaction decline on debit card │
│ 2. Subscription Charge Fail   │ Failed recurring auto-debit charge       │
│ 3. Mandate-Related Failure    │ Expired, revoked, or invalid e-mandate   │
│ 4. Repeated Payment Failure   │ $\ge 2$ consecutive decline attempts     │
│ 5. Checkout Abandonment       │ Payment started but no success in window │
│ 6. Payment Degradation        │ Spike in rolling failure rate ($>15\%$)  │
│ 7. Overdue Receivable         │ Invoice due date exceeded by $\ge 3$ days│
│ 8. Customer Action Required   │ Payment instrument expired or invalid    │
└───────────────────────────────┴──────────────────────────────────────────┘
```

---

## 4. Payment Failure Detection

```
Razorpay Webhook POST ──► HMAC Verification ──► Deduplication ──► Normalization ──► RaR Evaluation ──► Create Case
```

1. **Ingestion & Signature Check:** FastAPI intercepts `POST /webhooks/razorpay` and verifies `X-Razorpay-Signature` via constant-time SHA256 HMAC comparison.
2. **Deduplication Check:** Checks `event_id` in PostgreSQL. If the event exists, drops the duplicate immediately (`HTTP 200 OK`).
3. **Event Normalization:** Transforms raw JSON into standard `RevenueRiskEvent`.
4. **Risk Evaluation:** Calculates immediate uncaptured financial exposure ($\text{RaR} = \text{Amount} / 100$).
5. **Case Creation:** Spawns `PaymentRecoveryCase` and triggers `RecoverySagaWorkflow` in Temporal.

---

## 5. Subscription Failure Detection

Subscription charge failures differ fundamentally from one-time payment declines. They represent ongoing **Customer Lifetime Value (LTV)** at risk.

RecoverAI tracks:
* `subscription_id` & `payment_id`
* Historical failure count & previous successful charge count
* Days elapsed since last successful billing cycle
* Subscription status (`active`, `authenticated`, `halted`)

Repeated failures increase risk urgency but simultaneously enforce stricter OPA governance limits (e.g., maximum 3 retries).

---

## 6. Mandate Failure Detection

Mandate failures represent structural compliance locks rather than temporary liquidity issues.

### Internal Mandate Failure Taxonomy
* `MANDATE_EXPIRED`: E-mandate validity period has lapsed.
* `MANDATE_REVOKED`: Customer cancelled mandate via issuing bank portal.
* `MANDATE_AUTH_REQUIRED`: Additional Factor Authentication (AFA) required.
* `MANDATE_FAILURE`: Generic e-mandate execution error.

*Operational Rule:* Mandate-related failures are never retried with blind card charges. RecoverAI routes them to customer re-authorization flows.

---

## 7. Checkout Abandonment Detection

```
[ checkout.started ] ──► [ payment.attempted ] ──► [ No Success in 15 Min ] ──► Checkout Abandonment Risk
```

A checkout attempt is classified as an abandonment risk when:
1. `checkout.started` event is logged.
2. Payment attempt fails or remains uncaptured.
3. Configurable inactivity window (e.g., 15 minutes) elapses without a successful `payment.captured` event.

RecoverAI initializes a `CheckoutRecoveryCase` to dispatch a frictionless payment link rather than attempting automated account debits.

---

## 8. Overdue Receivable Detection

For invoice-based B2B transactions, overdue receivables represent unpaid accrued revenue:

```
[ invoice.created ] ──► [ due_date_passed ] ──► Overdue Receivable Risk
```

### Risk Stratification Tiers
* **Low Overdue ($1 - 7$ Days):** Automated polite email/SMS reminder.
* **Medium Overdue ($8 - 30$ Days):** Personalized AI WhatsApp follow-up with discount link.
* **High Overdue ($>30$ Days):** Hard escalation to human collections team.

---

## 9. Payment Degradation Detection

Systemic payment degradation indicates gateway infrastructure failures or bank switch outages.

RecoverAI tracks rolling-window failure rates:
$$\text{Failure Rate} = \frac{N_{\text{failed\_payments}}}{N_{\text{total\_attempts}}} \quad [\text{Windows: 5m, 1h, 24h}]$$

If failure rate exceeds $15\%$ in a 5-minute window, RecoverAI flags a `TRANSIENT_INFRASTRUCTURE` degradation event and temporarily pauses immediate retries to prevent retry storms.

---

## 10. Revenue-at-Risk Calculation Engine

$$\text{Revenue at Risk (RaR)} = \sum_{i=1}^{N} \text{Unresolved Transaction Amount}_i$$

* **Deduplication:** Multiple webhooks for the same invoice/subscription update the existing case rather than inflating $\text{RaR}$.
* **Hackathon Evaluation Baseline:** $\text{RaR}$ is strictly equal to the immediate uncaptured transaction amount in INR ($\text{₹}$).

---

## 11. Event Normalization Schema (`RevenueRiskEvent`)

All external telemetry is converted into a canonical internal Pydantic schema:

```python
class RevenueRiskEvent(BaseModel):
    event_id: str
    event_type: str
    source: str  # "razorpay", "merchant_billing", "checkout_engine"
    transaction_id: str
    subscription_id: Optional[str] = None
    customer_id: str
    amount: int  # Amount in paise (e.g., 249900 = ₹2499.00)
    currency: str = "INR"
    timestamp: datetime
    risk_type: str  # "SUBSCRIPTION_FAIL", "MANDATE_LOCK", "CHECKOUT_ABANDON"
    failure_code: Optional[str] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = {}
```

---

## 12. Real-Time Detection Pipeline

```
              SYNCHRONOUS BOUNDARY (<100ms ACK)
┌──────────────────────────────────────────────────────────┐
│ Razorpay Webhook ──► FastAPI ──► HMAC Verification ──►  │
│ PostgreSQL Event Persistence ──► Return HTTP 200 OK      │
└────────────────────────────┬─────────────────────────────┘
                             │ (Asynchronous Bus Handoff)
              ASYNCHRONOUS BOUNDARY (Temporal Workers)
┌────────────────────────────▼─────────────────────────────┐
│ Case Creation ──► Failure Diagnosis ──► AI Agent ──►     │
│ OPA Governance ──► Action Dispatch ──► immudb Audit      │
└──────────────────────────────────────────────────────────┘
```

The Webhook Listener acknowledges HTTP requests in $<100\text{ms}$. Long-running AI inference, OPA evaluation, and Temporal workflow execution occur asynchronously.

---

## 13. Event-to-Case Mapping Matrix

| Inbound Event Type | Revenue Risk Signal | Created Case Type | Initial Pipeline Action |
| :--- | :--- | :--- | :--- |
| `payment.failed` | Single transaction exposure | `PaymentRecoveryCase` | Trigger Diagnosis |
| `subscription.charged.failed` | Recurring LTV at risk | `SubscriptionRecoveryCase` | Check Payday Alignment |
| `subscription.halted` | Severe recurring risk | `HaltedSubscriptionCase` | Escalation Check |
| `checkout.abandoned` | Conversion loss | `CheckoutRecoveryCase` | Dispatch Payment Link |
| `invoice.overdue` | Receivable delay | `ReceivableRecoveryCase` | Tiered Dunning |

---

## 14. Idempotency & Replay Attack Protection

```
Inbound Webhook ──► Check PostgreSQL `event_id` Key ──► Exists? ──► YES ──► Drop Payload (HTTP 200 OK)
                                                        └──► NO  ──► Process Event
```

Deduplication occurs at 3 layers:
1. **Perimeter Database Uniqueness:** `PRIMARY KEY (event_id)` in PostgreSQL.
2. **Temporal Workflow Uniqueness:** `WorkflowID = "wf_rec_" + subscription_id + "_" + invoice_id`.
3. **Outbound API Idempotency:** Header `X-Razorpay-Idempotency-Key: rec_idemp_<event_id>_<attempt>`.

---

## 15. Real-Time Risk State Machine

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   REAL-TIME RISK STATE MACHINE                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [ DETECTED ] ──► [ VALIDATED ] ──► [ AT_RISK ] ──► [ DIAGNOSING ]      │
│                                                            │             │
│                                                            ▼             │
│  [ ACTION_EXECUTED ] ◄── [ ACTION_SCHEDULED ] ◄── [ GOVERNANCE_CHECK ]   │
│          │                                                               │
│          ▼                                                               │
│  [ RECOVERY_PENDING ] ──► (Outcome Evaluation)                           │
│          ├──► [ RECOVERED ] (Payment Captured)                           │
│          ├──► [ STILL_FAILED ] (Retry Exhausted)                         │
│          ├──► [ ESCALATED ] (Human Intervention Required)               │
│          └──► [ STOPPED_BY_POLICY ] (OPA Hard Brake Veto)                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Revenue Risk Scoring Model

The risk engine computes a deterministic priority score ($0.0 - 100.0$) to order cases in the recovery queue:

$$\text{Risk Score} = (w_1 \cdot \text{Amount}) + (w_2 \cdot \text{Failure Freq}) + (w_3 \cdot \text{Decline Severity}) + (w_4 \cdot \text{LTV History})$$

*Rule:* The LLM does **not** calculate financial risk scores. Risk scoring is strictly deterministic.

---

## 17. AI Agent Role Boundary

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      AI AGENT RESPONSIBILITY BOUNDARY                     │
├──────────────────────────────────────┬───────────────────────────────────┤
│ DETERMINISTIC LAYER (FastAPI / OPA)  │ AI AGENT LAYER (LLM / Instructor) │
├──────────────────────────────────────┼───────────────────────────────────┤
│ • Event detection & HMAC validation  │ • Contextual failure reasoning    │
│ • Deterministic risk scoring         │ • Payday / timing selection       │
│ • Hard OPA compliance enforcement    │ • Hinglish dunning text generation│
│ • Financial ledgering in immudb      │ • Candidate plan proposal (JSON)  │
└──────────────────────────────────────┴───────────────────────────────────┘
```

---

## 18. Real-Time Operational Scenario Matrix

| Scenario | Inbound Signal | Diagnosis Category | Candidate Action | OPA Rule Checked | Target Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Insufficient Funds | `subscription.charged.failed` | `LIQUIDITY_FRICTION` | Delay 72h + WhatsApp | `RULE-002: COOLDOWN` | `RECOVERED` |
| Expired Card | `payment.failed` | `INSTRUMENT_INVALIDATION` | Re-auth Link | `RULE-003: TERMINAL` | `RECOVERED` |
| Gateway Timeout | `payment.failed` | `TRANSIENT_INFRASTRUCTURE` | Exp Backoff 15m | `RULE-001: MAX_RETRIES`| `RECOVERED` |
| Mandate Lock | `subscription.halted` | `MANDATE_COMPLIANCE_LOCK` | Mandate Migration | `RULE-005: PRE_DEBIT` | `ESCALATED` |

---

## 19. Complete Real-Time Case Walkthrough (#case_rec_99)

1. **00:00.000:** Razorpay emits `subscription.charged.failed` ($\text{₹}2,499.00$, NSF).
2. **00:00.045:** FastAPI verifies HMAC signature and checks `event_id` uniqueness. Returns `HTTP 200 OK`.
3. **00:00.120:** Event normalized into `RevenueRiskEvent`. $\text{RaR}$ calculated as $\text{₹}2,499.00$. Case initialized in PostgreSQL (`case_rec_99`).
4. **00:00.350:** Temporal spawns `RecoverySagaWorkflow`. Diagnosis engine classifies failure as `LIQUIDITY_FRICTION`.
5. **00:01.200:** AI Agent generates candidate plan: delay retry 72h to alignment date (23rd) + send WhatsApp dunning.
6. **00:01.350:** OPA evaluates plan against Rego rules $\rightarrow$ `approved: true`, token signed.
7. **00:01.400:** Temporal enters durable sleep for 72 hours.
8. **72:00.000:** Workflow wakes up, executes `DispatchRazorpayActionActivity` with idempotency key.
9. **72:00.850:** Razorpay returns `payment.captured`. Outcome set to `RECOVERED`. Receipt committed to `immudb`.

---

## 20. System Fault Tolerance & Fallback Policies

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         FAULT TOLERANCE MATRIX                           │
├───────────────────────────┬──────────────────────────────────────────────┤
│ System Failure Scenario   │ System Resilience & Fallback Action          │
├───────────────────────────┼──────────────────────────────────────────────┤
│ Invalid HMAC Signature    │ HTTP 401 Unauthorized (Drop Payload)         │
│ Duplicate Event Webhook   │ HTTP 200 OK (Ignore Payload)                 │
│ Database Down             │ Redpanda Queue Retry Buffer                  │
│ LLM Timeout / Error       │ Deterministic Rule Engine Fallback Plan      │
│ OPA Sidecar Unavailable   │ Fail-closed: Block Action & Escalate         │
│ Razorpay API 5xx Error    │ Temporal Exponential Backoff Retry           │
└───────────────────────────┴──────────────────────────────────────────────┘
```

---

## 21. Real-Time Performance Benchmarks

* **Webhook Ingestion SLA:** $\le 100\text{ms}$ (P99)
* **Risk Detection & Normalization:** $\le 50\text{ms}$
* **AI Decision Latency (Async):** $\le 2500\text{ms}$
* **OPA Governance Evaluation:** $\le 15\text{ms}$
* **`immudb` Audit Commit:** $\le 30\text{ms}$

---

## 22. Zero-Trust Security Boundary

```
External Webhook ──► HMAC Verification ──► Schema Check ──► OPA Governance ──► Authorized Execution ──► immudb Ledger
```

No external payload can trigger payment executions without passing HMAC verification, Pydantic schema validation, and deterministic OPA policy checks.

---

## 23. Real-Time Telemetry & Observability Metrics

Prometheus & Langfuse track real-time operational health:
* `events_received_total` & `events_validated_total`
* `revenue_at_risk_inr_total`
* `recovery_cases_active`
* `opa_policy_evaluations_total` (`approved` vs `vetoed`)
* `llm_inference_latency_seconds` & `llm_token_cost_usd`

---

## 24. React Dashboard Live Operational View

The React UI provides real-time visibility for Finance Controllers:
* **Live Telemetry Stream:** Scrolling log of inbound webhooks.
* **Hero Risk Widgets:** Live Total Revenue at Risk ($\text{₹}$) and Total Recovered ($\text{₹}$).
* **Active Pipeline Funnel:** Cases progressing through Diagnosis $\rightarrow$ AI $\rightarrow$ OPA $\rightarrow$ Temporal.
* **Governance Audit Drawer:** Live view of OPA blocks and `immudb` SHA-256 Merkle tree verification.

---

## 25. Architectural Scope & Future Expansion

RecoverAI's primary implementation targets **Failed Recurring Subscription Payments**. The event-driven architecture is natively extensible to Checkout Abandonment, Overdue Receivables, and Mandate Recovery without breaking backend data contracts.

---

## 26. Final Architecture Principle

> **"RecoverAI does not wait for a user to tell it that revenue is being lost. Revenue-risk signals enter through events, are deterministically validated and classified, enriched with context, reasoned about by AI, bounded by policy, executed through durable workflows, and measured through financial outcomes."**

---

## 27. Document Metadata & Sign-off

* **Author:** Fintech System Architect & Lead Ingestion Engineer / Track 3 Team  
* **Target Buildathon:** Razorpay AI Buildathon — Track 3 (AI Revenue Recovery)  
* **Upstream Specification:** `docs/01-problem-statement.md` through `docs/18-execution-model.md`, `README.md`  
* **Implementation Artifacts:** `docs/19-real-time-revenue-risk-detection.md`, `backend/app/api/webhooks.py`  
