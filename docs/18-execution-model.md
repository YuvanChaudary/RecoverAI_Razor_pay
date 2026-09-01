# End-to-End Operational Execution & Decision Model Specification
**Project:** RecoverAI — Autonomous Revenue Recovery Agent  
**Target Buildathon:** Razorpay AI Buildathon (Track 3: AI Revenue Recovery)  
**Document ID:** `docs/18-execution-model.md`  
**Status:** Approved Architectural Baseline  

---

## Executive Summary

This document specifies the master operational execution and decision model for **RecoverAI**. It codifies the complete lifecycle of a payment failure from initial event ingestion through root-cause diagnosis, AI proposal generation, deterministic OPA governance, Temporal saga orchestration, action execution, cryptographic auditing, and comparative batch evaluation. This specification acts as the binding glue across all upstream engineering documents (`docs/01-problem-statement.md` through `docs/17-demo-script.md`) and the repository `README.md`.

---

## 1. End-to-End Operational Decision Architecture

The diagram below illustrates the exact closed-loop execution model governing RecoverAI:

```
                    MONEY AT RISK
                         │
                         ▼
              ┌─────────────────────┐
              │ REAL-TIME EVENTS    │
              │ Razorpay / Business │
              │ Systems             │
              └──────────┬──────────┘
                         ▼
                 Detect Revenue Risk
                         │
                         ▼
                  Create Case
                         │
                         ▼
                    Diagnose
                         │
                         ▼
                 AI Decision Agent
                         │
                         ▼
                  ┌──────────────┐
                  │     OPA      │
                  │ HARD BRAKES  │
                  └──────┬───────┘
                         ▼
                     Temporal
                         │
                         ▼
                      ACTION
                         │
                         ▼
                    OUTCOME
                   /        \
             RECOVERED     FAILED
                   \        /
                    ▼      ▼
                  AUDIT + METRICS
                         │
                         ▼
                 BATCH EVALUATION
                         │
                         ▼
          ┌──────────────────────────┐
          │ "Did we recover MORE     │
          │ money than the baseline?"│
          └──────────────────────────┘
```

---

## 2. Stage-by-Stage Operational Specification

### Stage 1: Money at Risk Ingestion (Real-Time Events)
* **Ingress Boundary:** Intercepts real-time payment failure telemetry (`payment.failed`, `subscription.charged.failed`, `subscription.halted`) emitted by Razorpay webhooks or merchant core business systems.
* **Perimeter Verification:** Performs immediate constant-time SHA256 HMAC signature verification (`X-Razorpay-Signature`) at network ingress.
* **Traceability:** Maps directly to `docs/04-data-flow.md` (Phase 1) and `docs/06-razorpay-integration.md`.

### Stage 2: Revenue Risk Detection & Case Creation
* **Risk Quantification:** Converts raw paise amounts into INR ($\text{₹}$) to establish immediate uncaptured financial exposure ($\text{RaR}$).
* **Case Initialization:** Instantiates a unique state record (`case_id`) with primary key deduplication on `event_id` to prevent duplicate concurrent workflows.
* **Risk Tier Assignment:** Categorizes case into `HIGH_RISK` ($>\text{₹}5,000$), `MEDIUM_RISK` ($\text{₹}1,000 - \text{₹}5,000$), or `LOW_RISK` ($<\text{₹}1,000$).
* **Traceability:** Maps directly to `docs/08-revenue-risk-engine.md` and `docs/05-api-contract.md`.

### Stage 3: Failure Root-Cause Diagnosis
* **Telemetry Parsing:** Analyzes raw gateway decline codes (`error.code`, `error.reason`, `error.source`).
* **Taxonomy Mapping:** Maps technical errors into one of four core failure categories:
  1. `LIQUIDITY_FRICTION` (Insufficient funds, transient cashflow gap)
  2. `TRANSIENT_INFRASTRUCTURE` (Bank switch timeout, gateway 5xx)
  3. `INSTRUMENT_INVALIDATION` (Expired card, lost/stolen card flag)
  4. `MANDATE_COMPLIANCE_LOCK` (RBI e-mandate registration or execution lock)
* **Traceability:** Maps directly to `docs/06-razorpay-integration.md` (Decline Taxonomy).

### Stage 4: AI Decision Agent (Contextual Proposal Generation)
* **Zero-Trust Boundary:** The LLM operates purely as a probabilistic candidate plan generator with **zero direct access** to Razorpay API keys or execution handles.
* **Context Prompt Injection:** Formats customer tier, subscription billing history, diagnosed failure cause, and risk amount into structured prompts.
* **Structured Output Enforcement:** Uses `openai` + `instructor` to enforce rigid Pydantic JSON outputs (`ProposedRecoveryPlan`).
* **Traceability:** Maps directly to `docs/07-ai-agent-design.md` and `docs/14-security.md`.

### Stage 5: Open Policy Agent (OPA) Hard Brakes (Governance Gate)
* **Deterministic Firewall:** Evaluates the candidate recovery plan against immutable Rego policies (`policies/governance.rego`, `policies/retry.rego`).
* **Compliance Checks:** Enforces strict compliance rules:
  - `RULE-001: MAX_RECOVERY_ATTEMPTS` (Hard stop at 3 retries)
  - `RULE-002: MINIMUM_COOLDOWN_WINDOW` (Minimum 24h cooldown)
  - `RULE-003: BLOCK_ON_TERMINAL_FAILURE` (Zero retries on expired cards/accounts)
  - `RULE-005: RBI_PREDEBIT_NOTICE_VALIDATION` (24h advance pre-debit notification requirement)
