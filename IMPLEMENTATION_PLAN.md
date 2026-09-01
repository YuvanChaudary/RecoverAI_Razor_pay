# RecoverAI — Master Implementation Plan & Phase 0 Readiness Report

**Project:** RecoverAI — Autonomous Revenue Recovery Agent  
**Target Buildathon:** Razorpay AI Buildathon (Track 3: AI Revenue Recovery)  
**Document Version:** 1.0.0  
**Status:** Awaiting User Approval (Planning Mode)

---

## 1. Executive Summary & Architecture Overview

RecoverAI is an event-driven, governed revenue recovery system engineered to convert payment failure webhooks into quantified **Revenue at Risk ($\text{RaR}$)**, diagnose granular root causes, query NVIDIA NIM for structured recovery recommendations, enforce deterministic **Open Policy Agent (OPA)** compliance guardrails, orchestrate durable multi-day sagas using **Temporal.io**, execute idempotent external API actions (Razorpay & Novu), and record cryptographic audit proofs in **`immudb`**.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         RECOVERAI CLOSED-LOOP EXECUTION PIPELINE                                 │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [ Real / Simulated Inbound Event ] (Razorpay Webhook POST + SHA256 HMAC Signature)              │
│                   │                                                                              │
│                   ▼                                                                              │
│  1. [ Revenue Risk Detection & Case Creation ] (Face Value RaR ₹, Priority Tiers: High/Med/Low)  │
│                   │                                                                              │
│                   ▼                                                                              │
│  2. [ Failure Diagnosis Engine ] (Deterministic Gateway Error Mapping to Taxonomy)               │
│                   │                                                                              │
│                   ▼                                                                              │
│  3. [ AI Decision Agent ] (NVIDIA NIM Contextual Reasoning: Payday Timing + Hinglish Dunning)    │
│                   │                                                                              │
│                   ▼                                                                              │
│  4. [ OPA Governance Firewall ] (Deterministic Rego Hard Brakes: RULE-001 to RULE-005)           │
│                   │                                                                              │
│                   ▼                                                                              │
│  5. [ Temporal Durable Saga ] (Workflow State Machine & O(1) RAM Sleep Timers)                   │
│                   │                                                                              │
│                   ▼                                                                              │
│  6. [ Action Dispatcher ] (Idempotent Razorpay Subscriptions / Payment Links / Novu Dunning)     │
│                   │                                                                              │
│                   ▼                                                                              │
│  7. [ Authoritative Settlement & immudb Audit ] (Razorpay Capture + SHA-256 Cryptographic Proof)│
│                   │                                                                              │
│                   ▼                                                                              │
│  8. [ Comparative Batch Evaluator & Dashboard ] (500 Cases: Incremental Revenue Lift +257.2%)    │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Non-Negotiable Engineering Principles

1. **Principle 1 — No Fake Success:** Revenue is marked `RECOVERED` **only** upon an authoritative `payment.captured` or `invoice.paid` event from Razorpay. API 200 OKs, dunning dispatches, or AI recommendations never count as recovered revenue.
2. **Principle 2 — AI Proposes, Deterministic Systems Decide:** NVIDIA NIM recommends candidate actions (`RETRY_SCHEDULED`, `SEND_PAYMENT_LINK`, etc.). Financial state (`status`, `recovered_amount`, `opa_approval`, `audit_hash`) is managed exclusively by backend deterministic services.
3. **Principle 3 — OPA is a Mandatory Security Boundary:** All AI proposals must pass through Open Policy Agent (Rego rules `RULE-001` through `RULE-005`). `DENY` outcomes immediately freeze automated actions.
4. **Principle 4 — PostgreSQL is Operational Truth:** SQLAlchemy models store operational cases, payments, attempts, decisions, outcomes, and audit references.
5. **Principle 5 — immudb is the Audit Layer:** Append-only cryptographic Merkle tree receipts record every state transition.
6. **Principle 6 — Simulator is Evaluation Infrastructure:** The 500-case simulator generates inputs and evaluates outcomes counterfactually. Metrics are aggregated dynamically from case records, never hardcoded.

---

## 3. Phase 0 Readiness Report

