# Deployment, Infrastructure & Production Readiness Specification
**Project:** Razorpay AI Buildathon (Track 3)  
**Document ID:** `docs/16-deployment.md`  
**Status:** Approved Architectural Baseline  

---

## Executive Summary

This document specifies the deployment architecture, container orchestration, cloud hosting topologies, CI/CD automation pipelines, and infrastructure observability stack for the **AI Revenue Recovery Agent**. Designed with a dual-path deployment philosophy, the system supports zero-configuration single-command execution (`docker-compose up`) for rapid hackathon demonstration while providing a cloud-native, lift-and-shift path to Kubernetes (EKS/GKE) capable of processing enterprise transaction volumes ($1\text{M+ TPS}$).

---

## 1. Overview & Dual-Path Deployment Philosophy

Fintech systems must balance speed of initial delivery with long-term architectural scalability.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         DUAL-PATH DEPLOYMENT STRATEGY                    │
├───────────────────────────────────┬──────────────────────────────────────┤
│ Hackathon / Demo MVP Path         │ Enterprise Production Rollout Path   │
├───────────────────────────────────┼──────────────────────────────────────┤
│ • 1-Command Docker Compose local  │ • Kubernetes (EKS/GKE) HPA Auto-scale│
│ • Local Redpanda + PostgreSQL     │ • Managed Confluent Kafka + Aurora DB│
│ • Free-tier PaaS (Render/Vercel)  │ • Temporal Cloud + OPA DaemonSets    │
│ • Instant live judge URL access   │ • Multi-AZ 99.999% High Availability │
└───────────────────────────────────┴──────────────────────────────────────┘
```

1. **Hackathon Path (Zero-Friction MVP):** Fully containerized microservices suite orchestrated locally via Docker Compose, with option for instant PaaS deployment (Vercel + Render) to provide hackathon judges with a live public URL.
2. **Enterprise Path (Cloud-Native Production):** Stateless worker pods, managed databases, event streaming clusters, and sidecar governance proxies deployed on Kubernetes with auto-scaling triggers.

---

## 2. Local & Hackathon Deployment (The MVP)

### 2.1 Containerized Microservices Stack (`docker-compose`)
The local setup runs 7 lightweight containerized services in a isolated bridge network:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   DOCKER COMPOSE LOCAL TOPOLOGY                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [ React + Vite Dashboard ] ──► [ FastAPI Ingestion & Management Backend ]│
│                                       │                                  │
│            ┌──────────────────────────┼──────────────────────────┐       │
│            ▼                          ▼                          ▼       │
│     [ Redpanda Queue ]      [ Temporal Server + UI ]    [ OPA Engine ]   │
│            │                          │                          │       │
│            └──────────────────────────┼──────────────────────────┘       │
│                                       ▼                                  │
│                           [ PostgreSQL & immudb ]                        │
└──────────────────────────────────────────────────────────────────────────┘
```

| Service Container | Technology Base | Internal Network Port | Description |
| :--- | :--- | :--- | :--- |
| `frontend` | React + Vite (Nginx) | `3000` | Finance Controller Dashboard UI |
| `api-server` | FastAPI (Uvicorn) | `8000` | Webhook listener & Management REST APIs |
| `temporal-worker` | Python Worker SDK | `N/A` (Internal) | Executes Temporal activity tasks & sagas |
| `redpanda` | Redpanda (Kafka-compatible)| `9092` | High-throughput event streaming bus |
| `temporal` | Temporal Server | `7233` / `8233` (UI) | Durable workflow state engine |
| `postgres` | PostgreSQL 16 | `5432` | Operational transactional datastore |
| `immudb` | immudb Server | `3322` | Cryptographic append-only audit ledger |
| `opa` | Open Policy Agent (Wasm)| `8181` | Policy evaluation engine sidecar |

### 2.2 Environment Configuration Injection (`.env`)
All sensitive credentials and test keys are injected securely via environment variables:
```bash
# Razorpay Test Credentials
RAZORPAY_KEY_ID=rzp_test_mock_1234567890
RAZORPAY_KEY_SECRET=secret_test_mock_9876543210
RAZORPAY_WEBHOOK_SECRET=whsec_test_mock_signature_key

# AI & Observability Keys
OPENAI_API_KEY=sk-proj-mock-openai-key
LANGFUSE_PUBLIC_KEY=pk-lf-mock-key
LANGFUSE_SECRET_KEY=sk-lf-mock-key
LANGFUSE_HOST=https://cloud.langfuse.com

# Database Connection URIs
POSTGRES_URI=postgresql://admin:password@postgres:5432/recovery_db
IMMUDB_URI=immudb://admin:password@immudb:3322/audit_db
```

### 2.3 Cloud Hosting Path for Live Judge Demonstration
* **Frontend:** Deployed to **Vercel** (`https://recovery-agent.vercel.app`).
* **Backend APIs & Workers:** Deployed to **Render / Railway** running containerized FastAPI.
* **Database:** **Supabase Managed PostgreSQL** for operational state indexing.

---

## 3. Enterprise Production Architecture (The Razorpay Scale)

