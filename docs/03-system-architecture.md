# System Architecture: AI Revenue Recovery Agent
**Project:** Razorpay AI Buildathon (Track 3)  
**Document ID:** `docs/03-system-architecture.md`  
**Status:** Approved Architectural Baseline  

---

## Executive Summary

The **AI Revenue Recovery Agent** is structured as an enterprise-grade, event-driven microservices architecture. Designed for sub-second webhook ingestion, deterministic error diagnosis, zero-trust AI reasoning, hard OPA policy governance, durable workflow execution via Temporal, and cryptographic audit ledgering, the system delivers high availability, zero compliance breaches, and predictable scaling under extreme transaction volumes.

---

## 1. Architectural Principles

Our system architecture is governed by four non-negotiable enterprise tenets:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        ARCHITECTURAL TENETS                              │
├──────────────────────────────────────────────────────────────────────────┤
│ 1. Event-Driven Ingestion   : Asynchronous webhook stream processing     │
│ 2. Decoupled Saga Execution : State-machine isolation via Temporal.io    │
│ 3. Zero-Trust AI Boundary   : LLM output is untrusted until OPA verification│
│ 4. Immutable Auditability   : Append-only cryptographic ledger (immudb)│
└──────────────────────────────────────────────────────────────────────────┘
```

1. **Event-Driven Asynchrony:** System components communicate asynchronously via streaming queues, eliminating blocking HTTP loops and guaranteeing immediate $< 50\text{ms}$ webhook receipt confirmation to Razorpay servers.
2. **Decoupled Saga Orchestration:** Long-running recovery workflows (spanning hours to days to align with bank settlement windows and pre-debit notice periods) are orchestrated using Temporal sagas, preventing state loss across process restarts.
3. **Zero-Trust AI Guardrails:** All generative AI outputs (dunning messages, proposed retry timings, discount offers) are treated as untrusted user input. No AI action can execute without explicit, deterministic approval from an isolated Open Policy Agent (OPA) policy engine.
4. **Cryptographic Auditability:** Operational state changes and policy evaluation decisions are written to both a high-speed transactional database (PostgreSQL) and a tamper-evident cryptographic ledger (`immudb`).

---

## 2. End-to-End System Architecture

The following diagram illustrates the complete data flow from Razorpay Webhook emission through diagnostic evaluation, OPA governance, execution, storage, and dashboard presentation:

```mermaid
graph TD
    subgraph External_Ingress["1. Ingress & Delivery"]
        RP["Razorpay Webhooks"] -->|HTTP POST + HMAC SHA256| FAL["FastAPI Webhook Listener"]
        FAL -->|Validate HMAC| EQ["Event Queue (Redpanda/Kafka)"]
    end

    subgraph Orchestration_Layer["2. Durable Orchestration"]
        EQ -->|Consume Event| TO["Temporal Orchestrator"]
        TO -->|Start Saga Workflow| RW["Recovery Worker"]
    end

    subgraph Intelligence_Layer["3. Intelligence Engine"]
        RW -->|Raw Decline Telemetry| DE["Diagnosis Engine (Deterministic)"]
        DE -->|Mapped Category| RRE["Revenue Risk Engine"]
        RRE -->|Quantified Risk + Context| LLM["LLM Decision Agent (Claude/OpenAI)"]
        LLM <-->|Telemetry & Tracing| LF["Langfuse Observability"]
        LLM -->|Proposed Recovery Plan| OPA["OPA Governance Gate"]
    end

    subgraph Governance_Layer["4. Policy & Governance Boundary"]
        OPA -->|Evaluate RBI & Merchant Rules| POL{"Policy Decision"}
        POL -->|deny| FALL["Fallback / Abort Workflow"]
        POL -->|allow| EXD["Action Dispatcher"]
    end

    subgraph Execution_Layer["5. Bounded Execution"]
        EXD -->|Automated Retries / Links| RPAI["Razorpay APIs"]
        EXD -->|Multi-Channel Dunning| NOVU["Novu Notification Engine"]
    end

    subgraph Storage_Layer["6. Storage & Cryptographic Ledger"]
        EXD -->|Operational State| PG[("PostgreSQL DB")]
        EXD -->|Audit Receipt & OPA Token| IMMU[("immudb Cryptographic Ledger")]
    end

    subgraph Presentation_Layer["7. User Interface"]
        PG -->|Read State $O(1)$| DASH["React + Vite Finance Dashboard"]
        IMMU -->|Verify Cryptographic Proofs| DASH
    end
