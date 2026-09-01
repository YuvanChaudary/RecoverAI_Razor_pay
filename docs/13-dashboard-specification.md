# Finance Controller Dashboard UI/UX Specification
**Project:** Razorpay AI Buildathon (Track 3)  
**Document ID:** `docs/13-dashboard-specification.md`  
**Status:** Approved Architectural Baseline  

---

## Executive Summary

This document specifies the UI/UX architecture, layout hierarchy, visual component mapping, and API integration paths for the **React + Vite Finance Controller Dashboard**. Built specifically for CFOs, Finance Controllers, and Merchant Payment Operations teams, the dashboard serves as an executive command center to track real-time revenue recovery ($\text{₹}$), verify regulatory compliance (0 violations), inspect OPA governance decisions, and audit individual case timelines with cryptographic proof verification.

---

## 1. Overview & Target Persona

### 1.1 Target Persona
* **Primary Users:** Finance Controllers, CFOs, VP of Revenue Operations, Merchant Payment Ops Managers.
* **Non-Target Users:** Consumer end-subscribers (This is an enterprise B2B management portal, not a customer checkout widget).

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        CORE DESIGN PHILOSOPHY                            │
├──────────────────────────────────────────────────────────────────────────┤
│ 1. High Data Density : Dark-mode glassmorphism with instant visual hierarchy│
│ 2. Financial Truth   : Only settled rupees (₹) are reported as recovered │
│ 3. 100% Governance   : Zero black-box AI decisions; OPA proofs visible    │
│ 4. Audit Lineage     : 1-click drill-down to immudb hashes & Langfuse    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Screen 1: Executive View (The Hero Section)

The top of the dashboard displays high-impact financial cards feeding real-time metrics from `GET /api/v1/metrics/overview`.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         EXECUTIVE HERO WIDGETS                           │
├───────────────────┬───────────────────┬───────────────────┬──────────────┤
│ TOTAL REVENUE     │ REVENUE RECOVERED │ BASELINE LIFT     │ TOTAL CASES  │
│ AT RISK           │                   │                   │ PROCESSED    │
│                   │                   │                   │              │
│ ₹ 5,000,000.00    │ ₹ 3,250,000.00    │ + ₹ 2,337,250.00  │ 500 Subscriptions│
│ (100% Exposure)   │ (65.0% Rec. Rate) │ (+ 257.2% Lift)   │ (0 Violations)│
└───────────────────┴───────────────────┴───────────────────┴──────────────┘
```

### Hero Metric Cards Detail
1. **Total Revenue at Risk ($\text{RaR}$):** Displays total uncollected invoice value ($\text{₹}$) across ingested failures.
2. **Total Revenue Recovered:** Displays gross settled rupees ($\text{₹}$) alongside the overall Recovery Rate percentage ($65.0\%$).
3. **Baseline Comparison Lift:** Highlights net rupee gain over standard legacy cron retry logic (e.g., `+ ₹2,337,250.00 (+257.2% Lift)`).
4. **Total Cases & Compliance Health:** Shows total cases processed ($500$) and confirms zero regulatory violations ($0$ breaches).

---

## 3. Screen 2: Recovery Analysis (The Cause Breakdown)

This section renders comparative bar charts and analytical tables powered by `GET /api/v1/metrics/breakdown`, proving that the AI Agent applies differentiated, root-cause-specific strategies rather than uniform retries.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   FAILURE CATEGORY PERFORMANCE MATRIX                    │
├──────────────────────────┬───────────┬──────────────┬───────┬────────────┤
│ Diagnostic Cause         │ Cases (N) │ Total RaR    │ Rec % │ Avg MTTR   │
├──────────────────────────┼───────────┼──────────────┼───────┼────────────┤
│ LIQUIDITY_FRICTION (NSF) │ 225       │ ₹ 2,250,000  │ 75.0% │ 44.5 Hours │
│ TRANSIENT_INFRASTRUCTURE │ 125       │ ₹ 1,250,000  │ 90.0% │ 3.2 Hours  │
│ INSTRUMENT_INVALIDATION  │ 75        │ ₹   750,000  │ 40.0% │ 78.0 Hours │
│ MANDATE_COMPLIANCE_LOCK  │ 75        │ ₹   600,000  │  6.7% │ 12.0 Hours │
└──────────────────────────┴───────────┴──────────────┴───────┴────────────┘
```