To scale to millions of daily recurring transactions, the architecture transitions to a cloud-native Kubernetes environment:

```mermaid
graph TD
    subgraph Public_Ingress["Network Perimeter & Global CDN"]
        LB["AWS ALB / Cloudflare WAF"]
    end

    subgraph EKS_Cluster["Kubernetes Cluster (EKS/GKE)"]
        subgraph Ingestion_Pods["Ingestion Auto-Scaling Group"]
            API1["FastAPI Pod 1"]
            API2["FastAPI Pod N"]
        end

        subgraph Worker_Pods["Worker Auto-Scaling Group"]
            W1["Temporal Worker Pod 1"]
            W2["Temporal Worker Pod N"]
        end

        subgraph Governance_DaemonSet["Governance Sidecars"]
            OPA1["OPA Sidecar 1"]
            OPA2["OPA Sidecar N"]
        end
    end

    subgraph Managed_Cloud_Services["Enterprise Managed Cloud Layer"]
        MSK[("AWS MSK / Confluent Kafka")]
        AURORA[("Amazon Aurora Multi-AZ Postgres")]
        TEMP_CLOUD["Temporal Cloud Engine"]
        IMMU_CLOUD[("Enterprise immudb Cluster")]
    end

    LB --> API1
    LB --> API2
    API1 --> MSK
    API2 --> MSK
    MSK --> W1
    MSK --> W2
    W1 <--> TEMP_CLOUD
    W2 <--> TEMP_CLOUD
    W1 --> OPA1
    W2 --> OPA2
    W1 --> AURORA
    W2 --> AURORA
    W1 --> IMMU_CLOUD
    W2 --> IMMU_CLOUD
```

### Enterprise Component Specifications
1. **Compute (AWS EKS / Google GKE):** Stateless FastAPI and Temporal Worker pods auto-scale using Horizontal Pod Autoscalers (HPA) triggered by CPU utilization and Kafka queue consumer lag.
2. **Streaming Bus (Confluent Cloud / AWS MSK):** Managed multi-broker Kafka cluster with partition replication factor 3.
3. **Operational Database (Amazon Aurora PostgreSQL):** Multi-AZ deployment with automated failover and read replicas supporting $10,000+\text{ IOPS}$.
4. **Workflow Orchestration (Temporal Cloud):** Fully managed, SOC2-certified Temporal Cloud instance guaranteeing sub-millisecond state persistence and 99.99% SLA.
5. **Governance Sidecars:** OPA running as a local container sidecar within each worker Pod, eliminating cross-network RPC latency during policy evaluation.

---

## 4. Continuous Integration & Deployment (CI/CD)

The GitHub Actions pipeline automates testing, validation, and container registry publishing:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        CI/CD AUTOMATION PIPELINE                         │
├──────────────────────────────────────────────────────────────────────────┤
│ Push to `main` branch                                                    │
│ ├── Stage 1: Pytest Unit & Deterministic Integration Tests               │
│ ├── Stage 2: OPA Rego Policy Syntax & Rule Validation (`opa test`)       │
│ ├── Stage 3: Container Build & Vulnerability Scan (Trivy Scanner)        │
│ └── Stage 4: Publish OCI Container to AWS ECR / GitHub Packages          │
│     └── Stage 5: Continuous Deployment to Staging Environment            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Infrastructure Observability & Telemetry

Production monitoring ensures complete visibility over system health, queue latencies, and LLM financial expenses:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      OBSERVABILITY TELEMETRY STACK                       │
├──────────────────────────┬───────────────────────────────────────────────┤
│ Telemetry Component      │ Function & Target Metric                      │
├──────────────────────────┼───────────────────────────────────────────────┤
│ Prometheus               │ Metrics collection (HTTP SLAs, Queue Latency) │
│ Grafana Dashboards       │ Visual alerts for worker health & webhook lags│
│ Langfuse Platform        │ LLM token tracking, USD costs, Prompt Latency │
│ OpenTelemetry Tracing    │ Cross-microservice distributed tracing        │
└──────────────────────────┴───────────────────────────────────────────────┘
```

### 5.1 Key Production Grafana Alert Triggers
* **Webhook Processing Latency:** Alert if 99th percentile ingestion latency exceeds $100\text{ms}$.
* **Queue Consumer Lag:** Alert if Kafka consumer lag exceeds 500 unprocessed events.
* **OPA Policy Veto Spike:** Alert if OPA block rate exceeds 25% of total transactions (indicating potential upstream payload regression).
* **LLM Spend Cap:** Alert if daily LLM inference expense exceeds pre-configured budget cap ($\text{\$50.00 USD/day}$).

---

## 6. Document Metadata & Sign-off

* **Author:** Fintech System Architect & DevOps Lead / Track 3 Team  
* **Target Buildathon:** Razorpay AI Buildathon — Track 3 (AI Revenue Recovery)  
* **Upstream Specification:** `docs/01-problem-statement.md`, `docs/03-system-architecture.md`, `docs/05-api-contract.md`, `docs/14-security.md`, `docs/15-testing-strategy.md`  
* **Implementation Artifacts:** `docs/16-deployment.md`  