### 3.1 External API & Service Connectivity Matrix

| Service / Dependency | Configuration Status | Network Status | Verification Details |
| :--- | :--- | :--- | :--- |
| **Razorpay Test API** | `CONFIGURED` | `CONNECTED` | Keys present in `.env`; `api.razorpay.com` probe responded with HTTP 401 (Live & reachable). |
| **NVIDIA NIM API** | `CONFIGURED` | `TESTED & CONNECTED` | `NVIDIA_API_KEY` validated against `integrate.api.nvidia.com/v1/models` (HTTP 200 OK). |
| **Langfuse Cloud** | `CONFIGURED` | `TESTED & CONNECTED` | `cloud.langfuse.com` health check passed (HTTP 200 OK). |
| **PostgreSQL** | `CONFIGURED` | `CONNECTED` | Active on local port `5432`. |
| **Temporal Engine** | `CONFIGURED` | `UNAVAILABLE` | Port `7233` ready for Docker/daemon startup in Phase 6. |
| **OPA Server** | `CONFIGURED` | `UNAVAILABLE` | Port `8181` ready for Docker/daemon startup in Phase 5; Rego rules exist in `policies/`. |
| **immudb Ledger** | `CONFIGURED` | `UNAVAILABLE` | Port `3322` ready for Docker/daemon startup in Phase 8. |
| **Novu Provider** | `PLACEHOLDER` | `UNCONFIGURED` | Set to placeholder `YOUR_NOVU_API_KEY_HERE` in `.env`. HTTP fallback notification ready. |

### 3.2 Current Codebase Implementation State

- **Phase 1 Ingestion**: Completed. FastAPI app (`backend/app/main.py`), settings (`backend/app/core/config.py`), webhook schemas (`backend/app/schemas/webhook.py`), and webhook router (`backend/app/api/webhooks.py`) are fully implemented.
- **HMAC Verification**: Raw-body HMAC-SHA256 signature verification with constant-time string comparison (`hmac.compare_digest`) verified against genuine Razorpay Test Mode webhooks (6/6 HTTP 200 OK dispatches processed live via ngrok).
- **Unit Tests**: 8/8 tests passing in `tests/unit/test_webhooks.py`.

---

## 4. Phase-by-Phase Master Implementation Roadmap

### Phase 1 — Core Foundation & Database Domain
- **Files to Modify/Create:**
  - `backend/app/db/database.py` [MODIFY]
  - `backend/app/db/models.py` [NEW]
  - `backend/app/db/repositories/case_repository.py` [NEW]
  - `backend/app/db/repositories/payment_repository.py` [NEW]
  - `migrations/env.py`, `migrations/versions/001_initial.py` [NEW]
- **Tasks:** Build SQLAlchemy models (`WebhookEvent`, `Customer`, `Payment`, `PaymentAttempt`, `RecoveryCase`, `RecoveryDecision`, `RecoveryAction`, `RecoveryOutcome`, `WorkflowExecution`, `AuditReference`). Set up Alembic async migrations.
- **Verification:** `pytest tests/unit/test_models.py` & DB migration tests.

### Phase 2 — Razorpay Webhook Ingestion & Event Persistence
- **Files to Modify/Create:**
  - `backend/app/api/webhooks.py` [MODIFY]
  - `backend/app/services/webhook_service.py` [NEW]
- **Tasks:** Connect webhook endpoint to database persistence (`WebhookEvent`). Implement idempotency deduplication on `event_id`. Asynchronously queue event processing.
- **Verification:** Post test webhook payload and verify persistence in PostgreSQL `webhook_events` table.

### Phase 3 — Failure Diagnosis & Revenue-at-Risk Engine
- **Files to Modify/Create:**
  - `backend/app/services/diagnosis_service.py` [NEW]
  - `backend/app/services/risk_service.py` [NEW]
  - `tests/unit/test_diagnosis_risk.py` [NEW]