```

---

## 3. Component Breakdown (The 7 Architectural Layers)

### 3.1 Layer 1: Ingestion Layer
* **FastAPI Webhook Listener:** Lightweight, high-throughput Python API service running Uvicorn workers. Responds immediately with `HTTP 200 OK` to incoming Razorpay webhooks.
* **HMAC Signature Validation:** Intercepts payload headers, verifies the `X-Razorpay-Signature` against the merchant's secret key using SHA256 HMAC before processing.
* **Event Queue (Redpanda / Kafka):** Decouples ingress from processing. Stores raw event streams to handle burst traffic during flash sales or mass billing events without dropping events.

### 3.2 Layer 2: Orchestration Layer
* **Temporal.io Workflow Engine:** Manages the durable state of recovery sagas. Replaces fragile, stateless cron jobs with persistent state machines that can sleep for hours (e.g., waiting out a 24-hour RBI pre-debit notice window or bank CBS downtime) and resume reliably.
* **Saga Worker Nodes:** Stateless python/go workers executing workflow activities (risk evaluation, OPA evaluation, API dispatch).

### 3.3 Layer 3: Intelligence Layer
* **Diagnosis Engine:** Deterministic mapping layer that translates raw Razorpay error codes (`BAD_REQUEST_ERROR`, `GATEWAY_ERROR`, `PAYMENT_EXPIRED`) and network decline parameters into standard failure taxonomies.
* **Revenue Risk Engine:** Computes instantaneous Revenue at Risk ($\text{RaR}$) and prioritizes recovery workflow execution queues.
* **AI Decision Agent:** LLM reasoning module (Claude 3.5 Sonnet / OpenAI GPT-4o) tasked with selecting dunning channels, drafting localized Hinglish notifications, and calculating payday-aligned retry delays.
* **Langfuse Tracing:** Integrates deep LLM observability to track token costs, latency, prompt templates, and reasoning chains.

### 3.4 Layer 4: Governance Layer (The Inner Trust Boundary)
* **Open Policy Agent (OPA):** Embedded, standalone WebAssembly/Go policy daemon enforcing RegTech constraints written in Rego language.
* **Policy Rule Set:**
  * Enforces RBI pre-debit notification mandatory 24-hour waiting period.
  * Enforces acquirer velocity caps and 48-hour retry cooldown windows.
  * Restricts merchant discount allocation to maximum pre-approved thresholds.
* **Hard Decision Output:** Returns a signed evaluation token containing `allow: true` or `allow: false` with explicit rule rejection reasons.

### 3.5 Layer 5: Execution Layer
* **Action Dispatcher:** Consumes OPA-approved recovery plans and dispatches HTTP requests to external APIs.
* **Razorpay Integration Client:** Triggers Subscriptions Retries API, Mandate Maintenance APIs, and Payment Links creation.
* **Novu Notification Orchestrator:** Manages multi-channel customer communications (WhatsApp, SMS, Email, Hinglish IVR Voice Call).

### 3.6 Layer 6: Storage & Audit Layer
* **PostgreSQL (Operational Datastore):** Stores structured entity models (Merchants, Subscriptions, Payments, Workflows) indexed for $O(1)$ indexed reads from the frontend dashboard.
* **immudb (Cryptographic Audit Ledger):** Immutable, append-only tamper-evident database. Writes cryptographic hashes of every failure event, diagnostic result, OPA policy decision, LLM prompt/response, and final settlement outcome.

### 3.7 Layer 7: Presentation Layer
* **React + Vite Finance Dashboard:** Modern, high-performance web client for Finance Controllers.
* **Capabilities:** Real-time MRR recovery metrics, active recovery saga visualization, OPA compliance audit viewer, and cryptographic proof verification tool.

---

## 4. Complexity Guarantees

Enterprise payment architectures must scale linearly without exponential latency spikes or memory leaks. The system enforces strict algorithmic bounds:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         COMPLEXITY GUARANTEES                            │
├──────────────────────────────────────────────────────────────────────────┤
│ Time Complexity  : O(N) Total Batch Processing (O(1) Constant per Event)│
│ Space Complexity : O(1) Memory Footprint per Execution Worker           │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Time Complexity: $O(N)$ Total / $O(1)$ Per Event
* **Event Streaming Pipeline:** Every webhook ingested from Redpanda is processed independently in constant time $O(1)$.
* **Elimination of Cartesian Scans:** Legacy cron engines run $O(N^2)$ nested scans across subscription tables to identify retry candidates. Our event-driven pipeline evaluates incoming payment failure events immediately upon arrival.
* **Indexed Lookups:** All operational database queries (fetching subscriber history, active mandate state) hit B-Tree indexed keys in PostgreSQL in $O(\log k) \approx O(1)$ time.
* **Total Batch Complexity:** Processing $N$ payment failures scales strictly as $O(N)$.

### 4.2 Space Complexity: $O(1)$ Worker Memory Footprint
* **Stateless Event Ingestion:** Worker nodes process events as stateless streams, holding zero in-memory batch arrays. Memory footprint remains constant $O(1)$ regardless of whether $N = 10$ or $N = 1,000,000$.
* **Externalized Workflow State:** Temporal externalizes workflow state to an enterprise persistence layer. Active sagas sleeping for 24 hours occupy zero RAM on execution workers.
* **Bounded Historical Windows:** Diagnostic context retrieval limits subscriber billing history lookups to a fixed sliding window ($K = 5$ previous transactions), enforcing $O(1)$ auxiliary space overhead.

---

## 5. Security Boundaries & Trust Architecture

The system establishes two impenetrable security perimeters:

```
                  ┌─────────────────────────────────────────┐
                  │          UNTRUSTED PUBLIC NETWORK       │
                  └────────────────────┬────────────────────┘
                                       │
  =====================================│=====================================
  OUTER SECURITY BOUNDARY              ▼ (Webhook Delivery)
  ===========================================================================
                  ┌─────────────────────────────────────────┐
                  │ FastAPI Webhook Listener (HMAC SHA256) │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │      LLM Decision Reasoning Engine      │
                  └────────────────────┬────────────────────┘
                                       │ (Untrusted Proposed Plan)
  =====================================│=====================================
  INNER GOVERNANCE BOUNDARY            ▼ (Policy Check)
  ===========================================================================
                  ┌─────────────────────────────────────────┐
                  │   Open Policy Agent (OPA) Guardrail     │
                  └────────────────────┬────────────────────┘
                                       │ (allow: true)
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │    Razorpay API & Action Execution      │
                  └─────────────────────────────────────────┘
