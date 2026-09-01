# OPA Governance & Policy Engine Specification
**Project:** Razorpay AI Buildathon (Track 3)  
**Document ID:** `docs/09-governance-and-policies.md`  
**Status:** Approved Architectural Baseline  

---

## Executive Summary

This document specifies the architecture, policy rules, evaluation schemas, state transition logic, and audit trail guarantees of the **Open Policy Agent (OPA) Governance Engine**. Serving as the "Inner Trust Boundary" of the AI Revenue Recovery Agent, this deterministic, Wasm/Go-based policy sidecar enforces strict compliance with Reserve Bank of India (RBI) e-mandate guidelines, acquirer velocity limits, and merchant-defined business rules. Operating under the "AI Proposes, OPA Disposes" principle, the Governance Gate guarantees that no probabilistic LLM output can execute a payment retry or dunning action without passing immutable compliance evaluation.

---

## 1. Overview & Zero-Trust Architecture

In financial technology, AI-driven automation cannot operate as an unconstrained decision maker. Generative AI models are inherently probabilistic and subject to hallucination, model drift, or prompt exploitation.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      ZERO-TRUST GOVERNANCE GATE                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Probabilistic LLM Decision Engine                                       │
│  (Claude 3.5 / GPT-4o)                                                   │
│         │                                                                │
│         ▼ (Proposed Recovery Plan - Untrusted Candidate Payload)         │
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │ HARD INNER TRUST BOUNDARY: Open Policy Agent (Rego Rule Engine)      │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
│         │                                                                │
│         ├── APPROVED (allow: true)  ──► Action Dispatcher (Razorpay API)│
│         └── BLOCKED  (allow: false) ──► Human Escalation Queue + immudb │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Core Tenets of the Governance Gate
1. **AI Proposes, OPA Disposes:** The LLM proposes a recovery strategy based on contextual heuristics; OPA deterministically approves or vetoes the plan against immutable Rego policy files.
2. **Deterministic Immutability:** Policy rules are written in declarative Rego code. They execute identically under all conditions regardless of AI model versions or system load.
3. **Fail-Closed Default:** If an OPA query times out, encounters an unhandled rule combination, or receives corrupted input, the engine defaults to `approved: false` (Fail-Closed Security).

---

## 2. Formal Policy Definitions

The system enforces five mandatory enterprise policy rules categorized by regulatory mandate and business guardrail:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         POLICY RULE DIRECTORY                            │
├──────────┬─────────────────────────────────┬───────────┬─────────────────┤
│ Rule ID  │ Policy Name                     │ Category  │ Severity Level  │
├──────────┼─────────────────────────────────┼───────────┼─────────────────┤
│ RULE-001 │ MAX_RECOVERY_ATTEMPTS           │ Regulatory│ HARD_BLOCK      │
│ RULE-002 │ MINIMUM_COOLDOWN_WINDOW         │ Regulatory│ HARD_BLOCK      │
│ RULE-003 │ BLOCK_ON_TERMINAL_FAILURE       │ Business  │ HARD_BLOCK      │
│ RULE-004 │ ESCALATE_ON_LOW_CONFIDENCE      │ Governance│ HARD_BLOCK      │
│ RULE-005 │ RBI_PREDEBIT_NOTICE_VALIDATION  │ Regulatory│ HARD_BLOCK      │
└──────────┴─────────────────────────────────┴───────────┴─────────────────┘
```

### `RULE-001: MAX_RECOVERY_ATTEMPTS` (Regulatory / Velocity Cap)
* **Description:** Restricts the total number of automated retry attempts to a maximum of 3 retries per billing cycle to comply with RBI e-mandate guidelines and acquirer velocity limits.
* **Evaluation Condition:** `input.current_retry_count >= 3`
* **Action on Breach:** `approved: false`, `veto_reason: "Maximum automated retry limit (3) reached for this subscription cycle."`

### `RULE-002: MINIMUM_COOLDOWN_WINDOW` (Regulatory / Cooldown)
* **Description:** Enforces a mandatory 24-hour minimum waiting period between consecutive automated debit execution attempts.
* **Evaluation Condition:** `input.time_since_last_attempt_hours < 24`
* **Action on Breach:** `approved: false`, `veto_reason: "Minimum 24-hour cooldown period between retries has not elapsed."`

### `RULE-003: BLOCK_ON_TERMINAL_FAILURE` (Business / Cost Avoidance)
* **Description:** Hard-blocks API retries when the root cause diagnosis indicates a terminal instrument or account failure (e.g., `CARD_EXPIRED`, `ACCOUNT_CLOSED`, `MANDATE_REVOKED`).
* **Evaluation Condition:** `input.diagnosed_cause IN ["CARD_EXPIRED", "ACCOUNT_CLOSED", "MANDATE_REVOKED"] AND input.proposed_action == "SCHEDULE_RETRY"`
* **Action on Breach:** `approved: false`, `veto_reason: "Terminal failure condition detected. Automated retries are prohibited."`

### `RULE-004: ESCALATE_ON_LOW_CONFIDENCE` (Governance / Model Safety)
* **Description:** Vetoes AI recovery plans if the LLM confidence score drops below the 0.80 safety threshold.
* **Evaluation Condition:** `input.ai_confidence_score < 0.80`
* **Action on Breach:** `approved: false`, `veto_reason: "AI confidence score (0.74) is below the minimum required threshold (0.80)."`

### `RULE-005: RBI_PREDEBIT_NOTICE_VALIDATION` (Regulatory / Pre-debit Notice)
* **Description:** Ensures that an automated debit retry is executed only if a valid RBI pre-debit notification was dispatched to the subscriber at least 24 hours prior.
* **Evaluation Condition:** `input.proposed_action == "SCHEDULE_RETRY" AND input.pre_debit_notice_sent == false`
* **Action on Breach:** `approved: false`, `veto_reason: "RBI e-mandate pre-debit notification has not been issued 24h prior to retry."`

---

## 3. OPA Evaluation Schema

The Temporal workflow queries the embedded OPA sidecar endpoint (`POST /v1/data/recovery/governance/allow`) passing the context payload.

### 3.1 OPA Request Payload (Input JSON)

```json
{
  "input": {
    "case_id": "case_rec_01J8A9X4K2M3N4P5",
    "subscription_id": "sub_PZ100s1T2u3V4W",
    "current_retry_count": 1,
    "time_since_last_attempt_hours": 72.5,
    "diagnosed_cause": "INSUFFICIENT_FUNDS",
    "pre_debit_notice_sent": true,
    "ai_proposed_plan": {
      "action_type": "SCHEDULE_RETRY",
      "retry_delay_hours": 72,
      "communication_channel": "WHATSAPP",
      "ai_confidence_score": 0.94
    },
    "merchant_limits": {
      "max_allowed_retries": 3,
      "min_cooldown_hours": 24
    }
  }
}
```

### 3.2 OPA Response Payload (Approval Example - HTTP 200)

```json
{
  "result": {
    "approved": true,
    "enforced_rule_id": "RULE_ALL_PASS",
    "veto_reason": null,
    "evaluated_at": 1724180405,
    "policy_version": "v1.4.2",
    "verification_token": "tok_opa_APPROVED_987654321_HASH_a8f9c0d1"
  }
}
```

### 3.3 OPA Response Payload (Veto/Block Example - HTTP 200)

```json
{
  "result": {
    "approved": false,
    "enforced_rule_id": "RULE-002",
    "veto_reason": "Minimum 24-hour cooldown period between retries has not elapsed.",
    "evaluated_at": 1724180405,
    "policy_version": "v1.4.2",
    "verification_token": "tok_opa_BLOCKED_RULE002_HASH_b9e8d7c6"
  }
}
```

---

## 4. State Transitions on Block

When OPA returns `approved: false`, the system initiates a graceful, deterministic state transition. The workflow **never crashes or throws unhandled exceptions**.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      STATE TRANSITION WORKFLOW                           │
├──────────────────────────────────────────────────────────────────────────┤
│ OPA Response: approved == false                                          │
│ └── ► Update State: GOVERNANCE_BLOCKED                                   │
│     └── ► Halt Automated Execution (0 Calls to Razorpay Retry API)       │
│         ├── Route to Escalation Queue (React Finance Dashboard)          │
│         └── Log Veto Token & Reason to immudb Ledger                     │
└──────────────────────────────────────────────────────────────────────────┘
```