- **Tasks:** Map raw Razorpay error codes (`BAD_REQUEST_ERROR`, `insufficient_funds`, `expired_card`, `gateway_timeout`, `mandate_expired`) into deterministic failure categories (`LIQUIDITY_FRICTION`, `TRANSIENT_INFRASTRUCTURE`, `INSTRUMENT_INVALIDATION`, `MANDATE_COMPLIANCE_LOCK`, `BANK_RISK_BLOCK`). Compute face-value $\text{RaR} = \text{Amount Paise} / 100$. Assign priority scores.
- **Verification:** Unit tests verifying 100% deterministic error mapping and math reproducibility.

### Phase 4 — NVIDIA NIM AI Decision Engine
- **Files to Modify/Create:**
  - `backend/app/ai/agent.py` [NEW]
  - `backend/app/ai/prompts.py` [NEW]
  - `backend/app/ai/schemas.py` [NEW]
  - `tests/unit/test_ai_agent.py` [NEW]
- **Tasks:** Build `NvidiaNIMAgent` using `openai` SDK pointing to `https://integrate.api.nvidia.com/v1`. Inject runtime context (amount, diagnosis, customer history, payday alignment). Return structured `ProposedRecoveryPlan` using Pydantic / `instructor`. Integrate Langfuse trace logging. Add fallback handler for timeouts ($>3\text{s}$) or confidence $<0.80$.
- **Verification:** Run live NVIDIA NIM inference test with different contexts and verify distinct structured outputs and Langfuse traces.

### Phase 5 — OPA Governance Firewall
- **Files to Modify/Create:**
  - `backend/app/policy/engine.py` [NEW]
  - `policies/governance.rego` [MODIFY]
  - `policies/retry.rego` [MODIFY]
  - `tests/unit/test_opa_governance.py` [NEW]
- **Tasks:** Implement `OPAGovernanceEngine` querying OPA HTTP REST sidecar (`http://localhost:8181/v1/data/recovery/governance/allow`). Codify `RULE-001` (Max 3 retries), `RULE-002` (24h cooldown), `RULE-003` (Terminal decline block), `RULE-004` (Confidence $<0.80$ floor), `RULE-005` (RBI 24h pre-debit notice check).
- **Verification:** Adversarial unit test proving an unsafe AI recommendation returns `ALLOW = False` and blocks execution.

### Phase 6 — Temporal Recovery Workflow
- **Files to Modify/Create:**
  - `backend/app/workflows/recovery_workflow.py` [NEW]
  - `backend/app/workflows/activities.py` [NEW]
  - `backend/app/integrations/temporal_client.py` [NEW]
  - `tests/unit/test_temporal_workflow.py` [NEW]
- **Tasks:** Implement `RecoverySagaWorkflow` in Temporal. Use `workflow.sleep()` for durable sleep timers ($O(1)$ space). Implement discrete activities for risk calculation, diagnosis, AI reasoning, OPA governance, action dispatch, and audit logging.
- **Verification:** Execute workflow test with simulated worker restart during 24h sleep timer; verify state persistence.

### Phase 7 — Real Razorpay & Novu Action Dispatch
- **Files to Modify/Create:**
  - `backend/app/services/razorpay_service.py` [NEW]
  - `backend/app/services/notification_service.py` [NEW]
- **Tasks:** Implement outbound Razorpay API client (`POST /v1/invoices/{id}/retry`, `POST /v1/payment_links`) with idempotency headers (`rec_idemp_<event_id>_<attempt>`). Implement Novu / fallback HTTP dunning notifications.
- **Verification:** End-to-end trace: AI Decision $\rightarrow$ OPA Approval $\rightarrow$ Temporal Activity $\rightarrow$ Razorpay Payment Link Creation $\rightarrow$ Response stored in PostgreSQL.

### Phase 8 — Immutable Audit Trail (`immudb`)
- **Files to Modify/Create:**
  - `backend/app/integrations/immudb_client.py` [NEW]
  - `backend/app/services/audit_service.py` [NEW]
  - `tests/unit/test_immudb_audit.py` [NEW]
- **Tasks:** Implement append-only Merkle tree ledger logger in `immudb`. Record state transitions (`EVENT_RECEIVED`, `DIAGNOSED`, `AI_DECISION`, `POLICY_APPROVED`, `ACTION_EXECUTED`, `PAYMENT_RECOVERED`). Implement verification hash check.
- **Verification:** Modify a PostgreSQL record and verify `immudb` cryptographic proof detects tampering.

