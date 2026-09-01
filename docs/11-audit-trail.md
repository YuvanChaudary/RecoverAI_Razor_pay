# Cryptographic Audit Ledger & Compliance Specification
**Project:** Razorpay AI Buildathon (Track 3)  
**Document ID:** `docs/11-audit-trail.md`  
**Status:** Approved Architectural Baseline  

---

## Executive Summary

This document specifies the architecture, JSON payload schema, integration flow, and audit read paths for the **Cryptographic Audit Ledger**. Operating on `immudb` (an append-only, tamper-evident cryptographic database), this layer records non-repudiable audit receipts for every payment failure event processed by the **AI Revenue Recovery Agent**. By linking failure telemetry, AI reasoning traces, OPA policy tokens, execution API responses, and final financial settlement outcomes into a SHA-256 hash-chained ledger, the system satisfies SOC2 Type II, PCI-DSS, and RBI financial compliance standards.

---

## 1. Overview & Compliance Philosophy

### 1.1 The Inadequacy of Standard SQL Databases
In autonomous fintech systems, standard relational SQL databases (`UPDATE` / `INSERT`) are structurally insufficient for compliance:
* **Mutation Vulnerability:** A standard `UPDATE subscription SET status = 'recovered'` overwrites historical state, making it impossible to prove what the exact system state was at the moment of decision.
* **Repudiation Risk:** Database administrators or malicious actors can alter records directly via SQL connection, invalidating audit integrity.
* **AI Explainability Deficit:** Finance Controllers cannot verify whether an automated retry was executed legally under RBI rules or hallucinated by an LLM without an immutable event record.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         MUTABLE VS. IMMUTABLE                            │
├───────────────────────────────┬──────────────────────────────────────────┤
│ Standard Relational SQL       │ immudb Cryptographic Ledger              │
├───────────────────────────────┼──────────────────────────────────────────┤
│ Mutable state (`UPDATE` queries)│ Append-only cryptographic ledger       │
│ Vulnerable to admin tampering │ Tamper-evident Merkle tree roots         │
│ No cryptographic linkage      │ SHA-256 hash chains per transaction      │
│ Inadequate for SOC2/PCI audits│ Non-repudiable financial audit evidence  │
└───────────────────────────────┴──────────────────────────────────────────┘
```

### 1.2 The Cryptographic Ledger Guarantee
Every state transition within the AI Revenue Recovery Agent generates an **Immutable Audit Receipt**. The receipt is hashed using SHA-256 and committed to `immudb`. If any byte in historical audit records is modified post-commit, the cryptographic Merkle tree root hash verification fails immediately, alerting compliance officers to data tampering.

---

## 2. Comprehensive Audit Payload Schema

The following JSON object represents the complete, aggregated payload committed to `immudb` at the conclusion of a recovery workflow loop:

```json
{
  "audit_version": "v1.0.0",
  "receipt_id": "rcpt_01J8A9X4K2M3N4P5Q6R7S8T9U0",
  "timestamp": 1724439612,
  "identifiers": {
    "case_id": "case_rec_01J8A9X4K2M3N4P5",
    "event_id": "evt_01J8A9X4K2M3N4P5Q6R7S8T9U0",
    "subscription_id": "sub_PZ100s1T2u3V4W",
    "original_payment_id": "pay_PZ182x9A7kL3mQ",
    "customer_id": "cust_PZ088x9Y0z1A2B"
  },
  "financial_context": {
    "raw_amount_paise": 299900,
    "revenue_at_risk_inr": 2999.00,
    "currency": "INR",
    "risk_tier": "MEDIUM_RISK",
    "priority_score": 0.89
  },
  "diagnosis": {
    "error_code": "BAD_REQUEST_ERROR",
    "error_reason": "insufficient_funds",
    "error_source": "issuing_bank",
    "diagnosed_root_cause": "LIQUIDITY_FRICTION",
    "is_hard_decline": false,
    "payday_window_detected": true
  },
  "ai_decision": {
    "recommended_action": "SCHEDULE_RETRY",
    "retry_delay_hours": 72,
    "communication_channel": "WHATSAPP",
    "dunning_template_id": "tpl_payday_grace_hinglish_v2",
    "reasoning": "Decline caused by NSF on 20th. Historical salary cycle indicates account replenishment on 23rd. High LTV subscriber warrants a 72-hour retry delay combined with a polite Hinglish WhatsApp notification.",
    "confidence_score": 0.94,
    "langfuse_trace_id": "trc_langfuse_9988776655443322"
  },
  "governance": {
    "opa_status": "APPROVED",
    "evaluated_policy_version": "v1.4.2",
    "applied_rules": [
      "rule_rbi_predebit_notice_24h_pass",
      "rule_cooldown_window_48h_pass",
      "rule_merchant_max_retries_pass"
    ],
    "policy_hash": "a8f9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9",
    "verification_token": "tok_opa_APPROVED_987654321_HASH_a8f9c0d1"
  },
  "execution": {
    "action_type": "RAZORPAY_INVOICE_RETRY",
    "executed_at": 1724439610,
    "razorpay_invoice_id": "inv_PZ166x1Y2z3A4B",
    "razorpay_payment_id": "pay_PZ999_RECOVERED",
    "settlement_status": "captured",
    "idempotency_key": "rec_idemp_evt_01J8A9X4K2M3N4P5_attempt_1",
    "novu_message_id": "msg_nov_44556677"
  },
  "outcome": {
    "final_case_status": "RECOVERED",
    "recovered_amount_inr": 2999.00,
    "net_financial_result": "REVENUE_SETTLED_SUCCESSFULLY"
  },
  "cryptographic_proof": {
    "payload_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "immudb_tx_id": 4820194,
    "immudb_tree_root_hash": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
  }
}
```

---

## 3. System Integration & Temporal Activity Flow

The cryptographic audit receipt is committed as the **final, atomic Activity** in the `RecoverySaga` Temporal workflow:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      ATOMIC COMMIT PIPELINE                              │
├──────────────────────────────────────────────────────────────────────────┤
│ Phase 1-6: Ingest ──► Risk ──► Diagnose ──► AI ──► OPA ──► Execute      │
│                                                                          │
│  7. CommitImmudbLedgerActivity (Final Atomic Activity)                   │
│     ├── Compute SHA-256 Hash of Aggregated Case Payload                  │
│     ├── Write Payload to immudb Append-Only Store                        │
│     ├── Extract `immudb_tx_id` and Merkle Root Hash                      │
│     └── Update PostgreSQL Index Record with immudb Transaction Reference   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Why the Log is Written at Workflow Completion
1. **Actual vs. Intended Realization:** Writing the audit log at workflow completion ensures the receipt records the *actual gateway settlement outcome* (`pay_PZ999_RECOVERED`, status = `captured`) alongside the *intended AI action* and *OPA approval token*.
2. **Atomic Execution:** If the payment API call fails mid-way, the audit payload reflects the exact point of failure (`FAILED_RETRY` or `GATEWAY_ERROR`) rather than logging an unfulfilled intention.

---

## 4. Read Path: Dashboard Audit Consumption & Verification

Finance Controllers and auditors consume this data through the **React + Vite Dashboard Audit Explorer**:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   DASHBOARD AUDIT DRILL-DOWN PATH                        │
├──────────────────────────────────────────────────────────────────────────┤
│ User Clicks Case ID in React Dashboard                                   │
│ └── ► API Fetch: `GET /api/v1/cases/{case_id}`                            │
│     ├── Reads Operational Index from PostgreSQL                           │
│     └── Reads Cryptographic Proof Receipt from immudb                     │
│         └── ► Renders 7-Stage Timeline Visualizer                        │
│             └── ► Displays "Verify Ledger Hash" Cryptographic Proof Badge  │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Case Drill-Down View (Full Explainability)
When a Finance Controller selects a case in the UI, the dashboard renders a complete timeline displaying:
1. **Financial Risk Card:** Immediate $\text{RaR}$ and risk tier.
2. **Diagnostic Panel:** Mapped root cause (`LIQUIDITY_FRICTION`) and original decline code.
3. **AI Reasoning Drawer:** Plain-English explanation, proposed action, and clickable link to the **Langfuse LLM Trace** (`trc_langfuse_9988776655443322`).
4. **OPA Compliance Badge:** Signed OPA token (`tok_opa_APPROVED_...`) and verified Rego rule checklist.
5. **Settlement Receipt:** Razorpay payment ID and transaction settlement timestamp.

### 4.2 On-Demand Cryptographic Verification
The React UI features a **"Verify Ledger Proof"** button. Clicking this triggers a client-side or backend call to `immudb`'s verification endpoint:
```http
POST /api/v1/cases/{case_id}/verify-proof
```
The server re-computes the SHA-256 hash of the case payload and verifies it against the Merkle tree root stored in `immudb`. The UI displays a green **"Cryptographically Verified"** badge, guaranteeing the audit record has zero data tampering.

---

## 5. Document Metadata & Sign-off

* **Author:** Fintech System Architect / Track 3 Engineering Team  
* **Target Buildathon:** Razorpay AI Buildathon — Track 3 (AI Revenue Recovery)  
* **Upstream Specification:** `docs/01-problem-statement.md`, `docs/03-system-architecture.md`, `docs/04-data-flow.md`, `docs/09-governance-and-policies.md`, `docs/10-recovery-workflows.md`  
* **Implementation Artifacts:** `docs/11-audit-trail.md`  