* **Hard Brake Veto:** If any policy is violated, OPA issues an immediate hard block (`approved: false`), halting automated execution and escalating the case.
* **Traceability:** Maps directly to `docs/09-governance-and-policies.md`.

### Stage 6: Temporal Workflow Orchestration
* **Durable Execution Engine:** Manages long-running recovery sagas across multi-day wait timers with $O(1)$ RAM space complexity.
* **Time-Travel Reliability:** Ensures sleeping workflows survive server crashes, worker restarts, or infrastructure migration without losing state.
* **Traceability:** Maps directly to `docs/10-recovery-workflows.md` and `docs/16-deployment.md`.

### Stage 7: Recovery Action Dispatch & Outcome Tracking
* **Idempotent Dispatch:** Executes approved actions (e.g., Razorpay Subscription Retry API, Payment Link creation, Novu Hinglish WhatsApp notification) using deterministic idempotency keys (`rec_idemp_<event_id>_<attempt>`).
* **Terminal Status Resolution:** Tracks outcome resolution to one of two final states:
  - **`RECOVERED`**: Payment successfully captured and settled on Razorpay rails.
  - **`FAILED`**: Max retries reached, hard decline confirmed, or policy stopped.
* **Traceability:** Maps directly to `docs/06-razorpay-integration.md` and `docs/10-recovery-workflows.md`.

### Stage 8: Audit Trail & Operational Metrics
* **Tamper-Evident Commitment:** Commits an immutable JSON receipt containing diagnosis, risk score, AI proposal, OPA token, and settlement status to the `immudb` append-only Merkle tree ledger.
* **Dashboard Verification:** Exposes 1-click ledger verification in the React Finance Controller Dashboard.
* **Traceability:** Maps directly to `docs/11-audit-trail.md` and `docs/13-dashboard-specification.md`.

### Stage 9: Comparative Batch Evaluation Framework
* **The Core Question:** Evaluates performance against the ultimate question: *"Did we recover MORE money than the baseline?"*
* **Counterfactual Benchmark:** Evaluates 500 synthetic failure cases counterfactually against a fixed-retry baseline (`FIXED_RETRY_BASELINE`).
* **ROI Attribution:** Calculates Incremental Revenue Recovery ($\text{IRR} = \text{RR}_{\text{RecoverAI}} - \text{RR}_{\text{Baseline}}$) and verifies 0% governance violations.
* **Traceability:** Maps directly to `docs/12-batch-evaluation.md`.

---

## 3. System-Wide Consistency & Specification Matrix

The table below verifies that every stage of the operational execution model is 100% consistent across the entire repository documentation suite:

| Execution Stage | Underlying Specification Files | Key Consistency Requirement |
| :--- | :--- | :--- |
| **Ingestion** | `docs/04-data-flow.md`, `docs/05-api-contract.md`, `docs/06-razorpay-integration.md` | SHA256 HMAC verification, FastAPI `POST /webhooks/razorpay` |
| **Risk & Case** | `docs/08-revenue-risk-engine.md`, `docs/05-api-contract.md` | Non-inflated uncaptured invoice amount, `case_id` deduplication |
| **Diagnosis** | `docs/06-razorpay-integration.md`, `docs/07-ai-agent-design.md` | Gateway decline taxonomy mapping (`LIQUIDITY_FRICTION`, etc.) |
| **AI Decision** | `docs/07-ai-agent-design.md`, `docs/14-security.md` | Instructor Pydantic schema validation, Zero-Trust isolated execution |
| **OPA Governance** | `docs/09-governance-and-policies.md`, `policies/governance.rego` | Immutable Rego rules (`RULE-001` to `RULE-005`), Hard brake veto |
| **Temporal Saga** | `docs/10-recovery-workflows.md`, `docs/16-deployment.md` | `RecoverySagaWorkflow`, durable sleep timers, task queue |
| **Action & Outcome**| `docs/06-razorpay-integration.md`, `docs/10-recovery-workflows.md` | Idempotency keys (`rec_idemp_...`), Razorpay API & Novu notifications |
| **Audit Ledger** | `docs/11-audit-trail.md`, `docs/13-dashboard-specification.md` | `immudb` append-only Merkle tree, React 1-click hash verification |
| **Batch Proof** | `docs/12-batch-evaluation.md`, `docs/17-demo-script.md`, `README.md` | Incremental Revenue Recovery ($\text{IRR}$), 500-case simulator |

---

## 4. Mathematical Formula for Incremental Recovery

The core evaluation objective of RecoverAI is governed by the following mathematical identity:

$$\boxed{\text{Incremental Revenue Recovered (IRR)} = \sum_{i \in \text{RecoverAI Captured}} \text{Amount}_i - \sum_{j \in \text{Baseline Captured}} \text{Amount}_j}$$

Subject to the mandatory constraints:
$$\text{Governance Violation Rate (GVR)} = 0.0\%$$
$$\text{Audit Trail Completeness (ACP)} = 100.0\%$$

---

## 5. Document Metadata & Sign-off

* **Author:** Fintech System Architect & Lead Systems Engineer / Track 3 Team  
* **Target Buildathon:** Razorpay AI Buildathon — Track 3 (AI Revenue Recovery)  
* **Upstream Specification:** `docs/01-problem-statement.md` through `docs/17-demo-script.md`, `README.md`  
* **Implementation Artifacts:** `docs/18-execution-model.md`  