### Visual Features
* **Differential Strategy Proof:** Demonstrates high recovery ($90\%$) for transient switch errors vs. immediate halting for instrument invalidation.
* **Interactive Filtering:** Clicking any category filters the primary Case Management Table below.

---

## 4. Screen 3: Compliance & Governance Panel

Visualizes the activity of the Open Policy Agent (OPA) "Inner Trust Boundary" to prove regulatory compliance to Finance Controllers.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    OPA GOVERNANCE GATE STATUS PANEL                      │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [  325  ]  Automated Actions Approved (OPA Signed)                      │
│  [   94  ]  Unsafe Actions Blocked (Cooldown / Pre-Debit Violation)      │
│  [   81  ]  Smart Human Escalations (High Risk / Terminal Failure)       │
│  [    0  ]  REGULATORY VIOLATIONS (STRICT ZERO TARGET)                    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Key UI Indicators
* **Green Compliance Shield:** Visual indicator showing `RBI E-Mandate RegTech Active`.
* **Blocked Actions Drawer:** Clickable counter opening a modal listing all 94 blocked retry attempts along with the exact Rego rule ID (e.g., `RULE-002: MINIMUM_COOLDOWN_WINDOW`).

---

## 5. Screen 4: Case Drill-Down (The Audit Modal)

When a user selects a specific subscription failure from the Case Management Table (`GET /api/v1/cases`), the dashboard opens the **7-Stage Audit Modal** backed by `GET /api/v1/cases/{case_id}`:

```
┌──────────────────────────────────────────────────────────────────────────┐
│               CASE DRILL-DOWN AUDIT TIMELINE (Case #case_rec_01)         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. INGESTION  ──► Webhook Ingested (pay_PZ182x9A7kL3mQ)                 │
│  2. RISK       ──► RaR Quantified: ₹ 2,999.00 (MEDIUM_RISK)              │
│  3. DIAGNOSIS  ──► Mapped Cause: LIQUIDITY_FRICTION (NSF on 20th)        │
│  4. AI DECIDE  ──► Proposed: 72h Payday Delay + Hinglish WhatsApp        │
│                    [View Langfuse LLM Trace: trc_langfuse_998877]       │
│  5. OPA GOVERN ──► Status: APPROVED (Verification Token: tok_opa_987)    │
│  6. EXECUTE    ──► Razorpay Invoice Retry Dispatched (pay_PZ999)         │
│  7. AUDIT      ──► Settled ₹ 2,999.00 | immudb Tx #4820194               │
│                    [VERIFY LEDGER HASH PROOF BADGE]                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Deep Inspection Controls
1. **Langfuse Trace Link:** Direct hyperlink opening the exact prompt, response, latency, and cost record in Langfuse.
2. **Cryptographic Proof Badge:** Clickable badge triggering an on-demand SHA-256 Merkle tree verification against `immudb`.

---

## 6. Component Mapping & Architecture

The React codebase is organized into modular UI components mapping 1:1 with API contract endpoints:

```
src/components/
├── dashboard/
│   ├── MetricsOverviewCard.jsx          <-- GET /api/v1/metrics/overview
│   ├── BaselineComparisonWidget.jsx     <-- GET /api/v1/metrics/overview
│   ├── FailureCategoryBreakdown.jsx     <-- GET /api/v1/metrics/breakdown
│   └── GovernanceStatusPanel.jsx        <-- GET /api/v1/metrics/overview
├── cases/
│   ├── CaseManagementTable.jsx          <-- GET /api/v1/cases
│   ├── CaseFilters.jsx                  <-- Query params handler
│   └── CaseAuditDrilldownModal.jsx      <-- GET /api/v1/cases/{case_id}
├── simulator/
│   └── BatchSimulatorControl.jsx        <-- POST /api/v1/simulator/batch
└── audit/
    └── ImmudbProofVerifier.jsx          <-- POST /api/v1/cases/{id}/verify
```

---

## 7. Document Metadata & Sign-off

* **Author:** Fintech System Architect / Track 3 Engineering Team  
* **Target Buildathon:** Razorpay AI Buildathon — Track 3 (AI Revenue Recovery)  
* **Upstream Specification:** `docs/01-problem-statement.md`, `docs/03-system-architecture.md`, `docs/05-api-contract.md`, `docs/11-audit-trail.md`, `docs/12-batch-evaluation.md`  
* **Implementation Artifacts:** `docs/13-dashboard-specification.md`  