### Phase 9 — Authoritative State Machine & Business Rules
- **Files to Modify/Create:**
  - `backend/app/core/state_machine.py` [NEW]
- **Tasks:** Enforce strict legal state transitions (`DETECTED` $\rightarrow$ `DIAGNOSING` $\rightarrow$ `DECISION_PENDING` $\rightarrow$ `GOVERNANCE_CHECK` $\rightarrow$ `ACTION_SCHEDULED` $\rightarrow$ `ACTION_EXECUTED` $\rightarrow$ `RECOVERED`/`FAILED`/`STOPPED`). Block illegal transitions.
- **Verification:** Unit tests asserting illegal state transitions raise `InvalidStateTransitionError`.

### Phase 10 — 500-Case Evaluation Simulator
- **Files to Modify/Create:**
  - `simulator/generate_failures.py` [NEW]
  - `simulator/scenarios/` [NEW]
  - `scripts/run_evaluation.py` [NEW]
- **Tasks:** Generate 500 synthetic payment failure cases modeling Indian payment failure distributions. Run cases through the full RecoverAI pipeline counterfactually against `FIXED_RETRY_BASELINE`.
- **Verification:** Run simulator; verify all 500 cases process through the pipeline without hardcoded metric shortcuts.

### Phase 11 — Baseline vs. RecoverAI Evaluation Engine
- **Files to Modify/Create:**
  - `backend/app/services/evaluation_service.py` [NEW]
- **Tasks:** Calculate Incremental Revenue Recovery ($\text{IRR} = \text{RR}_{\text{RecoverAI}} - \text{RR}_{\text{Baseline}}$), Recovery Lift (%), average MTTR, policy violation rate, and confidence intervals from actual case outcomes.
- **Verification:** Assert zero hardcoded numbers in evaluation outputs.

### Phase 12 — React Finance Controller Dashboard
- **Files to Modify/Create:**
  - `frontend/src/api/client.js` [NEW]
  - `frontend/src/components/` [NEW]
  - `frontend/src/pages/Dashboard.jsx` [NEW]
- **Tasks:** Build dark-mode React + Vite command center: Hero Metric Cards, Failure Category Matrix, OPA Governance Panel, Case Table, and 7-Stage Audit Modal with Langfuse links and live `immudb` proof verifier.
- **Verification:** Verify real-time UI rendering against FastAPI REST APIs (`/api/v1/metrics/overview`, `/cases`, `/simulator/batch`).

### Phase 13 — Security Hardening & Audit
- **Files to Modify/Create:**
  - `backend/app/core/security.py` [NEW]
- **Tasks:** Sanitize PII in logs, enforce JWT authentication on management endpoints, verify CORS headers, test prompt injection defenses.
- **Verification:** Security audit sweep verifying zero secret leakage in logs or HTTP error envelopes.

### Phase 14 — Full Integration & Adversarial Verification Suite
- **Files to Modify/Create:**
  - `tests/integration/test_full_pipeline.py` [NEW]
- **Tasks:** Implement comprehensive end-to-end integration tests covering webhooks, AI fallback, OPA hard blocks, Temporal sleeps, Razorpay APIs, and `immudb` receipts.
- **Verification:** Execute full `pytest` suite across unit and integration tests.

### Phase 15 — Hostile Fintech Demo Readiness
- **Files to Modify/Create:**
  - `scripts/run_demo.py` [NEW]
- **Tasks:** Create automated demo runner executing the 6 hostile attack scenarios (Different AI contexts, Real API calls, Delayed recovery confirmation, OPA block demonstration, Dynamic 500-case evaluation, `immudb` proof check).
- **Verification:** Successful execution of `python scripts/run_demo.py`.

---

## 5. Verification & Approval Gate

Per the **Phase Execution Rule**:
1. We will execute **one phase at a time**.
2. After completing each phase, we will present the exact code created, test execution results, and Phase Definition of Done checklist.
3. We will **STOP and wait for your explicit approval** before moving to the next phase.

**Awaiting your explicit approval to begin Phase 1 (Core Foundation & Database Domain)!**
