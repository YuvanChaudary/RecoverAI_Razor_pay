# Foundational Engineering Contract: AI Revenue Recovery Agent
**Project:** Razorpay AI Buildathon (Track 3)  
**Document ID:** `docs/01-problem-statement.md`  
**Status:** Approved Architectural Baseline  

---

## Executive Summary

In subscription and recurring revenue models, payment failures are rarely caused by explicit customer intent to churn. Instead, merchant top-line revenue is silently eroded by **involuntary churn**—a state where valid subscriptions terminate due to transient bank declines, insufficient funds, expired payment instruments, or strict e-mandate compliance locks.

Existing merchant recovery systems rely on static, scheduled retry logic ("dumb cron jobs") that execute blind retries regardless of failure root cause. This legacy approach results in low recovery rates, degraded customer experience, acquirer-level penalties, and severe compliance risks under Reserve Bank of India (RBI) e-mandate regulations.

This document establishes the foundational engineering contract for the **AI Revenue Recovery Agent**: an autonomous, governed system designed to detect revenue at risk, diagnose granular payment failure root causes, decide optimal intervention strategies, enforce strict regulatory guardrails via Open Policy Agent (OPA), execute bounded recovery workflows through Razorpay APIs, and produce an immutable, financial-grade audit log.

---

## 1. The Core Problem: Involuntary Churn & Silent Revenue Decay

### 1.1 Involuntary Churn Mechanics
Involuntary churn occurs when a recurring payment transaction fails at the processing gateway, card network, issuing bank, or e-mandate engine without explicit cancellation intent from the subscriber. 

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       REVENUE LOSS PIPELINE                              │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
   Voluntary Churn                           Involuntary Churn
(User cancels service)             (Silent Payment Failure: NSF, Expiry, Bank Decline)
              │                                         │
              ▼                                         ▼
   Expected LTV Loss                          Quantifiable "Revenue at Risk"
                                                        │
                                                        ▼
                                           Requires Autonomous AI Recovery
```

Key drivers of payment failures in the Indian payment ecosystem include:
* **Insufficient Funds (NSF / Insufficient Balance):** Account balances drop below the debit amount prior to salary cycles or debit execution windows.
* **Expired or Replaced Instruments:** Credit/debit cards reach expiry or are replaced post-loss/fraud without updated mandate binding.
* **Transient Issuer & Switch Failures:** Core Banking System (CBS) downtime, NPCI/e-NACH switch timeouts, or acquirer processing errors.
* **E-Mandate Execution Failures:** Pre-debit notification mismatches, mandate limit breaches, or missing authentication tokens under circular mandates.
* **Bank-Side Risk & Soft Declines:** Fraud detection engines flagging velocity anomalies or unusual time-of-day execution.

### 1.2 Quantifying "Revenue at Risk"
For subscription businesses (SaaS, OTT, Fintech, Utilities), every failed payment immediately converts active ARR/MRR into **Revenue at Risk ($\text{RaR}$)**.

$$\text{Revenue at Risk (RaR)} = \sum_{i=1}^{N} \left( V_i + \text{LTV}_{\text{remaining}, i} \times P(\text{Churn} \mid \text{Failure}_i) \right)$$

Where:
* $V_i$: Immediate uncollected invoice/debit value for subscription $i$.
* $\text{LTV}_{\text{remaining}, i}$: Net present value of expected future cash flows from subscriber $i$.
* $P(\text{Churn} \mid \text{Failure}_i)$: Conditional probability of permanent subscriber loss given payment failure mode $\text{Failure}_i$.

Left unmanaged, unrecovered payment failures compound monthly, artificially elevating customer acquisition costs (CAC) and prematurely truncating customer lifetime value (LTV).

---

## 2. Flaws of Existing Solutions

Legacy payment recovery infrastructure across payment service providers and merchant backend platforms exhibits four structural flaws:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          LEGACY RECOVERY VS. AI AGENT                             │
├───────────────────────────────┬──────────────────────────────────────────────────┤
│ Legacy Cron Approach          │ AI Revenue Recovery Agent                        │
├───────────────────────────────┼──────────────────────────────────────────────────┤
│ Blind 24-hour retry interval  │ Dynamic, payday-aware, failure-specific timing   │
│ Zero root cause diagnosis     │ Multi-dimensional failure telemetry analysis     │
│ Risk of RBI mandate blacklisting│ Pre-execution OPA compliance guardrails          │
│ No financial ledger auditing  │ Immutable, verifiable audit event trail          │
└───────────────────────────────┴──────────────────────────────────────────────────┘
```

