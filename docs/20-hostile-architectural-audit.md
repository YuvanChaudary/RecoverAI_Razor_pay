# Hostile Fintech Architectural Audit & Refinement Report
**Project:** RecoverAI — Bounded Autonomous Revenue Recovery Agent  
**Target Buildathon:** Razorpay AI Buildathon (Track 3: AI Revenue Recovery)  
**Document ID:** `docs/20-hostile-architectural-audit.md`  
**Audit Role:** Principal Fintech Architect, Senior AI Engineer, Razorpay Integration Expert & RegTech Auditor  
**Final Audit Verdict:** **B+ STRONG ENTERPRISE ARCHITECTURE (APPROVED WITH REFINED CONTRACTS)**  

---

## Executive Summary

This document presents an unsparing architectural audit and refinement specification for **RecoverAI**. It codifies the precise separation between probabilistic AI reasoning and deterministic financial safety, enforces counterfactual baseline benchmarks, eliminates inaccurate regulatory claims, defines the two-mode execution environment (Live Test Mode vs. Evaluation Mode), and establishes the authoritative ground-truth state machine.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    CLOSED-LOOP RECOVERAI PIPELINE                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [ Real / Simulated Inbound Event ] (Razorpay Webhook / Synthetic Bus)   │
│                   │                                                      │
│                   ▼                                                      │
│  [ Revenue Risk Detection & Case Creation ] (RaR Face Value Accounting)  │
│                   │                                                      │
│                   ▼                                                      │
│  [ Failure Diagnosis Engine ] (Decline Code Taxonomy Mapping)            │
│                   │                                                      │
│                   ▼                                                      │
│  [ NVIDIA NIM AI Reasoning ] (Contextual Proposal: "What to attempt?")   │
│                   │                                                      │
│                   ▼                                                      │
│  [ OPA Governance Firewall ] (Deterministic Gate: "Allowed?")            │
│                   │                                                      │
│                   ▼                                                      │
│  [ Temporal Durable Saga ] (Workflow State & Sleep Timers)               │
│                   │                                                      │
│                   ▼                                                      │
│  [ Action Dispatch ] (Razorpay API / Novu Notification)                  │
│                   │                                                      │
│                   ▼                                                      │
│  [ Authoritative Outcome Resolution ] (Razorpay `payment.captured`)     │
│                   │                                                      │
│                   ▼                                                      │
│  [ Recovered Revenue Calculation ] (sum(case.recovered_amount))          │
│                   │                                                      │
│                   ▼                                                      │
│  [ Cryptographic immudb Audit ] (SHA-256 Merkle Tree Receipt)            │
│                   │                                                      │
│                   ▼                                                      │
│  [ React Finance Controller Dashboard ] (Live Stream & Incremental Lift) │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 1. System Responsibility Division: AI vs. Deterministic Core

To pass enterprise compliance and buildathon judging, RecoverAI strictly isolates probabilistic LLM outputs from financial state management.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    DETERMINISTIC vs AI BOUNDARIES                        │
├──────────────────────────────────────┬───────────────────────────────────┤
│ Deterministic Backend (FastAPI / OPA)│ AI Reasoning Engine (NVIDIA NIM)  │
├──────────────────────────────────────┼───────────────────────────────────┤
│ • HMAC SHA256 Webhook Verification   │ • Failure root-cause diagnosis    │
│ • Face Value Revenue at Risk (RaR ₹) │ • Payday-aligned retry delay      │
│ • Merchant Safety Policy (Max 3)     │ • Hinglish dunning message tone   │
│ • Cooldown Window Enforcement (24h)  │ • Recommended Action Proposal     │
│ • Authoritative Payment Capture      │ • Candidate plan confidence score │
│ • immudb SHA-256 Merkle Proofs       │                                   │
│ • Summed Recovered Revenue ($\sum A$)│ NEVER: Modifies status or amounts │
└──────────────────────────────────────┴───────────────────────────────────┘
```

### NVIDIA NIM Proposal Schema
```json
{
  "root_cause": "LIQUIDITY_FRICTION",
  "recommended_action": "RETRY_SCHEDULED",
  "delay_hours": 48,
  "dunning_channel": "WHATSAPP_HINGLISH",
  "reasoning": "High-value customer experiencing transient cashflow gap 2 days prior to salary credit date."
}
```

---

## 2. Regulatory & Architectural Terminology Corrections

1. **Merchant Safety Policy vs. Regulatory Claims:**
   - **Incorrect:** *"Statutory Retry Cap (Max 3 retries required by RBI)."*
   - **Correct:** *"Merchant-Configurable Safety Policy (Maximum 3 retries, 24-hour minimum cooldown). Applicable statutory constraints (e.g., RBI e-mandate 24-hour advance pre-debit notifications) are enforced independently."*
2. **Space & Time Complexity Precision:**
   - **Incorrect:** *"The entire system is $O(1)$ space."*
   - **Correct:** *"The event-processing path uses bounded in-memory context per event ($O(1)$ space complexity per task); persistent state is externalized to PostgreSQL, Temporal, and immudb. Batch evaluation executes in $O(N)$ case processing time."*
3. **Role of immudb:**
   - **Incorrect:** *"immudb proves that Razorpay captured the money."*
   - **Correct:** *"Razorpay `payment.captured` webhooks prove payment settlement; immudb cryptographic receipts prove the tamper-evident integrity of our internal state transition record."*
4. **Agent Framing:**
   - **Incorrect:** *"Fully autonomous financial AI that guarantees recovery."*
   - **Correct:** *"Bounded autonomous revenue recovery agent where AI selects contextual interventions, bounded by OPA governance, and measured strictly from verified payment outcomes."*

---

## 3. Dual Execution Modes: Live Test Mode vs. Evaluation Mode

RecoverAI supports two distinct operational modes sharing the exact same backend engine:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       DUAL EXECUTION MODES                               │
├───────────────────────────────────┬──────────────────────────────────────┤
│ Mode A: Live / Test Mode          │ Mode B: Batch Evaluation Mode        │
├───────────────────────────────────┼──────────────────────────────────────┤
│ • Inbound: Razorpay Test Webhook  │ • Inbound: 500 Synthetic Event Bus   │
│ • Processing: RecoverAI Pipeline  │ • Processing: RecoverAI Pipeline     │
│ • Execution: Real Razorpay API    │ • Executor: Ground-Truth Simulator   │
│ • Outcome: Razorpay `pay_test_...`│ • Outcome: Stochastic ground truth   │
│ • Proves: Real API Integration    │ • Proves: Statistical ROI & Lift     │
└───────────────────────────────────┴──────────────────────────────────────┘
```

