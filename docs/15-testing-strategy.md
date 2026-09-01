# Testing Strategy & Quality Assurance Specification
**Project:** Razorpay AI Buildathon (Track 3)  
**Document ID:** `docs/15-testing-strategy.md`  
**Status:** Approved Architectural Baseline  

---

## Executive Summary

This document specifies the quality assurance methodology, testing pyramid, automated test suites, time-travel workflow testing, and chaos fault-injection procedures for the **AI Revenue Recovery Agent**. Designed to guarantee financial correctness, zero regulatory infractions, and resilient distributed execution, the testing strategy enforces a strict rule: **"Deterministic components must be 100% testable offline, probabilistic AI outputs must be bounded by schema guardrails, and workflows must recover gracefully from any infrastructure crash."**

---

## 1. Overview & Testing Philosophy

In financial software engineering, unhandled exceptions, race conditions, or unverified AI actions directly cause financial loss and regulatory sanctions.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         THE TESTING PYRAMID                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                 / \     Chaos & Fault Injection Tests                    │
│                /   \    (Worker Crash, 5xx Injection, Duplicate Events)  │
│               /-----\                                                    │
│              /       \   Temporal Time-Travel Integration Tests          │
│             /---------\  (Workflow Saga Replay, Fast-Forward Timers)     │
│            /           \                                                 │
│           /-------------\ Bounded AI Guardrail Mock Tests                │
│          /               \ (Pydantic Schema Validation, Fallback Triggers)│
│         /-----------------\                                              │
│        /                   \ Deterministic Core Unit Tests (Pytest + OPA)│
│       /---------------------\ (Risk Engine, Diagnosis, Rego Policies)    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Core QA Principles
1. **Deterministic Core 100% Offline:** All risk calculation, decline code mapping, OPA governance evaluation, and payload hashing logic must run deterministically in unit test suites without external network dependencies.
2. **Deterministic Mocking for AI Validation:** LLM inference is tested in CI/CD using deterministic mock fixtures and schema validation tests to prevent flaky, expensive third-party API calls.
3. **Time-Travel Saga Validation:** Multi-day Temporal recovery sagas are validated in milliseconds using Temporal's in-memory test environment.

---

## 2. Unit Testing (The Deterministic Core)

The deterministic core components are tested using **Pytest** and native **Rego OPA CLI** test runners, targeting 100% code coverage.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      DETERMINISTIC UNIT TEST SUITE                       │
├───────────────────┬──────────────────────────────────────────────────────┤
│ Test Domain       │ Assertions & Target Behaviors                        │
├───────────────────┼──────────────────────────────────────────────────────┤
│ Revenue Risk      │ • Accurate paise-to-INR conversion (299900 ──► ₹2999)│
│ Engine            │ • Correct risk tier assignment (HIGH > ₹5k, etc.)    │
│                   │ • Priority score calculation logic                   │
├───────────────────┼──────────────────────────────────────────────────────┤
│ Diagnosis         │ • Mapping BAD_REQUEST + insufficient_funds ──► NSF   │
│ Engine            │ • Mapping GATEWAY_ERROR + timeout ──► SWITCH_TIMEOUT │
│                   │ • Hard decline detection (expired_card ──► Hard=True)│
├───────────────────┼──────────────────────────────────────────────────────┤
│ OPA Governance    │ • RULE-001: 4 retries ──► BLOCKED (Max 3 breaches)   │
│ (Rego Tests)      │ • RULE-002: < 24h gap ──► BLOCKED (Cooldown breach)  │
│                   │ • RULE-003: Terminal failure retry ──► BLOCKED       │
│                   │ • RULE-005: Missing pre-debit notice ──► BLOCKED     │
└───────────────────┴──────────────────────────────────────────────────────┘
```

---

## 3. AI Agent Validation (Testing the Probabilistic Layer)

To prevent CI pipeline flakiness and control token expenses during buildathon development, LLM integration is tested through bounded schema fixtures and fallback assertions.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         AI GUARDRAIL TEST MATRIX                         │
├───────────────────────────────────┬──────────────────────────────────────┤
│ Mocked AI Condition               │ Expected System Behavior             │
├───────────────────────────────────┼──────────────────────────────────────┤
│ Valid JSON + High Confidence      │ Passes validation ──► Forwards to OPA│
│ Invalid Action ENUM ("REFUND_ALL")│ Pydantic Exception ──► Safe Fallback │
│ Confidence Score < 0.80 (e.g. 0.74)│ Guardrail Trigger ──► ESCALATE_HUMAN│
│ Malformed / Free-text Response    │ Schema Error ──► Static Rules Engine │
└───────────────────────────────────┴──────────────────────────────────────┘
```

