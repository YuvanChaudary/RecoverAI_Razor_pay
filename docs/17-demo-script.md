# 5-Minute Final Demo Video Script & Storyboard
**Project:** AI Revenue Recovery Agent  
**Target Buildathon:** Razorpay AI Buildathon (Track 3: AI Revenue Recovery)  
**Document ID:** `docs/17-demo-script.md`  
**Total Target Duration:** 05:00 Minutes  
**Status:** Approved Pitch Baseline  

---

## Executive Pitch Philosophy

This script is engineered to maximize judges' scoring across all evaluation criteria for **Track 3 (AI Revenue Recovery)**. Rather than walking line-by-line through backend source code, the video delivers an executive demonstration of **business ROI (Net ₹ Recovered)**, **RegTech safety (Zero Compliance Breaches)**, **Zero-Trust AI governance**, and **statistically proven batch lift**.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          5-MINUTE TIME ALLOCATION                        │
├───────────────┬─────────────────────────────────┬────────────────────────┤
│ Time Window   │ Pitch Focus Phase               │ Key Technical Hook     │
├───────────────┼─────────────────────────────────┼────────────────────────┤
│ 0:00 – 0:30   │ The Hook & Involuntary Churn    │ Quantified RaR (₹)     │
│ 0:30 – 1:15   │ React Dashboard & Risk Engine   │ Instant exposure (₹)   │
│ 1:15 – 2:15   │ Live Diagnosis & AI Reasoning   │ Why it failed (NSF)    │
│ 2:15 – 3:15   │ OPA Governance & Execution      │ OPA Approve vs. Block  │
│ 3:15 – 4:15   │ 500-Case Synthetic Batch Proof  │ +257% Net Revenue Lift │
│ 4:15 – 5:00   │ Cryptographic Audit & Close     │ immudb Proof Badge     │
└───────────────┴─────────────────────────────────┴────────────────────────┘
```

---

## Storyboard & Script Breakdown

### Act 1: The Hook & Problem (0:00 – 0:30)

**[Visual: Presenter on camera or crisp motion graphic showing a recurring subscription debit failing. Screen displays text: "Subscription Failed → Involuntary Churn → Silent Revenue Decay".]**

**Spoken Script:**  
> *"When a recurring subscription payment fails, the merchant doesn't just lose one transaction. That silent failure immediately converts active customer LTV into quantified **Revenue at Risk**. Today, most businesses rely on 'dumb' cron jobs—blindly retrying payments every 24 hours regardless of why they failed. This naive approach burns customer trust, yields terrible recovery rates, and risks catastrophic RBI e-mandate regulatory violations. We built a better way."*

---

### Act 2: Executive Dashboard & Risk Engine (0:30 – 1:15)

**[Visual: Screen recording transitions to the React Finance Controller Dashboard. Mouse hovers over the top-level Hero Metric Cards.]**

**Spoken Script:**  
> *"Meet the **AI Revenue Recovery Agent**. The moment a failure occurs, our **Revenue Risk Engine** sits at the very front of the pipeline to quantify exact rupee exposure before any processing occurs. Here on our Finance Controller Dashboard, you immediately see **₹50 Lakhs in Revenue at Risk** across 500 subscription cases. But unlike legacy systems, we don't just report numbers—we manage a bounded, autonomous recovery pipeline that has already recovered **₹32.5 Lakhs**, delivering a **65% recovery rate** with **STRICT ZERO regulatory violations**."*

**[Visual: Zoom in on the "Baseline Lift" widget highlighting `+ ₹23.37 Lakhs (+257.26% Lift over Cron)` in glowing green text.]**

---

### Act 3: Intelligent Diagnosis & AI Decision (1:15 – 2:15)

**[Visual: Terminal / Postman window triggers a live Razorpay test webhook `subscription.charged.failed` with error `BAD_REQUEST_ERROR` and reason `insufficient_funds` (NSF). Switch back to React Dashboard as a new case appears.]**

**Spoken Script:**  
> *"Let's watch a live recovery in action. Razorpay emits a failure webhook. Our **Diagnosis Engine** parses the raw gateway telemetry and immediately identifies the root cause: **Liquidity Friction** due to insufficient funds. Instead of blindly retrying in 24 hours, our **AI Decision Agent** analyzes subscriber context. Recognizing that the customer's salary is credited on the 23rd, the AI proposes a payday-aligned 72-hour retry delay combined with a polite Hinglish WhatsApp notification containing a direct payment link."*

**[Visual: Click on the case row. Open the AI Reasoning Drawer showing the structured JSON output and a clickable link: `View Langfuse LLM Trace: trc_langfuse_998877`.]**

---

### Act 4: The Governance Gate & Bounded Execution (2:15 – 3:15)

**[Visual: Split screen visualizer. Left side shows a valid retry passing OPA with a bright green shield: `OPA APPROVED`. Right side demonstrates an invalid retry being hard-blocked with a red shield: `OPA BLOCKED - RULE-002: COOLDOWN_BREACH`.]**

**Spoken Script:**  
> *"Now for our core innovation: **Zero-Trust Governance**. In fintech, AI cannot have direct execution keys. Our LLM is strictly a decision engine. Its proposal MUST pass through our deterministic **Open Policy Agent (OPA)** guardrail. Watch this: when the AI proposes a valid action, OPA verifies RBI pre-debit rules and signs an approval token. But if an AI plan violates a 24-hour cooldown or retry velocity cap, OPA issues an instant hard block—stopping automated execution dead in its tracks and routing the case to human escalation. No hallucination can ever breach regulatory rails."*

**[Visual: Switch to Temporal UI dashboard. Show the `RecoverySagaWorkflow` executing `DispatchRazorpayActionActivity`. Switch back to Razorpay Dashboard showing payment status updated to `captured`.]**

---

### Act 5: Synthetic Batch Evaluation — The Ultimate Proof (3:15 – 4:15)

**[Visual: Navigate to the "Batch Simulator" tab on the React Dashboard. Click "Run 500-Case Benchmark". Show real-time progress bar filling up, then rendering the comparative Scorecard Matrix.]**

**Spoken Script:**  
> *"A single recovery is just an anecdote. To satisfy enterprise rigor, we built an integrated **Batch Simulator**. We benchmarked our AI Recovery Agent against a standard cron-job control strategy across **500 synthetic failed subscriptions** modeling real Indian payment failure distributions. The results are undeniable: The legacy cron engine recovered only **18.2%** of revenue while committing **20 regulatory breaches**. Our AI Agent recovered **65.0%**, delivering **₹23.37 Lakhs in Net Revenue Lift**—a **257% gain**—while maintaining **STRICT ZERO compliance violations**."*

**[Visual: Zoom in on the Comparative Matrix highlighting `Net Revenue Lift: + ₹2,337,250.00` and `Regulatory Violations: 0`.]**

---

### Act 6: Cryptographic Audit & Winning Close (4:15 – 5:00)

**[Visual: Open the Case Audit Drill-Down modal for Case #case_rec_01. Scroll down to the bottom section showing `immudb Cryptographic Ledger Receipt`. Click the glowing button: **"Verify Ledger Proof"**.]**

**Spoken Script:**  
> *"Finally, every state transition, failure diagnosis, AI trace ID, OPA verification token, and settlement receipt is committed to `immudb`—an append-only, tamper-evident cryptographic ledger. With one click, Finance Controllers can verify SHA-256 Merkle tree root hashes live in the dashboard, guaranteeing 100% auditability for SOC2 and RBI compliance.*

**[Visual: Green checkmark badge flashes: `Cryptographically Verified in immudb Merkle Tree`. Screen transitions to final presentation slide with GitHub Repository link, architecture summary, and team credits.]**

**Spoken Script:**  
> *"We don't just detect failed payments. We diagnose the root cause, decide the optimal recovery path, enforce immutable regulatory guardrails, and prove every single rupee we recover. Thank you."*

---

## Key Screen Recording & Visual Checklist

* [ ] **0:15** — Motion graphic: Subscription failure converting to Revenue at Risk ($\text{RaR}$).
* [ ] **0:45** — React Dashboard Hero Section: Hover over $\text{₹}50\text{L}$ Total $\text{RaR}$ and $\text{₹}32.5\text{L}$ Total Recovered.
* [ ] **1:30** — Webhook delivery: Terminal trigger $\rightarrow$ Instant diagnostic badge update (`LIQUIDITY_FRICTION`).
* [ ] **2:00** — AI Drawer: Clickable Langfuse trace link (`trc_langfuse_...`).
* [ ] **2:40** — OPA Split Screen: Green `APPROVED` token vs. Red `BLOCKED (RULE-002)` shield.
* [ ] **3:00** — Temporal UI: Sleeping timer fast-forwarding to activity execution.
* [ ] **3:45** — Batch Evaluation Scorecard: Side-by-side comparison table showing $+257\%$ Lift and $0$ Violations.
* [ ] **4:45** — `immudb` Live Verification: Click "Verify Ledger Proof" $\rightarrow$ Green verified badge.

---

## Document Metadata & Sign-off

* **Author:** Fintech System Architect & Product Pitch Lead / Track 3 Team  
* **Target Buildathon:** Razorpay AI Buildathon — Track 3 (AI Revenue Recovery)  
* **Upstream Specification:** `docs/01-problem-statement.md`, `docs/02-solution-overview.md`, `docs/09-governance-and-policies.md`, `docs/12-batch-evaluation.md`, `docs/13-dashboard-specification.md`  
* **Implementation Artifacts:** `docs/17-demo-script.md`  
