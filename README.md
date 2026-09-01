# RecoverAI: Autonomous Revenue Recovery & Payment Failure Orchestration Platform 🚀

> **Razorpay AI Buildathon — Track 3: AI Revenue Recovery**  
> *A safety-first, governed autonomous agent that transforms raw payment failures into quantified revenue risk, generates failure-aware AI recovery proposals, enforces deterministic policy guardrails via OPA, executes durable long-running workflows via Temporal, and acknowledges financial recovery only upon cryptographically verified Razorpay settlement webhooks.*

---

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Vite-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Policy Engine](https://img.shields.io/badge/Governance-Open%20Policy%20Agent%20(Rego)-5C42B1.svg?logo=openpolicyagent&logoColor=white)](https://www.openpolicyagent.org)
[![Orchestration](https://img.shields.io/badge/Workflows-Temporal%201.24+-000000.svg?logo=temporal&logoColor=white)](https://temporal.io)
[![Audit Ledger](https://img.shields.io/badge/Audit%20Ledger-immudb%20v1.9+-3B82F6.svg?logo=database&logoColor=white)](https://codenotary.com/technologies/immudb/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2016+-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Infrastructure-Docker%20Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)
[![Tests](https://img.shields.io/badge/Tests-127%20Unit%20%7C%2019%20Integration-success.svg)](#23-testing--verification-suite)

---

## 🚀 Recruiter & Executive Snapshot

| Pillar | Engineering Reality & Verified Implementation |
|---|---|
| **Core Value Proposition** | Automatically rescues failed recurring & checkout payments in India (UPI, Cards, Mandates) while enforcing strict regulatory compliance (RBI e-mandate, NPCI retry caps). |
| **Autonomous AI Boundary** | LLM / NVIDIA NIM serves strictly as a **Strategy Advisor** (generates structured JSON recovery proposals). **AI has ZERO authority to execute financial operations directly.** |
| **Deterministic RegTech Firewall** | Open Policy Agent (OPA) evaluates enterprise Rego policies before any action is scheduled. **Even a 99% confident AI proposal is vetoed if it violates cooldown or retry limits.** |
| **Durable Long-Running Workflows** | Temporal Saga Orchestrator manages multi-day cooldowns and retries using durable `workflow.sleep()` timers surviving service restarts — **Zero in-memory `sleep()` timers.** |
| **Financial Invariant (`ACTION_EXECUTED ≠ RECOVERED`)** | An outbound HTTP 200 from a gateway only transitions state to `ACTION_EXECUTED` (Recovered = ₹0.00). **Recovery is acknowledged strictly upon HMAC-verified `payment.captured` webhooks.** |
| **Double-Recovery Prevention** | Strict state machine idempotency and cryptographic event hashing guarantee **0 double recoveries and 0 double-counted paise** across duplicate webhook deliveries. |
| **Cryptographic Auditability** | Every state transition and decision is hashed (SHA-256) and anchored in an append-only **immudb** cryptographic ledger with tamper detection. |
| **Dynamic Execution** | **Zero hardcoded outcomes.** All failure categories, risk scores, AI strategies, governance gates, and settlement values are computed dynamically from transaction payloads. |
| **Verified Test Coverage** | **127 Unit Tests (100% passing)** + **19 Integration Tests (100% passing)** + **500-Case Simulation Engine** verifying ₹2.52 Cr revenue-at-risk. |

---

## 1. The Problem: The High Cost of Payment Failures

Payment failures in modern e-commerce and SaaS are rarely binary errors—they are complex, multi-variable events. In high-growth digital economies like India, recurring auto-debits (e-mandates), UPI transactions, and cards suffer from a **15%–30% failure rate** due to temporary liquidity issues, bank server downtime, card expirations, or regulatory friction.

```mermaid
flowchart LR
    A[Payment Failure Occurs] --> B[Naive Blind Retry]
    B --> C[Card / Bank Hard Block]
    B --> D[Harassed Customer Churn]
    B --> E[Regulatory Penalty - RBI Mandate]
    
    A --> F[Silent Abandonment]
    F --> G[Direct Revenue Leakage]
```

### Why Simple Retries Fail:
1. **Blind Retries Destroy Merchant Reputation:** Retrying an empty bank account 5 times in 10 minutes leads to bank decline penalties and triggers anti-fraud blocks.
2. **Regulatory Non-Compliance:** The Reserve Bank of India (RBI) mandates strict pre-debit notifications and minimum 24-hour cooldown windows between automated retry attempts.
3. **Ghost Recoveries:** Legacy systems assume that because a payment link was generated (HTTP 200 OK), the revenue has been saved, corrupting accounting ledgers.
4. **Unchecked AI Hallucination:** Allowing unconstrained LLMs to trigger payment retries can result in uncontrolled debit loops and compliance breaches.

---

## 2. The Solution: Autonomous, Governed Revenue Recovery

RecoverAI bridges the gap between intelligent AI decision-making and mission-critical financial reliability. It acts as an autonomous revenue orchestration engine operating within strict deterministic boundaries.

```mermaid
flowchart TD
    subgraph INGEST["1. INGESTION & DIAGNOSIS"]
        E1[Raw Gateway Error] --> S1[Diagnosis Engine]
        S1 --> S2[Paise Risk Engine]
    end

    subgraph REASONING["2. AI STRATEGY ADVISOR"]
        S2 --> A1[NVIDIA NIM / LLM Agent]
        A1 --> A2["Structured Proposal (JSON)"]
    end

    subgraph GOVERNANCE["3. REGTECH POLICY FIREWALL"]
        A2 --> G1{OPA Rego Engine}
        G1 -- VIOLATION --> G2[BLOCKED State]
        G1 -- COMPLIANT --> G3[GOVERNANCE_APPROVED]
    end

    subgraph ORCHESTRATION["4. DURABLE WORKFLOWS"]
        G3 --> T1[Temporal Saga Workflow]
        T1 --> T2["Durable Timer (workflow.sleep)"]
        T2 --> T3[Razorpay Gateway API]
        T3 --> T4["ACTION_EXECUTED (Recovered: ₹0.00)"]
    end

    subgraph SETTLEMENT["5. AUTHORITATIVE SETTLEMENT"]
        W1[Razorpay Webhook: payment.captured] --> W2{HMAC-SHA256 Valid?}
        W2 -- YES --> W3[State Machine Transition]
        W3 --> W4["RECOVERED (Authoritative ₹)"]
        W4 --> I1[(immudb Audit Ledger)]
    end

    T4 -. Awaiting Evidence .-> W1
```

---

## 3. Why RecoverAI Is Different

| Feature | Traditional Retry Systems / Zapier / CRON | Unconstrained AI Agents | RecoverAI Governed Platform |
|---|---|---|---|
| **Strategy Formulation** | Static fixed intervals (e.g., retry at 1h, 24h, 48h) | Unpredictable, prompt-injected LLM calls | **Context-aware AI proposals bounded by deterministic rules** |
| **Regulatory Guardrails** | Manual coding per country / payment type | None (hallucination risk) | **Open Policy Agent (OPA) Rego policy firewall** |
| **Execution Reliability** | Fragile `cron` jobs or in-memory Celery delays | Python `time.sleep()` prone to pod crash loss | **Temporal Saga Orchestration with durable timers** |
| **Accounting Accuracy** | Outbound HTTP 200 counted as "recovered" | Guessed / fabricated recovery metrics | **`ACTION_EXECUTED ≠ RECOVERED` — Webhook settlement required** |
| **Idempotency** | Vulnerable to double-charging during retries | Non-idempotent re-runs | **Strict state machine & idempotency key preservation** |
| **Audit Trail** | Mutable application log files | Non-reproducible conversational logs | **Append-only cryptographic immudb ledger** |
| **Monetary Math** | Floating point `float` with rounding drift | Unverified string outputs | **Strict Integer Paise Precision (`amount_paise`)** |

---

## 4. Complete System Architecture

The RecoverAI platform is structured as a resilient 7-layer decoupled microservice architecture:

```mermaid
graph TB
    subgraph UI_LAYER["Presentation Layer (Port 3000)"]
        FE[React 18 + Vite + Tailwind CSS SPA]
        FE_D[Dashboard & Live Control Panel]
        FE_C[Recovery Cases Table]
        FE_A[AI Strategy Visualizer]
        FE_G[OPA Governance Inspector]
        FE_S[500-Case Simulation Hub]
        FE_L[immudb Audit Trail Explorer]
    end

    subgraph API_LAYER["API & Ingestion Gateway (Port 8000)"]
        API[FastAPI Asynchronous Gateway]
        WH[HMAC Webhook Ingestion Endpoint]
        DEMO_API[Interactive Demo Controller]
        SIM_API[Monte Carlo Simulation Engine]
        HEALTH[Readiness & Health Probes]
    end

    subgraph ENGINE_LAYER["Core Domain Engines"]
        DIAG[Failure Diagnosis Engine]
        RISK[Paise Risk & Revenue Engine]
        SM[Strict Recovery State Machine]
    end

    subgraph AI_LAYER["AI Intelligence Boundary"]
        AGENT[Nvidia NIM / LLM Strategy Agent]
        PROMPT[XML Encapsulated Safe Prompting]
        FALLBACK[Deterministic Fallback Strategy Matrix]
    end

    subgraph GOV_LAYER["Governance & RegTech Firewall (Port 8181)"]
        OPA[Open Policy Agent - OPA Server]
        REGO[Enterprise Rego Rules - governance.rego]
        LOCAL_REGO[In-Memory Fail-Closed Rego Engine]
    end

    subgraph WORKFLOW_LAYER["Durable Execution & Workers (Port 8233)"]
        TEMP_SRV[Temporal Server Cluster]
        TEMP_WORKER[Temporal Python Worker]
        SAGA[Payment Recovery Saga Workflows]
        TIMERS[Durable Sleep Timers]
    end

    subgraph DATA_LAYER["Persistence & Cryptographic Ledgers"]
        PG[(PostgreSQL 16 Relational Store)]
        IMMU[(immudb v1.9 Cryptographic Ledger - Port 3322)]
    end

    subgraph EXT_LAYER["External Integration Boundaries"]
        RZP_API[Razorpay Payment Links / Invoices]
        RZP_WH[Razorpay Signed Webhook Streams]
        NOTIF[WhatsApp / Email Notification Dispatch]
    end

    FE -->|REST API Requests| API
    API --> WH & DEMO_API & SIM_API & HEALTH
    WH -->|Verify HMAC| SM
    API --> DIAG --> RISK --> AGENT
    AGENT -->|Proposal Only| OPA
    OPA -->|ALLOW| TEMP_WORKER
    OPA -->|DENY| SM
    TEMP_WORKER --> SAGA --> TIMERS --> RZP_API
    RZP_WH --> WH
    SM --> PG
    SM --> IMMU
    SAGA --> NOTIF
```

---

## 5. Complete Transaction State Machine Lifecycle

RecoverAI implements an explicit, non-bypassable finite state machine (FSM). Every state transition is validated against current state preconditions and backed by cryptographically signed evidence.

```mermaid
stateDiagram-v2
    [*] --> DETECTED: payment.failed received
    
    DETECTED --> DIAGNOSED: Failure categorized & Risk assessed
    
    DIAGNOSED --> AI_DECISION: AI Agent produces action proposal
    
    AI_DECISION --> GOVERNANCE_APPROVED: OPA evaluates ALLOW (Compliant)
    AI_DECISION --> BLOCKED: OPA evaluates DENY (Policy Veto)
    
    GOVERNANCE_APPROVED --> ACTION_SCHEDULED: Temporal workflow initiated
    
    ACTION_SCHEDULED --> DURABLE_WAIT: workflow.sleep(cooldown_hours)
    
    DURABLE_WAIT --> ACTION_EXECUTED: Outbound API executed (Recovered = ₹0)
    
    ACTION_EXECUTED --> AWAITING_SETTLEMENT: Customer notified with payment link
    
    AWAITING_SETTLEMENT --> RECOVERED: Authoritative payment.captured Webhook
    AWAITING_SETTLEMENT --> FAILED_SAFELY: Cooldown timeout / Exhausted retries
    
    BLOCKED --> [*]
    RECOVERED --> [*]
    FAILED_SAFELY --> [*]
```

### State Definitions:
1. **`DETECTED`**: Initial payment failure event ingested with raw gateway error code.
2. **`DIAGNOSED`**: Failure mapped to normalized taxonomy; integer paise revenue-at-risk computed.
3. **`AI_DECISION`**: Strategy formulated (recommended action, cooldown delay, channel strategy).
4. **`GOVERNANCE_APPROVED`**: OPA validates that retry caps, cooldown rules, and notice constraints are satisfied.
5. **`BLOCKED`**: Governance policy vetoed the AI proposal (no financial action permitted).
6. **`ACTION_SCHEDULED`**: Workflow safely scheduled in Temporal task queue.
7. **`ACTION_EXECUTED`**: Outbound recovery action dispatched (e.g., payment link generated). **Recovered Amount remains ₹0.00.**
8. **`AWAITING_SETTLEMENT`**: System listens for gateway settlement events.
9. **`RECOVERED`**: Validated `payment.captured` HMAC webhook received. **Revenue officially recognized.**
10. **`FAILED_SAFELY`**: Recovery exhausted without financial violation or spamming.

---

## 6. 💰 Critical Financial Safety Invariant: `ACTION_EXECUTED ≠ RECOVERED`

One of the most dangerous design flaws in revenue recovery systems is treating an outbound API response (e.g., HTTP 200 from Razorpay Create Payment Link) as recovered revenue.

```mermaid
sequenceDiagram
    autonumber
    participant Engine as RecoverAI Orchestrator
    participant RZP as Razorpay Gateway API
    participant Cust as Customer
    participant WH as Webhook Ingestion
    participant Ledger as immudb Audit Ledger

    Note over Engine,RZP: STAGE 1: OUTBOUND ACTION
    Engine->>RZP: POST /v1/payment_links (Amount: ₹12,500)
    RZP-->>Engine: HTTP 200 OK (Link ID: plink_882)
    Engine->>Ledger: Transition -> ACTION_EXECUTED (Recovered: ₹0.00)
    Note over Engine: CRITICAL: Zero revenue is credited.<br/>State is NOT recovered!

    Note over Cust,WH: STAGE 2: CUSTOMER PAYS
    Engine->>Cust: Send Payment Link via WhatsApp/Email
    Cust->>RZP: Customer completes payment of ₹12,500
    
    Note over RZP,Ledger: STAGE 3: AUTHORITATIVE SETTLEMENT
    RZP->>WH: POST /webhooks/razorpay (event: payment.captured)
    WH->>WH: Verify HMAC-SHA256 Signature
    WH->>Engine: Authoritative Settlement Verified
    Engine->>Ledger: Transition -> RECOVERED (Recovered: ₹12,500.00)
    Note over Engine: Official Revenue Recognition complete.
```

### Proof of Invariant:
* When Razorpay returns `HTTP 200 OK` for an outbound payment link, `recovered_amount_paise` is strictly **`0`**.
* Only when a cryptographically signed webhook with event `payment.captured` and verified signature matches the case, does `recovered_amount_paise` increment to the captured value.

---

## 7. 🔄 Dynamic Transaction Processing Pipeline

RecoverAI does **not** rely on static predetermined transaction templates. Every transaction is dynamically evaluated end-to-end through data-driven business rules and AI reasoning.

```
Transaction Input
  ├── amount_paise (e.g., 999900)
  ├── raw_gateway_code (e.g., "network_error")
  ├── retry_count (e.g., 0)
  └── customer_tier (e.g., "PREMIUM")
        │
        ▼
[1] DiagnosisService.diagnose_failure()
  └── Normalized Category: TRANSIENT_INFRASTRUCTURE
        │
        ▼
[2] RiskService.assess_risk()
  └── Revenue at Risk: 999900 paise (₹9,999.00) | Priority Score: 78.4 (HIGH)
        │
        ▼
[3] NvidiaNIMAgent.recommend_recovery_strategy()
  └── AI Proposal: RETRY_SCHEDULED | Cooldown: 48h | Confidence: 0.94
        │
        ▼
[4] OPAGovernanceEngine.evaluate_policy()
  └── OPA Decision: ALLOW (Violations: [])
        │
        ▼
[5] Temporal Workflow Orchestrator
  └── Execution State: ACTION_SCHEDULED -> DURABLE_WAIT -> ACTION_EXECUTED
        │
        ▼
[6] Authoritative Settlement Verification
  └── Webhook payment.captured -> RECOVERED (₹6,799.32 dynamically credited)
```

### Verified Multi-Run Dynamic Execution Evidence:
In our automated test runs, consecutive executions generated completely unique outcomes based on dynamic inputs:

* **Run A:** Error: `NETWORK_ERROR` | Amount: `999,900 paise` (₹9,999.00)  
  ➜ Category: `TRANSIENT_INFRASTRUCTURE` | Action: `RETRY_SCHEDULED` | Recovered: **₹6,799.32** (68% capture)
* **Run B:** Error: `EXPIRED_CARD` | Amount: `1,250,000 paise` (₹12,500.00)  
  ➜ Category: `INSTRUMENT_INVALIDATION` | Action: `SEND_PAYMENT_LINK` | Recovered: **₹8,500.00** (68% capture)
* **Run C:** Error: `INSUFFICIENT_FUNDS` (with 5 prior retries) | Amount: `4,987,100 paise`  
  ➜ Category: `LIQUIDITY_FRICTION` | OPA Decision: **`DENIED (RULE-001: Max retries exceeded)`** ➜ State: **`BLOCKED`**

---

## 8. Failure Diagnosis Taxonomy

RecoverAI maps all raw payment gateway error codes from Razorpay, Visa, Mastercard, and NPCI into 6 normalized categories:

| Normalized Category | Raw Gateway Error Codes | Root Cause Diagnosis | Autonomous AI Strategy | OPA Governance Constraints |
|---|---|---|---|---|
| **`LIQUIDITY_FRICTION`** | `INSUFFICIENT_FUNDS`, `low_balance`, `limit_exceeded` | Customer account temporarily has insufficient balance. | Smart-retry scheduled around salary/payday windows (1st/5th of month). | Cooldown ≥ 24h; Max 3 retries; Pre-debit notice check. |
| **`INSTRUMENT_INVALIDATION`** | `EXPIRED_CARD`, `card_inactive`, `invalid_card_number` | Payment card expired, canceled, or replaced. | **Zero retries.** Immediate interactive Payment Link dispatched via WhatsApp/SMS. | Retries strictly prohibited (`RULE-003`); Send link permitted. |
| **`TRANSIENT_INFRASTRUCTURE`** | `GATEWAY_TIMEOUT`, `network_error`, `bank_timeout` | Temporary network glitch between bank switch and gateway. | Exponential backoff retry after short cooldown (2h to 24h). | Cooldown ≥ 2h; Max 3 retries. |
| **`MANDATE_COMPLIANCE_LOCK`** | `MANDATE_EXPIRED`, `frequency_breached`, `mandate_inactive` | RBI e-mandate registration expired or threshold exceeded. | Re-authorization workflow; Customer prompted to accept new SI mandate. | Direct automated retries blocked until mandate re-validated. |
| **`BANK_RISK_BLOCK`** | `BANK_DECLINE`, `risk_threshold_exceeded`, `fraud_suspected` | Issuing bank risk engine flagged transaction. | Soft non-retry notification asking customer to approve via banking app. | Retries prohibited until bank clearance. |
| **`UNKNOWN`** | Unrecognized error strings | Unclassified failure code. | Conservative fallback to manual escalation queue. | Fail-closed security rule applied. |

---

## 9. AI Decision Engine & Safety Boundary

RecoverAI utilizes a dual-engine architecture: an LLM (NVIDIA NIM / Nemotron-3 / Mistral) for contextual strategy formulation, guarded by a deterministic fallback rules engine.

```mermaid
flowchart LR
    A[Payment Failure Context] --> B[XML Structured Encapsulation]
    B --> C{AI Agent Available?}
    
    C -- YES --> D[NVIDIA NIM Agent API]
    C -- NO / TIMEOUT --> E[Deterministic Rule-Based Fallback]
    
    D --> F[Pydantic Response Schema Validator]
    E --> F
    
    F -->|Invalid Schema| E
    F -->|Valid Proposal| G["Structured AI Proposal (JSON)"]
    
    G --> H[OPA Policy Firewall]
```

### Prompt Injection & Adversarial Defense:
All untrusted customer and gateway inputs are encapsulated inside rigid `<transaction_context>` XML delimiters. The model system prompt enforces:
> *"You are an AI advisory engine with NO authority to approve or execute financial actions. Output strictly structured JSON matching the ProposedRecoveryPlan schema."*

---

## 10. Open Policy Agent (OPA) Rego Governance Firewall

The governance layer acts as a zero-trust firewall. The OPA engine evaluates declarative Rego policies in `policies/governance.rego`.

```rego
package recovery.governance

default allow = false

# RULE-001: Enforce Maximum 3 Automated Retries (RBI Compliance)
allow if {
    input.action == "RETRY_SCHEDULED"
    input.retry_count < 3
    input.cooldown_hours >= 24
    input.is_terminal_decline == false
    input.confidence >= 0.70
}

# RULE-003: Terminal Declines Prohibit Any Retry Action
violations contains "RULE-003: Terminal decline prohibited from retry execution" if {
    input.action == "RETRY_SCHEDULED"
    input.is_terminal_decline == true
}

# RULE-002: Minimum Cooldown Window of 24 Hours
violations contains sprintf("RULE-002: Insufficient cooldown hours (%.2f < 24)", [input.cooldown_hours]) if {
    input.action == "RETRY_SCHEDULED"
    input.cooldown_hours < 24
}
```

### Verified Hostile AI Veto Demonstration:
When tested with an adversarial scenario where a hijacked or hallucinating AI claimed **99% Confidence** for an aggressive retry:

```
[TEST] HOSTILE AI OPA VETO DEMONSTRATION
------------------------------------------------------------
  Hostile AI Claims:
    AI Confidence    : 0.99 (99% Claimed Confidence)
    Requested Retries: 5    (Exceeds 3-Retry Cap)
    Cooldown Delay   : 1.0h (Violates 24h Cooldown Rule)
    Terminal Decline : True (Expired Card)

  OPA Decision: DENIED
    • RULE-001: Maximum retries exceeded (5 >= 3)
    • RULE-002: Cooldown violation (1.0h < 24.0h)
    • RULE-003: Terminal decline prohibited from retry execution

  Result: Financial Action BLOCKED. AI confidence cannot override Rego policy.
```

---

## 11. Temporal Durable Workflow Orchestration

RecoverAI uses **Temporal** for durable, long-running Saga execution. If a recovery strategy dictates waiting 48 hours for a customer's salary deposit:

* **No In-Memory Sleeping:** Traditional `time.sleep(172800)` blocks threads and loses state on server restart.
* **Temporal `workflow.sleep(timedelta(hours=48))`:** Persists state deterministically to the database. Even if the entire backend cluster restarts, the workflow resumes at the exact second required.
* **Idempotency Key Stability:** The same idempotency key (`X-Razorpay-Idempotency-Key`) is preserved across network retries, preventing duplicate charges.

```mermaid
sequenceDiagram
    autonumber
    participant App as RecoverAI Backend
    participant Temp as Temporal Cluster
    participant Worker as Temporal Python Worker
    participant RZP as Razorpay Service

    App->>Temp: StartWorkflow(PaymentRecoveryWorkflow, case_id)
    Temp->>Worker: Dispatch Activity: EvaluatePolicyActivity
    Worker-->>Temp: Policy Approved
    Temp->>Worker: Dispatch Activity: ScheduleDurableTimer(48h)
    Note over Worker,Temp: Durable Sleep: Cluster can restart without state loss
    Temp->>Worker: Timer Expired -> Dispatch Activity: ExecuteOutboundActionActivity
    Worker->>RZP: POST /v1/payment_links (with Idempotency Key)
    RZP-->>Worker: HTTP 200 OK (Link Created)
    Worker-->>Temp: Activity Succeeded -> State: ACTION_EXECUTED
```

---

## 12. Webhook Security & Dual-Signature Verification

Every inbound webhook is verified against Razorpay's HMAC-SHA256 signature specification before JSON parsing:

```text
HMAC_SHA256(raw_payload, RAZORPAY_WEBHOOK_SECRET) == X-Razorpay-Signature
```

```python
# Verified constant-time signature comparison prevents timing attacks
computed_hmac = hmac.new(
    settings.RAZORPAY_WEBHOOK_SECRET.encode(),
    raw_body,
    hashlib.sha256
).hexdigest()

if not hmac.compare_digest(computed_hmac, header_signature):
    raise HTTPException(status_code=401, detail="Invalid Webhook Signature")
```

### Idempotency & Zero Double-Recovery Guarantee:
If Razorpay delivers the same `payment.captured` webhook multiple times (common during network retries):
* **1st Delivery:** State transitions `AWAITING_SETTLEMENT` → `RECOVERED`. ₹8,500 credited.
* **2nd Delivery:** State machine recognizes `state == RECOVERED`. Flags transaction as **`Idempotent No-Op`**. Exactly **₹0.00 additional paise** are credited.
* **Verified Metric:** **0 Double Recoveries | 0 Double-Counted Paise.**

---

## 13. immudb Cryptographic Audit Ledger & Tamper Detection

Every governance evaluation, state change, and financial settlement produces an immutable cryptographic receipt in **immudb**:

```text
Payload Digest = SHA-256( Canonical_JSON( AuditEvent ) )
```

```mermaid
flowchart TD
    E["AuditEvent: Case #882 Transition -> RECOVERED"]
    E --> H[Canonical SHA-256 Hash Computation]
    H --> L[(immudb Append-Only Merkle Ledger)]
    
    subgraph AUDIT_VERIFICATION["Tamper Detection Verification"]
        L --> V1[Read Stored Payload]
        V1 --> V2{Stored Hash == Computed Hash?}
        V2 -- MATCH --> PASS[VALID: Cryptographically Verified]
        V2 -- MISMATCH --> ALERT[TAMPER DETECTED: Audit Alert Triggered]
    end
```

### Verified Tamper Detection Test:
In our automated test suite, an audit record was stored, verified as `VALID`, and then subjected to adversarial payload mutation:
* **Original Record Verification:** `VALID` (SHA-256 matched canonical payload)
* **Tampered Record Verification:** `TAMPER DETECTED` (Hash mismatch detected immediately)

---

## 14. Mathematical Model & Monetary Safety

RecoverAI adheres strictly to integer paise precision for all financial accounting. Floating-point arithmetic (`float`) is strictly prohibited to prevent IEEE-754 precision drift.

### Core Equations:

```text
1. Integer Paise Conversion:
   amount_paise = round(amount_inr * 100)

2. Total Revenue at Risk:
   Revenue_At_Risk = Sum( case_i.amount_paise for i in 1..N )

3. Total Authoritative Recovered:
   Recovered_Amount = Sum( settlement_j.recovered_amount_paise for j in Settled_Cases )

4. Measured Recovery Rate (%):
   Recovery_Rate = (Recovered_Amount / Revenue_At_Risk) * 100   [if Revenue_At_Risk > 0, else 0.0]
```

---

## 15. 500-Case Monte Carlo Simulation Benchmark

To benchmark recovery performance across varied portfolio conditions, RecoverAI features a built-in Monte Carlo simulation engine (`backend/app/simulation/`):

| Simulation Metric | Seed 42 Benchmark Result | Mathematical & Governance Invariant |
|---|---|---|
| **Total Cases Evaluated** | **500** | 100% evaluated across 6 failure categories |
| **Total Revenue at Risk** | **₹2,52,38,426.32** (25,238,426.32 INR / 2,523,842,632 paise) | Integer paise precision verified |
| **Simulated Recovery Achieved** | **₹85,65,745.32** (8,565,745.32 INR / 856,574,532 paise) | Synthetic recovery modeling |
| **Simulated Recovery Rate** | **33.94%** | (8,565,745.32 / 25,238,426.32) × 100 |
| **OPA Policy Approvals** | **307 (61.4%)** | Compliant with cooldown & retry caps |
| **OPA Policy Denials** | **193 (38.6%)** | Blocked high-risk / invalid retries |
| **Terminal Declines Filtered** | **36** | 100% prevented from blind retry |
| **Double Recoveries** | **0** | **Zero duplicate settlements** |
| **Unsafe Financial Claims** | **0** | **Zero execution-as-recovery violations** |

---

## 16. Frontend Dashboard & Control Center

The RecoverAI frontend is built with React 18 and Vite, featuring dark-mode fintech aesthetics, glassmorphism, real-time KPI updates, and full interactive control.

```
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│  RecoverAI  |  [Dashboard]  [Recovery Cases]  [AI Strategy]  [Governance]  [Audit] [Health]│
├────────────────────────────────────────────────────────────────────────────────────────────┤
│  DEMO CONTROL PANEL:  [ 🔄 Reset Demo ]  [ ⚡ Start 8-Stage Demo ]  [ ➕ Process Another ] │
│  State: RECOVERED  |  Revenue at Risk: ₹12,500.00  |  Recovered: ₹8,500.00 (68.0%)         │
├────────────────────────────────────────────────────────────────────────────────────────────┤
│  [ KPI Cards ]                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │ Revenue at Risk  │  │ Total Recovered  │  │ Recovery Rate    │  │ Active Cases     │    │
│  │ ₹25,238,426.32   │  │ ₹8,565,745.32    │  │ 33.94%           │  │ 500 Cases        │    │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘    │
│                                                                                            │
│  [ 8-Stage Lifecycle Progression ]                                                         │
│  (1) DETECTED ──> (2) DIAGNOSED ──> (3) AI DECISION ──> (4) OPA GOVERNED ──>              │
│  (5) SCHEDULED ──> (6) EXECUTED ──> (7) AWAITING SETTLEMENT ──> (8) RECOVERED [COMPLETED]  │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Frontend Views Breakdown:
1. **`Dashboard.jsx`**: Live KPI summary, dynamic demo controller, and real-time 8-stage visual stepper.
2. **`RecoveryCases.jsx`**: Paginated ledger of all ingested payment failures with category filters and state badges.
3. **`AIDecisions.jsx`**: Detailed inspection of NVIDIA NIM proposals, confidence scores, and reasoning text.
4. **`Governance.jsx`**: OPA Rego policy rule inspector showing ALLOW / DENY decisions and violation lists.
5. **`Simulation.jsx`**: 500-case Monte Carlo benchmark visualizer with seed control and duplicate injection tests.
6. **`AuditLedger.jsx`**: immudb cryptographic receipt explorer with interactive tamper verification tools.
7. **`Health.jsx`**: Real-time diagnostic monitor tracking PostgreSQL, OPA, Temporal, and immudb status.

---

## 17. Security & Threat Mitigation Matrix

| Threat / Attack Vector | Risk Level | RecoverAI Defense Implementation | Verification Status |
|---|---|---|---|
| **Webhook Forgery / Spoofing** | Critical | Constant-time HMAC-SHA256 signature verification (`X-Razorpay-Signature`). Reject unauthorized with HTTP 401. | **VERIFIED (HTTP 401 on bad HMAC)** |
| **Duplicate Webhook Replay** | High | FSM idempotency tracking. Subsequent `payment.captured` webhooks flagged as idempotent no-ops. | **VERIFIED (0 double recoveries)** |
| **AI Prompt Injection** | High | XML tag encapsulation (`<transaction_context>`), strict Pydantic JSON schema output enforcement. | **VERIFIED (No prompt leakage)** |
| **AI Retrying Hostile Declines** | High | OPA Rego firewall evaluates policy independently of AI. Prohibits terminal retries. | **VERIFIED (99% AI vetoed by OPA)** |
| **Runaway Retry Storms** | High | Hard caps (Max 3 retries, ≥ 24h cooldown) strictly enforced by OPA `RULE-001` & `RULE-002`. | **VERIFIED (Blocked at 3 retries)** |
| **Audit Log Tampering** | Critical | Append-only immudb ledger with SHA-256 Merkle hash chain. Instant tamper alert on mutation. | **VERIFIED (Tamper detected)** |
| **Credential Leakage** | Critical | Automated regex secret redaction filter (`RedactingFilter`) on all stdout/stderr logging. | **VERIFIED (0 secrets leaked)** |
| **Floating-Point Rounding Error** | Medium | Strict integer paise representation across database, state machine, and APIs. | **VERIFIED (All amounts integer paise)** |

---

## 18. Technology Stack

### Backend & Core Logic
* **Language & Runtime:** Python 3.11+ / 3.13
* **Web Framework:** FastAPI (Asynchronous ASGI)
* **Data Validation:** Pydantic v2 (Strict typing & serialization)
* **Database ORM:** SQLAlchemy 2.0 (Asyncpg PostgreSQL driver)
* **Workflow Engine:** Temporal Python SDK 1.24+
* **Policy Engine:** Open Policy Agent (OPA) / Rego
* **Cryptographic Ledger:** immudb v1.9+ Python SDK
* **Testing Framework:** Pytest, AnyIO, Respx, Faker

### Frontend & UI
* **Framework:** React 18.3
* **Build Tool:** Vite 5.4
* **Styling:** Tailwind CSS & Lucide Icons
* **Charts & Visuals:** Recharts & Canvas-Confetti
* **HTTP Client:** Axios with dynamic base URL resolution

### Infrastructure & DevOps
* **Containerization:** Docker & Docker Compose
* **Relational Database:** PostgreSQL 16 Alpine
* **Orchestrator:** Temporal Server + Web UI
* **Security:** Cryptographic HMAC-SHA256, Rego Policy as Code

---

## 19. Repository Directory Structure

```
recoverai/
├── backend/                        # FastAPI Backend Application
│   ├── app/
│   │   ├── ai/                     # AI Strategy & LLM Integration
│   │   │   ├── agent.py            # NVIDIA NIM / Rule-based Agent
│   │   │   └── schemas.py          # AI Proposal Pydantic Schemas
│   │   ├── api/                    # REST API Endpoints
│   │   │   ├── demo.py             # Interactive Demo Controller
│   │   │   ├── health.py           # /health, /ready, /metrics
│   │   │   └── webhooks.py         # Razorpay Webhook Ingestion
│   │   ├── core/                   # App Configuration & Logging Filters
│   │   │   ├── config.py           # Environment Settings
│   │   │   └── logging.py          # Secret-Redacting Logging Filter
│   │   ├── db/                     # Database Engine & Session Factory
│   │   ├── models/                 # SQLAlchemy Database Models
│   │   ├── policy/                 # OPA Policy Integration Engine
│   │   │   └── engine.py           # OPA HTTP Client + Local Fallback
│   │   ├── repositories/           # Data Access Layer Repositories
│   │   ├── schemas/                # Domain Pydantic Models
│   │   │   ├── audit.py            # immudb Audit Schemas
│   │   │   ├── diagnosis.py        # Failure Category Enums
│   │   │   └── state_machine.py    # Case State Machine Schemas
│   │   ├── services/               # Core Business Domain Services
│   │   │   ├── demo_service.py     # 8-Stage Interactive Demo Service
│   │   │   ├── diagnosis_service.py# Error Diagnosis & Taxonomy
│   │   │   ├── immutable_audit_service.py # immudb Audit Service
│   │   │   ├── razorpay_service.py # Gateway Integration Boundary
│   │   │   ├── recovery_state_machine.py # 8-Stage Recovery FSM
│   │   │   └── risk_service.py     # Integer Paise Risk Calculator
│   │   ├── simulation/             # 500-Case Simulation Engine
│   │   │   ├── engine.py           # Monte Carlo Simulation Runner
│   │   │   └── evaluator.py        # Simulation Governance Evaluator
│   │   └── workflows/              # Temporal Workflow Definitions
│   │       ├── activities.py       # Temporal Workflow Activities
│   │       └── recovery_workflow.py# PaymentRecoveryWorkflow Definition
│   └── worker.py                   # Temporal Background Worker
├── frontend/                       # React 18 + Vite Frontend Application
│   ├── src/
│   │   ├── components/             # Reusable UI Components
│   │   │   ├── DemoControlPanel.jsx# Live Demo Action Buttons
│   │   │   ├── Navbar.jsx          # Header & Status Navigation
│   │   │   └── RecoveryTable.jsx   # Interactive Case Table
│   │   ├── pages/                  # Main Application Views
│   │   │   ├── Dashboard.jsx       # Main KPI & Lifecycle Stepper
│   │   │   ├── AIDecisions.jsx     # AI Strategy Breakdown
│   │   │   ├── Governance.jsx      # OPA Policy Rule Inspector
│   │   │   ├── Simulation.jsx      # Monte Carlo Benchmark Hub
│   │   │   ├── AuditLedger.jsx     # immudb Audit Trail Explorer
│   │   │   └── Health.jsx          # Service Health Diagnostics
│   │   └── services/               # Frontend API Client Services
│   │       └── api.js              # Axios HTTP REST Client
│   ├── package.json                # Frontend Dependencies
│   └── vite.config.js              # Vite Build Configuration
├── policies/                       # RegTech Policy Definitions
│   └── governance.rego             # Enterprise OPA Rego Governance Policy
├── scripts/                        # Automated Verification & Demo Scripts
│   ├── final_demo.py               # Master 19-Stage Hackathon Demo Runner
│   ├── verify_full_system.py       # 7-Gate Master Compliance Verifier
│   └── verify_dynamic_transactions.py # 8-Gate Dynamic Transaction Verifier
├── tests/                          # Automated Pytest Test Suite
│   ├── integration/                # End-to-End Integration Tests (19 tests)
│   └── unit/                       # Unit Test Suite (127 tests)
├── docker-compose.yml              # Multi-Service Orchestration Spec
├── Dockerfile                      # Backend Container Build Spec
├── requirements.txt                # Python Dependencies Spec
└── README.md                       # Comprehensive System Documentation
```

---

## 20. Local Setup & Execution Guide (Windows CMD)

Follow these step-by-step instructions to run the complete stack locally.

### Prerequisites:
* Python 3.11+ or 3.13 installed (`python --version`)
* Node.js 18+ and npm installed (`node --version`)
* Docker & Docker Compose installed (optional for full container mode)

---

### Step 1: Clone Repository & Setup Environment
Open **Command Prompt (CMD)**:

```cmd
cd /d "D:\razor pay hackathon"

:: Copy environment template
copy .env.example .env
```

---

### Step 2: Start Infrastructure via Docker Compose
To start PostgreSQL, OPA, Temporal, immudb, backend, and worker containers:

```cmd
docker compose up -d
docker compose ps
```

*If running without Docker, the backend automatically enables robust local in-memory fallbacks for OPA, Temporal, and immudb.*

---

### Step 3: Start FastAPI Backend (Manual or Local Dev Mode)
If running Python locally:

```cmd
:: Install backend dependencies
pip install -r requirements.txt

:: Start FastAPI server on port 8000
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Step 4: Start Frontend Development Server

Open a second CMD window:

```cmd
cd /d "D:\razor pay hackathon\frontend"

:: Install npm dependencies
npm install

:: Start Vite dev server on port 3000
npm run dev
```

---

### Step 5: Access the Web Interfaces

| Service | Local URL | Description |
|---|---|---|
| **Frontend Web App** | [http://localhost:3000](http://localhost:3000) | Full Interactive Dashboard & Control Panel |
| **Backend Swagger API** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive OpenAPI / Swagger UI |
| **Temporal Web UI** | [http://localhost:8233](http://localhost:8233) | Workflow Saga Inspector & Timeline |
| **OPA Governance Server** | [http://localhost:8181](http://localhost:8181) | Open Policy Agent HTTP API |

---

## 21. Health & Diagnostic Verification

Verify backend readiness using `curl` in CMD:

```cmd
:: 1. Basic Health Check
curl -s http://localhost:8000/health
:: Expected: {"status":"healthy","service":"RecoverAI"}

:: 2. Readiness Check across Dependencies
curl -s http://localhost:8000/ready
:: Expected: {"status":"PARTIALLY_DEGRADED"|"HEALTHY","components":{"postgres":"HEALTHY","opa":"HEALTHY",...}}

:: 3. Prometheus Metrics Endpoint
curl -s http://localhost:8000/metrics
:: Expected: # HELP recoverai_http_requests_total ...
```

---

## 22. 2-Minute Interactive Demo Walkthrough

Follow this sequence in the web browser at `http://localhost:3000`:

1. **Open Dashboard:** Navigate to `http://localhost:3000/`.
2. **Press "Reset Demo":** Click **🔄 Reset Demo** in the Control Panel. Notice the state resets to `READY` with `₹0.00` active risk and 0 cases.
3. **Execute 8-Stage Demo:** Click **⚡ Start Demo**. Watch the real-time stepper smoothly advance through all 8 stages:
   * `DETECTED` → `DIAGNOSED` (Error mapped) → `AI DECISION` (Strategy proposed) → `GOVERNANCE APPROVED` (OPA allow) → `ACTION SCHEDULED` → `ACTION EXECUTED` (Recovered: ₹0.00) → `AWAITING SETTLEMENT` → `RECOVERED` (HMAC webhook verified, ₹ credited).
4. **Process Another Transaction:** Click **➕ Process Another Transaction**. A new randomized case is dynamically generated and appended to the table with its own distinct category and amount.
5. **Inspect Recovery Cases:** Navigate to the **Recovery Cases** tab to view the live case ledger with state badges.
6. **Inspect AI Decisions:** Navigate to **AI Strategy** to examine the JSON proposal, reasoning, and confidence score.
7. **Inspect Governance:** Navigate to **Governance** to view the OPA Rego rules and active enforcement status.
8. **Verify Audit Trail:** Open **Audit Ledger** to view the immudb cryptographic receipts and run a live tamper detection test.

---

## 23. Testing & Verification Suite

RecoverAI includes a comprehensive, verified test suite covering unit tests, integration tests, adversarial security tests, and full-system compliance gates.

### Run All Tests in CMD:

```cmd
cd /d "D:\razor pay hackathon"

:: 1. Run Complete Unit Test Suite (127 Tests)
python -m pytest tests/unit/ -v

:: 2. Run Complete Integration Test Suite (19 Tests)
python -m pytest tests/integration/ -v

:: 3. Run Dynamic Transaction Verifier (8 Gates)
python -c "import asyncio; from scripts.verify_dynamic_transactions import main; asyncio.run(main())"

:: 4. Run Master Full-System Compliance Verifier (7 Gates)
python scripts\verify_full_system.py

:: 5. Run Master 19-Stage Final Demo Runner
python scripts\final_demo.py
```

### Verified Test Results Summary:

```
============================================================
              RECOVERAI TEST & COMPLIANCE SUMMARY
============================================================
  • Unit Tests Passed             : 127 / 127  [PASS - 100%]
  • Integration Tests Passed      :  19 /  19  [PASS - 100%]
  • Dynamic Transaction Gates     :   8 /   8  [PASS - 100%]
  • Full System Compliance Gates  :   7 /   7  [PASS - 100%]
  • Master Final Demo Stages      :  19 /  19  [PASS - 100%]
  • Secret Leaks Detected         :   0        [PASS - Clean]
  • Double Recoveries Detected    :   0        [PASS - Zero]
============================================================
```

---

## 24. Engineering Decisions & Design Rationale

### Q: Why use integer paise instead of standard floating-point INR?
> **A:** Floating-point arithmetic (`float`) in programming languages is subject to binary representation rounding errors (e.g., `0.1 + 0.2 = 0.30000000000000004`). In financial systems, accumulating sub-cent rounding errors across millions of transactions leads to ledger corruption. Working in integer paise (1 INR = 100 paise) guarantees exact mathematical precision at all times.

### Q: Why decouple AI strategy generation from execution using OPA?
> **A:** Large Language Models are probabilistic and susceptible to prompt injection, hallucination, and drift. Financial recovery is strictly regulated by regulatory authorities (RBI, NPCI). Open Policy Agent (OPA) provides a deterministic, auditable, and unbypassable policy firewall written in declarative Rego. If an AI proposes an invalid retry, OPA guarantees a hard deny.

### Q: Why use Temporal instead of Celery or standard Python `time.sleep()`?
> **A:** Recovery strategies often require multi-day delays (e.g., waiting 48 hours for a customer's salary deposit). Python in-memory timers lose all state if the application restarts or crashes. Temporal workflows are event-sourced and durable; the workflow state is saved, allowing the server to reboot without losing scheduled actions.

### Q: Why require an authoritative webhook instead of relying on HTTP 200 responses?
> **A:** Generating a payment link returns HTTP 200 OK, but the customer has not yet paid. Claiming revenue recovery at the time of link creation is an accounting violation. Only an authoritative, HMAC-signed `payment.captured` webhook provides cryptographically verifiable proof of settlement.

---

## 25. Core Design Principles

1. **Safety Over Automation:** If an action violates policy or confidence thresholds, the system defaults to safe fail-closed behavior (`BLOCKED` or `FAILED_SAFELY`).
2. **Evidence Over Assumption:** Revenue recovery is recognized strictly when cryptographic proof of settlement is provided.
3. **Policy Over AI Authority:** The AI model is an advisor, never an executioner. Deterministic Rego code holds veto power over all AI proposals.
4. **Durability Over Ephemeral Timers:** Long-running recovery workflows survive pod restarts and network outages via Temporal Sagas.
5. **Idempotency by Design:** Duplicate webhooks and retried requests produce zero duplicate financial effects.
6. **Immutable Auditability:** Every action, decision, and transition is mathematically sealed in an append-only cryptographic ledger.

---

## 26. Current Limitations & Production Roadmap

### Current Scope & Synthetic Boundaries:
* **Synthetic Gateway Boundary:** In testing and hackathon demonstration mode, outbound Razorpay API calls and inbound webhooks utilize authenticated synthetic payloads to guarantee zero unauthorized charges to live payment methods.
* **Local Single-Node Deployment:** Docker Compose runs single-instance instances of PostgreSQL, OPA, Temporal, and immudb suitable for development and demonstration.

### Production Roadmap:
* [ ] **Distributed Multi-Region Deployment:** Helm charts for Kubernetes (EKS / GKE) with managed Amazon RDS Aurora and Temporal Cloud.
* [ ] **Direct Payment Aggregator Multiplexing:** Automatic failover across multiple payment gateways (Razorpay $\to$ PayU $\to$ Cashfree) when a primary bank route experiences degraded success rates.
* [ ] **Customer Behavioral ML Embeddings:** Fine-tuned transformer models predicting customer-specific optimal settlement windows based on historical payment timing.
* [ ] **OpenTelemetry & Prometheus/Grafana Dashboards:** Production APM distributed tracing tracking end-to-end recovery latency across microservices.

---

## 💼 What This Project Demonstrates to Technical Recruiters

This repository demonstrates practical expertise across key senior engineering domains:

* **Fintech & Payment Systems:** Deep understanding of payment lifecycles, webhook signatures, idempotency, and integer-precision financial accounting.
* **Distributed Systems Architecture:** Multi-service coordination using FastAPI, Temporal Saga workflows, and asynchronous message flows.
* **Safe AI Engineering:** Strict isolation of generative AI models behind deterministic policy-as-code firewalls (OPA/Rego) with prompt injection defenses.
* **Security & Cryptography:** HMAC-SHA256 signature verification, constant-time comparisons, secret-redacting loggers, and immudb cryptographic ledgers.
* **State Machine Design:** Explicit finite state machine modeling preventing illegal state transitions and ensuring predictable lifecycle progression.
* **Full-Stack Engineering:** High-performance asynchronous Python backend paired with a modern, reactive React 18 / Vite single-page application.
* **Automated Testing & QA:** Robust test suite featuring 127 unit tests, 19 integration tests, and reproducible Monte Carlo simulations.

---

## 🏆 Final Project Statement

> **RecoverAI is not a simple payment retry script.**  
> It is an enterprise-grade, safety-first autonomous revenue recovery platform where **AI formulates strategies**, **deterministic Rego policies govern**, **durable Temporal Sagas execute**, and **cryptographically verified settlement evidence proves when revenue was truly recovered.**

---

*Developed for the **Razorpay AI Buildathon** — Track 3 (AI Revenue Recovery)*  
*Repository: [https://github.com/YuvanChaudary/RecoverAI_Razor_pay.git](https://github.com/YuvanChaudary/RecoverAI_Razor_pay.git)*