### Key AI Test Scenarios
1. **Schema Integrity Test:** Inject valid candidate JSON plans; assert successful Pydantic deserialization into `ProposedRecoveryPlan`.
2. **Adversarial Schema Rejection:** Inject malformed LLM responses containing invalid ENUM values or hallucinated fields; assert that Pydantic validation catches the exception and immediately invokes `DeterministicFallbackActivity`.
3. **Low Confidence Floor Test:** Mock an LLM response returning `confidence_score: 0.74`; assert that the system overrides the action and transitions the workflow state to `ESCALATED_TO_HUMAN`.

---

## 4. Integration & Workflow Testing

Integration tests validate component interactions, API authentication, and long-running saga orchestration.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    INTEGRATION & TIME-TRAVEL TESTS                       │
├──────────────────────────┬───────────────────────────────────────────────┤
│ Integration Target       │ Verification Methodology                      │
├──────────────────────────┼───────────────────────────────────────────────┤
│ Webhook Ingestion        │ • Valid HMAC signature ──► HTTP 200 OK        │
│ API Perimeter            │ • Forged HMAC signature ──► HTTP 401          │
│                          │ • Corrupted JSON body ──► HTTP 400            │
├──────────────────────────┼───────────────────────────────────────────────┤
│ Temporal Workflow Saga   │ • Execute `RecoverySagaWorkflow` in           │
│ (Time-Travel Testing)    │   `temporalio.testing.WorkflowEnvironment`    │
│                          │ • Fast-forward 72-hour sleep in 5 milliseconds │
│                          │ • Assert activity order: Ingest ──► Risk ──►  │
│                          │   Diagnose ──► AI ──► OPA ──► Execute ──► Audit│
└──────────────────────────┴───────────────────────────────────────────────┘
```

### Time-Travel Testing Methodology
Using Temporal's `WorkflowEnvironment.start_time_skipping()`, the integration test suite simulates multi-day recovery loops instantaneously:
1. Trigger `RecoverySagaWorkflow` with a synthetic NSF payment failure payload.
2. The workflow calculates risk, diagnoses NSF, gets a 72-hour retry proposal, passes OPA governance, and enters `workflow.sleep(timedelta(hours=72))`.
3. The test runner fast-forwards virtual time by 72 hours in under $10\text{ms}$.
4. Assert that the workflow wakes up, executes `DispatchRazorpayActionActivity` with the correct idempotency key, and commits the audit receipt to `immudb`.

---

## 5. Chaos Engineering & Failure Injection

Chaos testing proves that the system remains resilient under infrastructure faults, network partitioning, and external API downtime.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     CHAOS FAULT INJECTION SUITE                          │
├───────────────────────────────────┬──────────────────────────────────────┤
│ Injected Fault Scenario           │ Expected System Resilience Behavior  │
├───────────────────────────────────┼──────────────────────────────────────┤
│ Razorpay API 503 / Network Timeout│ Temporal retries activity with       │
│                                   │ exponential backoff (2s..60s). Zero  │
│                                   │ duplicate charges dispatched.        │
├───────────────────────────────────┼──────────────────────────────────────┤
│ Duplicate Webhook Replay          │ Unique constraint on `event_id` drops│
│ (Same event_id injected twice)    │ duplicate payload. Single saga runs. │
├───────────────────────────────────┼──────────────────────────────────────┤
│ Worker Process Crash (SIGKILL)    │ Temporal worker pool recovers state  │
│ during active 48h sleep timer     │ on secondary node. Timer fires on    │
│                                   │ schedule without event loss.         │
└───────────────────────────────────┴──────────────────────────────────────┘
```

### Detailed Chaos Test Cases
1. **External Gateway Timeout Injection:** Mock the Razorpay `POST /v1/invoices/{id}/retry` API to return `HTTP 503 Service Unavailable` for 3 consecutive attempts before returning `200 OK`. Assert that Temporal's `SYSTEM_ACTIVITY_RETRY_POLICY` retries the activity with exponential backoff and succeeds on attempt 4 without creating duplicate payment links or invoices.
2. **Duplicate Webhook Attack:** Inject identical `payment.failed` webhook payloads simultaneously across 10 concurrent HTTP worker threads. Assert that database primary key locks and Redpanda consumer group partition deduplication ensure exactly **one** recovery saga is spawned.
3. **Hard Worker Termination (SIGKILL):** Kill the execution worker process while a recovery saga is waiting on an OPA evaluation or sleeping for 24 hours. Spawn a fresh worker process; assert that the saga resumes state seamlessly from the Temporal event history log.

---

## 6. Document Metadata & Sign-off

* **Author:** Fintech System Architect & QA Lead / Track 3 Team  
* **Target Buildathon:** Razorpay AI Buildathon — Track 3 (AI Revenue Recovery)  
* **Upstream Specification:** `docs/01-problem-statement.md`, `docs/03-system-architecture.md`, `docs/09-governance-and-policies.md`, `docs/10-recovery-workflows.md`, `docs/14-security.md`  
* **Implementation Artifacts:** `docs/15-testing-strategy.md`  