### 2.1 Dumb Cron-Based Retries
Existing merchant platforms run static batch jobs (e.g., retrying every failed payment daily at 00:00 UTC or 09:00 IST for 3 consecutive days). 
* **Payload Blindness:** A hard decline (e.g., "Card Expired" or "Account Closed") is retried identically to a soft decline (e.g., "Network Timeout").
* **Suboptimal Timing:** Retrying an NSF failure 24 hours after initial decline frequently hits an un-replenished bank account, wasting retry attempts.

### 2.2 Absence of Diagnostic Intelligence
Legacy recovery engines lack context integration. They do not correlate failure telemetry with external signals such as:
* Customer salary and liquidity windows (e.g., 1st–5th of the month vs. month-end).
* Bank CBS scheduled maintenance windows.
* Channel responsiveness (WhatsApp vs. SMS vs. In-App vs. Email).
* Promise-to-Pay (P2P) history or customer interaction patterns.

### 2.3 Regulatory Non-Compliance & RBI E-Mandate Risks
Under Reserve Bank of India (RBI) guidelines for recurring payments on cards/UPI/e-NACH:
* **Pre-Debit Notification Mandatory Rules:** Merchants must issue a pre-debit notification at least 24 hours prior to recurring debit execution. Executing immediate or un-notified retries can violate regulatory mandates.
* **Retry Limits & Cooldown Windows:** Excessively pinging issuing banks violates acquirer velocity thresholds and risks merchant terminal blacklisting or bank-level mandate revocation.
* **Customer Consent & Limit Enforcement:** Escalations (e.g., sending alternative payment links for amounts exceeding mandate caps) must adhere strictly to authorization limits.

Ungoverned automated retry scripts risk structural regulatory non-compliance, exposing merchants to monetary fines and processing suspension.

### 2.4 Financial Auditability Deficit
Standard cron logs record basic status codes (`500 Internal Server Error` or `400 Bad Request`) without maintaining a verifiable, audit-compliant trail of *why* an action was taken, *which* policy authorized it, and *what* financial state transition occurred.

---

## 3. The Target Workflow: Autonomous & Governed Recovery Loop

To solve involuntary churn safely at enterprise scale, the AI Revenue Recovery Agent implements a closed-loop, six-stage lifecycle: **Detect $\rightarrow$ Diagnose $\rightarrow$ Decide $\rightarrow$ Govern $\rightarrow$ Execute $\rightarrow$ Audit**.

```
 ┌───────────┐     ┌───────────┐     ┌───────────┐
 │ 1. DETECT │ ──► │2. DIAGNOSE│ ──► │ 3. DECIDE │
 └───────────┘     └───────────┘     └───────────┘
                                           │
                                           ▼
 ┌───────────┐     ┌───────────┐     ┌───────────┐
 │ 6. AUDIT  │ ◄── │5. EXECUTE │ ◄── │ 4. GOVERN │
 └───────────┘     └───────────┘     └───────────┘
```

### Stage 1: Detect (Quantify Revenue at Risk)
* Ingest real-time webhooks (`payment.failed`, `subscription.halted`, `mandate.paused`) from Razorpay.
* Parse payload metadata, subscription schedule, and past billing history.
* Calculate instantaneous Revenue at Risk ($\text{RaR}$) and prioritize recovery queue by net expected recoverable value.

### Stage 2: Diagnose (Root Cause Analysis)
* Classify raw decline codes (e.g., `BAD_REQUEST_ERROR`, `GATEWAY_ERROR`, `PAYMENT_EXPIRED`) into granular diagnostic buckets:
  1. **Transient Infrastructure Failure:** Gateway switch timeout, CBS offline.
  2. **Liquidity Friction:** NSF / Insufficient balance.
  3. **Instrument Invalidation:** Expired card, cancelled token, inactive UPI ID.
  4. **Mandate Lifecycle Block:** Pre-debit notification missing, limit exceeded, mandate revoked.
* Extract subscriber context: preferred language (e.g., Hinglish), historical payday alignment, previous promise-to-pay compliance.

### Stage 3: Decide (AI Intervention Selection)
Synthesize diagnostic data to select the optimal recovery strategy:
* **Optimal Retry Timing:** Delay debit execution to match bank maintenance resolution or customer payday window.
* **Direct Customer Engagement:** Dispatch personalized, context-aware dunning messages (e.g., Hinglish voice agent, WhatsApp payment link, SMS notification).
* **Instrument Swap / Mandate Repair:** Generate a Razorpay Payment Link or Mandate Update Flow if the underlying instrument is invalid.
* **Stopping Rules:** Halt retries if recovery probability drops below cost threshold or hard-decline criteria are met.