1. **Immediate Execution Freeze:** The Temporal Action Dispatcher activity skips external API calls. Zero charges or retries are dispatched to Razorpay.
2. **State Machine Commit:** The PostgreSQL operational database updates the case status to `GOVERNANCE_BLOCKED` and sets `workflow_state = "AUTOMATED_RECOVERY_STOPPED"`.
3. **Escalation Queue Dispatch:** The case is routed directly to the React Finance Dashboard's **Human Escalation Review Queue**, enabling Finance Controllers to manually review the veto reason and override or cancel the subscription.

---

## 5. Auditability Guarantee & Cryptographic Ledgering

Every single OPA evaluation decision—regardless of whether it yields an approval (`approved: true`) or a veto (`approved: false`)—is appended to the `immudb` cryptographic ledger.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       IMMUDB AUDIT RECEIPT SCHEMA                        │
├──────────────────────────────────────────────────────────────────────────┤
│ {                                                                        │
│   "tx_id": 4820195,                                                      │
│   "case_id": "case_rec_01J8A9X4K2M3N4P5",                               │
│   "opa_decision": "BLOCKED",                                             │
│   "enforced_rule_id": "RULE-002",                                        │
│   "veto_reason": "Minimum 24-hour cooldown period not elapsed.",         │
│   "verification_token": "tok_opa_BLOCKED_RULE002_HASH_b9e8d7c6",        │
│   "payload_hash": "f4e3d2c1b0a987654321fedcba9876543210123456789",       │
│   "timestamp": 1724180405                                                │
│ }                                                                        │
└──────────────────────────────────────────────────────────────────────────┘
```

* **Non-Repudiable Evidence:** Demonstrates 100% regulatory compliance during RBI or acquirer audits by providing tamper-evident cryptographic Merkle tree proofs for every recovery decision.

---

## 6. Document Metadata & Sign-off

* **Author:** Fintech System Architect / Track 3 Engineering Team  
* **Target Buildathon:** Razorpay AI Buildathon — Track 3 (AI Revenue Recovery)  
* **Upstream Specification:** `docs/01-problem-statement.md`, `docs/03-system-architecture.md`, `docs/04-data-flow.md`, `docs/07-ai-agent-design.md`  
* **Implementation Artifacts:** `docs/09-governance-and-policies.md`  