---

## 4. 500-Case Simulator & Ground-Truth Architecture

In Evaluation Mode, the simulator **never** bypasses RecoverAI to output a hardcoded recovery percentage. Instead, the simulator operates as an independent Ground-Truth Environment:

```
                     500 SYNTHETIC EVENTS
                              │
                              ▼
                [ Synthetic Event Generator ]
                              │
                              ▼
               ┌─────────────────────────────┐
               │ Ground-Truth Environment    │
               │ (Probability Distributions) │
               └──────────────┬──────────────┘
                              ▼
                   [ RecoverAI Pipeline ]
                   (Risk → AI → OPA → Temporal)
                              │
                              ▼
                [ Simulated Action Executor ]
                              │
                              ▼
               ┌─────────────────────────────┐
               │ Ground-Truth Outcome Engine │
               │ (Evaluates Action Success)  │
               └──────────────┬──────────────┘
                              ▼
                  RECOVERED / STILL_FAILED
                              │
                              ▼
                 Summed Actual Recoveries ($\sum A_i$)
```

---

## 5. Mathematical Proof of Incremental Revenue Recovery

Revenue recovery is calculated mathematically from authoritative captured cases, never guessed by LLMs:

$$\text{Total Revenue at Risk (RaR)} = \sum_{i=1}^{N} \text{Unresolved Invoice Amount}_i$$

$$\text{Total Recovered Revenue (RR)} = \sum_{j \in \text{Captured Cases}} \text{Captured Amount}_j$$

$$\text{Incremental Revenue Recovery (IRR)} = \text{RR}_{\text{RecoverAI}} - \text{RR}_{\text{Baseline}}$$

$$\text{Recovery Lift (\%)} = \left( \frac{\text{RR}_{\text{RecoverAI}} - \text{RR}_{\text{Baseline}}}{\text{RR}_{\text{Baseline}}} \right) \times 100$$

### Benchmark Cohorts
1. **`NO_RETRY` (Control A):** Zero recovery attempts ($0\%$ recovery rate).
2. **`FIXED_RETRY_BASELINE` (Control B):** Blind static retry schedule (24h/48h retries, no AI diagnosis, no OPA cooldown customization).
3. **`RECOVERAI` (Treatment C):** Full pipeline (Diagnosis + NVIDIA NIM + OPA Governance + Temporal Saga).

---

## 6. Dynamic Reasoning Proof (5 Contextual Cases)

To prove during demonstrations that NVIDIA NIM reasons dynamically rather than executing static rules:

```json
[
  {
    "case_id": "ADV_001",
    "context": "Amount = ₹4,999; Failure = NSF; Billing = 21st; Salary Day = 23rd; Retry = 0",
    "ai_proposal": "RETRY_SCHEDULED (Delay 48h to salary date + WhatsApp Hinglish)",
    "opa_decision": "APPROVED",
    "execution_path": "Temporal sleep 48h -> Retry -> CAPTURED"
  },
  {
    "case_id": "ADV_002",
    "context": "Amount = ₹499; Failure = EXPIRED_CARD; Retry = 0",
    "ai_proposal": "REQUEST_PAYMENT_METHOD_UPDATE (Email/SMS Re-auth Link)",
    "opa_decision": "APPROVED",
    "execution_path": "Dispatch Link -> Customer Updates Card -> CAPTURED"
  },
  {
    "case_id": "ADV_003",
    "context": "Amount = ₹1,50,000; Failure = MANDATE_REVOKED; Retry = 0",
    "ai_proposal": "ESCALATE_TO_HUMAN (Enterprise Collections Team)",
    "opa_decision": "APPROVED",
    "execution_path": "Create High-Priority Dashboard Ticket -> Human Outreach"
  },
  {
    "case_id": "ADV_004",
    "context": "Amount = ₹1,999; Failure = BANK_SWITCH_TIMEOUT; Retry = 0",
    "ai_proposal": "RETRY_NOW (Exponential Backoff 1h)",
    "opa_decision": "APPROVED",
    "execution_path": "Temporal sleep 1h -> Retry -> CAPTURED"
  },
  {
    "case_id": "ADV_005",
    "context": "Amount = ₹2,499; Failure = NSF; Retry = 3 (Merchant Limit)",
    "ai_proposal": "RETRY_SCHEDULED",
    "opa_decision": "VETOED (RULE-001: Max Retries Exceeded)",
    "execution_path": "Hard Stop -> Case Marked STOPPED_BY_POLICY"
  }
]
```

---

## 7. Authoritative State Machine & Transition Rules

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   AUTHORITATIVE STATE MACHINE                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [ DETECTED ] ──► [ VALIDATED ] ──► [ DIAGNOSING ] ──► [ AI_DECISION ]  │
│                                                               │          │
│                                                               ▼          │
│  [ ACTION_EXECUTED ] ◄── [ ACTION_SCHEDULED ] ◄─── [ OPA_CHECK ]         │
│          │                                                               │
│          ▼                                                               │
│  [ RECOVERY_PENDING ] ──► (Authoritative Razorpay Event)                 │
│          ├──► [ RECOVERED ] (Verified `payment.captured`)                │
│          ├──► [ STILL_FAILED ] (Retry Limit Exhausted)                   │
│          ├──► [ ESCALATED ] (Human Ticket Created)                       │
│          └──► [ STOPPED_BY_POLICY ] (OPA Hard Veto)                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Prohibited Illegal State Transitions
* $\text{AI\_DECISION} \longrightarrow \text{RECOVERED}$ (FORBIDDEN: Requires authoritative capture event)
* $\text{OPA\_VETOED} \longrightarrow \text{ACTION\_EXECUTED}$ (FORBIDDEN: Overriding OPA is impossible)
* $\text{ACTION\_EXECUTED} \longrightarrow \text{RECOVERED}$ (FORBIDDEN: Requires `payment.captured` payload)

---

## 8. Adjusted 13-Phase Monorepo Execution Roadmap

```
PHASE 0 : API Credentials & Infrastructure Verification (Pre-Flight Check)
           (Razorpay Test Keys, NVIDIA NIM, OPA, Temporal, immudb, Novu, PostgreSQL)
PHASE 1 : Core Configuration & Async PostgreSQL Models
PHASE 2 : Razorpay Webhook Ingestion Endpoint & SHA256 Verification
PHASE 3 : Revenue Risk Accounting Engine & Failure Diagnosis
PHASE 4 : NVIDIA NIM AI Agent & Instructor Pydantic Schema Integration
PHASE 5 : Open Policy Agent (OPA) Rego Governance Engine & Pytest Suite
PHASE 6 : Temporal.io Durable Saga Workflows & Activity Definitions
PHASE 7 : Real External API Integration (Razorpay Test API & Novu WhatsApp API)
PHASE 8 : Cryptographic Audit Ledgering (immudb Merkle Tree Commitments)
PHASE 9 : 500-Case Evaluation Engine & Baseline Counterfactual Benchmark
PHASE 10: React Finance Controller Dashboard UI / UX
PHASE 11: End-to-End Chaos Testing & Time-Travel Verification
PHASE 12: Buildathon Final Pitch Video & Live Demo Protocol
```

---

## 9. Document Metadata & Sign-off

* **Lead Auditor:** Principal Fintech Architect & RegTech Compliance Lead  
* **Target Buildathon:** Razorpay AI Buildathon — Track 3 (AI Revenue Recovery)  
* **Upstream Specification:** `docs/01-problem-statement.md` through `docs/19-real-time-revenue-risk-detection.md`, `README.md`  
* **Implementation Artifacts:** `docs/20-hostile-architectural-audit.md`  