### Stage 4: Govern (Strict OPA Compliance Check)
Before *any* action is dispatched, the agent forwards the execution payload to an isolated **Open Policy Agent (OPA)** policy engine.
* Evaluate regulatory policies: RBI pre-debit notice validation, mandatory 24h/48h cooldown periods, maximum retry count checks.
* Evaluate merchant policies: Max contact frequency caps, discount bounds for recovery incentives.
* **Hard Stop Condition:** If OPA returns `deny`, the execution path is aborted instantly, preventing non-compliant actions.

### Stage 5: Execute (Razorpay API & Communication Dispatch)
Upon OPA authorization (`allow`), execute the intervention via deterministic integrations:
* Trigger Razorpay Retries API / Subscription Debit endpoint.
* Create Razorpay Payment Links for manual customer-driven recovery.
* Dispatch multi-channel communications (WhatsApp / Hinglish Voice / Email) with embedded payment action hooks.

### Stage 6: Audit (Immutable Financial Logging)
* Record every state transition, failure diagnostic, OPA evaluation log (`allow`/`deny` with policy signatures), decision prompt context, and execution response into a append-only, tamper-evident audit store.
* Provide full financial traceability from initial payment failure to final rupee recovered.

---

## 4. The Definition of Success

In financial technology engineering, vanity metrics such as "notifications dispatched," "emails opened," or "AI model inference speed" are insufficient indicators of system efficacy.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         DEFINITION OF SUCCESS                            │
├──────────────────────────────────────────────────────────────────────────┤
│  SUCCESS IS STRICTLY DEFINED AS:                                         │
│                                                                          │
│  "Measured Net Money (₹) Recovered Across a Batch Without Regulatory     │
│   Infractions or Customer Harassment."                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

The system is successful **only if**:
1. **Financial Output is Positive:** Net recovered revenue exceeds baseline recovery strategies after accounting for gateway and communication costs.
2. **Zero Compliance Breaches:** Zero violations of RBI e-mandate retry policies, pre-debit notice timing rules, or merchant-defined guardrails.
3. **Bounded Execution:** Every intervention terminates within explicit stopping criteria (max retries, max days elapsed) without infinite retry loops.

---

## 5. The Evaluation Metric

The AI Revenue Recovery Agent will be benchmarked against a synthetic control environment modeling real-world Indian subscription payment dynamics.

### 5.1 Benchmark Dataset & Execution Protocol
* **Batch Size:** $N = 500$ failed subscription transactions.
* **Failure Distribution:** Realistic distribution covering NSF (45%), Bank/Switch Downtime (25%), Expired/Invalid Instrument (15%), and Mandate/Pre-debit Violations (15%).
* **Control Baseline:** Standard Cron Engine retrying failed payments every 24 hours up to 3 times with standard static email reminders.
* **Test Subject:** AI Revenue Recovery Agent executing dynamic detection, diagnosis, decision, OPA governance, and multi-channel/retry execution.

### 5.2 Primary Quantitative Evaluation Metrics

$$\text{Recovery Lift (\%)} = \left( \frac{\text{Net Revenue Recovered}_{\text{AI Agent}} - \text{Net Revenue Recovered}_{\text{Baseline}}}{\text{Net Revenue Recovered}_{\text{Baseline}}} \right) \times 100$$

| Metric Category | Formula / Indicator | Target Standard |
| :--- | :--- | :--- |
| **Gross Recovered Revenue** | $\sum \text{Rupees (₹) successfully settled}$ | Maximize vs. Control |
| **Net Recovered Revenue** | $\text{Gross Recovered (₹)} - (\text{API/Communication Costs})$ | Positive ROI (> 5x recovery cost) |
| **Recovery Rate (%)** | $\frac{\text{Successful Recoveries}}{500 \text{ Subscriptions}} \times 100$ | Statistically significant lift over baseline |
| **Compliance Violations** | $\sum \text{OPA Denials breached} + \text{RBI Guideline Breaches}$ | **Strict Zero Tolerance ($0$)** |
| **Mean Time-to-Recovery (MTTR)** | Average hours elapsed from initial failure to settlement | Reduction vs 72h cron window |
| **Customer Friction Score** | Total contact attempts per recovered rupee | Minimize contact redundancy |

---

## 6. Document Metadata & Sign-off

* **Author:** Fintech System Architect / Track 3 Engineering Team  
* **Target Buildathon:** Razorpay AI Buildathon — Track 3 (AI Revenue Recovery)  
* **Upstream Specification:** Hackathon Brief & Razorpay Payment/Subscription API Docs  
* **Implementation Artifacts:** `docs/01-problem-statement.md`  