```

### 5.1 Outer Security Boundary: Webhook Authenticity Verification
* **Threat Model:** Spoofed HTTP POST requests injected by malicious third parties to trigger unauthorized retries or send fake dunning notifications.
* **Protection Mechanism:** The FastAPI Webhook Listener computes an HMAC SHA256 signature of the raw request body using the shared `RAZORPAY_WEBHOOK_SECRET` and compares it against the `X-Razorpay-Signature` header via constant-time string comparison (`hmac.compare_digest`). Unsigned or invalid requests are dropped immediately at the network perimeter.

### 5.2 Inner Governance Boundary: OPA Zero-Trust AI Guardrail
* **Threat Model:** LLM hallucination, prompt injection, model drift, or rogue recovery plan proposing unauthorized discounts, spamming customers, or executing retries in violation of RBI e-mandate rules.
* **Protection Mechanism:** The LLM Decision Agent has **zero execution permissions**. It cannot directly call Razorpay APIs or Novu notification services. Its output is piped strictly as a data payload into the Open Policy Agent (OPA).
* **Policy Enforcer:** OPA evaluates the proposed payload against immutable Rego policy files. Only payloads that yield `allow: true` advance to the Execution Layer. Any violation results in an immediate workflow branch to a safe, deterministic fallback routine.

---

## 6. Document Metadata & Sign-off

* **Author:** Fintech System Architect / Track 3 Engineering Team  
* **Target Buildathon:** Razorpay AI Buildathon — Track 3 (AI Revenue Recovery)  
* **Upstream Specification:** `docs/01-problem-statement.md`, `docs/02-solution-overview.md`  
* **Implementation Artifacts:** `docs/03-system-architecture.md`  
