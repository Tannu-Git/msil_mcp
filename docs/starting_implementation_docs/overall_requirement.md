# MSIL Composite MCP Server – Detailed Technical Solution (Internal Working Document – Nagarro)

**Purpose of this document**
This is a **technical solution blueprint** for Nagarro teams to design, build, and demo a **Composite MCP Server** integrated with MSIL’s AWS-based API Manager (APIM) using **OpenAPI-driven tool generation**, meeting **Stage-1 deliverables** and passing **Stage-2 technical demo** (service booking). It is written for internal alignment and will be later distilled into the formal RFP response.

---

## 0. RFP Scope Snapshot (What is explicitly required)

### In scope

* Convert **309 APIs** into **30+ MCP Products** (final number decided during implementation). 
* Use **Composite MCP Server architecture** (ref Fig 2.3). 
* **Tool-first workflows auto-derived from OpenAPI/Swagger**; **no model training and no RAG**. 
* **Minimal/zero static coding**: bind dynamically to OpenAPI; tool definitions automatically update when API specs change. 
* **Security-by-design + governance**: OAuth2/OIDC, RBAC (incl. PIM/PAM), central registration/discovery, observability + audit.  
* **Containerized deployment**, CI/CD integration, observability integration. 

### Stage-2 demo (gating)

* Live demo: generic service booking prompt; MCP client discovers tools via composite MCP server; handles dynamic inputs and completes end-to-end transaction. 
* MSIL validates by DB entry check, code tracing (guardrails + invocation logic), dashboards + audit logs; confirms zero static coding behavior. 

### Additional inputs from MSIL call (non-RFP but direction)

* Discard PII where applicable (esp. logs/traces/telemetry).
* Improve journeys/product boundaries; recommend better API Product segregation.
* LLM selection configurable (any LLM ok for demo).
* MCP server publicly accessible “with security”.
* Focus: service booking with ~9 mandatory input parameters; can derive from user or other APIs; governance must not affect existing apps.

> **Note**: These call inputs are treated as **constraints/preferences**; where not explicitly in RFP, we label them as **Client Direction / Assumption** in the relevant sections.

---

## 1. Proposed Target Architecture (AWS-hosted, Composite MCP Pattern)

### 1.1 Architecture principles (from RFP design principles)

* **Composite MCP servers tailored to journeys** to minimize tool sprawl and reduce token burn, while preserving central governance (registry/admin/policy) and AAA. 
* Treat each API Product as a purposeful tool bundle owned by a domain; register centrally for governed discovery and lifecycle control. 
* Security-by-design: OAuth2/OIDC, RBAC/PIM/PAM, schema validation, allow/deny lists, secrets isolation, output sanitization, rate-limit parity with API manager. 
* Observability/audit: tamper-evident trails; standardized logs/metrics/traces; dashboards. 
* Minimal development: OpenAPI-driven generation, reusable templates/modules, repeatable blueprint. 

### 1.2 “MCP Product” clarification (internal terminology alignment)

* **APIM API Product (MSIL/APIM):** Logical grouping of backend APIs published via MSIL APIM.
* **MCP “Product” (RFP language):** A governed **bundle of MCP tools** that represents a business journey/product (e.g., “Service Booking”) mapped to APIM APIs.
* **MCP Runtime (our implementation):** The MCP server software that exposes those tools and calls APIM.

**Key implementation choice (minimal effort):**
We build **one reusable MCP runtime** and represent “30+ MCP Products” as **configuration + registry entries (tool bundles)** rather than 30 bespoke codebases. This matches “minimal development effort” expectations. 

---

## 2. Diagram Placeholders (to be produced separately)

> Replace each placeholder with a diagram in the final internal pack and later proposal.

1. **[DIAGRAM-01] HLD – Composite MCP Logical Architecture**

   * MCP client → Composite MCP Gateway → MCP tool bundles → MSIL APIM → backend systems
     *(Ref: Fig 2.3 composite concept)* 

2. **[DIAGRAM-02] LLD – MCP Runtime Component Diagram**

   * tool definition layer, routing engine, validation modules, caching, observability stack 

3. **[DIAGRAM-03] Security Architecture – OAuth2/OIDC + RBAC + PIM/PAM + Policy Flow** 

4. **[DIAGRAM-04] Deployment Architecture – AWS (EKS/ECS), environments (Dev/QA/Prod), DR/BCP** 

5. **[DIAGRAM-05] Tool Lifecycle – OpenAPI → Tool generation → Registry publish → Approval gates → Deploy** 

6. **[DIAGRAM-06] Observability & Audit – Logs/metrics/traces + dashboards + WORM audit store**  

7. **[DIAGRAM-07] Service Booking E2E Sequence Diagram (Stage-2 demo)** 

---

## 3. Detailed Solution Design

### 3.1 Core components (LLD description)

#### A) Composite MCP Gateway (Entry MCP endpoint)

**Responsibilities**

* Expose a single MCP endpoint for clients (demo agent/chat UI).
* Enforce **AuthN/AuthZ**, policy decision point, allow/deny lists.
* Apply rate-limits aligned with APIM policy (parity). 
* Route tool calls to the correct **tool bundle** (MCP Product) and execution module.

**Implementation options (AWS)**

* Containerized gateway (EKS/ECS) behind ALB/NLB
* Optional WAF at edge (public access requirement from call note)
* mTLS internal between gateway and executor modules (recommended)

#### B) MCP Registry + MCP Admin (Governance plane)

**Responsibilities**

* Central tool discovery & lifecycle control (RFP requires central registration/discovery). 
* Store:

  * list of MCP products (tool bundles)
  * tool schemas (generated)
  * versioning (OpenAPI version → tool bundle version)
  * approvals/release gates (Dev→QA→Prod)
  * ownership & metadata (domain, sensitivity)

**Minimal-effort approach**

* Start with a lightweight registry implementation:

  * a metadata service + storage (e.g., DynamoDB/RDS) + admin UI/CLI
  * or integrate into existing internal tooling if available
* Scale to enterprise registry later (future-phase), but keep interfaces stable.

#### C) Tool Definition Generator (OpenAPI-driven)

**Responsibilities**

* Parse OpenAPI/Swagger; derive:

  * tool name / description
  * input JSON schema from parameters + requestBody schemas
  * output schema from responses
  * error models & examples
* Enforce “schema-first validation” and avoid bespoke parsing. 

**Update model (“zero static coding”)**

* Tool bundle auto-updates when OpenAPI changes: achieved via CI/CD pipeline triggers + registry publish. 

> **Clarification to confirm with MSIL**: Whether runtime-pull of OpenAPI is required or CI/CD-driven regeneration satisfies “automatic updating”. RFP requires the behavior, not the mechanism. 

#### D) Tool Execution Engine (APIM invoker)

**Responsibilities**

* Execute a tool call by invoking MSIL APIM endpoint.
* Apply:

  * request validation (strict schema)
  * response shaping (compact payloads, selective fields) 
  * retries/timeouts/circuit breakers
  * caching (idempotent reads only) 
* Attach correlation IDs for traceability.

#### E) Policy & Guardrails Module (Security & agent safety)

**Responsibilities**

* Enforce allow/deny lists per tool and per role. 
* Prompt-injection guardrails & safe execution:

  * strict schema validation
  * tool selection constraints (only expose necessary tool packs to clients)
  * output sanitization
  * secrets isolation 
* Support PIM/PAM integration model (as required). 

#### F) Observability & Audit subsystem

**Responsibilities**

* Logs/metrics/traces for tool invocations + policy decisions; dashboards for reviewers. 
* Audit logs retained 12 months (explicit). 
* Tamper-evident trails (explicit). 

**WORM storage pattern (AWS)**

* Use S3 Object Lock (Governance/Compliance mode) or equivalent immutability pattern for audit records.

---

## 4. Token Efficiency & “Claude-style MCP best practices” (applied pragmatically)

> The RFP explicitly calls out token burn and tool sprawl. 
> This is production-grade best practice and directly improves demo success.

### 4.1 Tool sprawl control

* Only publish/enable the **ServiceBooking tool bundle** for Stage-2 demo.
* Keep tool names intent-aligned: `GetNearbyDealers`, `GetSlots`, `CreateServiceBooking`. 
* Avoid exposing raw CRUD endpoints as tools unless needed.

### 4.2 Context minimization

* Short tool descriptions; avoid dumping full OpenAPI into prompts.
* Return compact responses (only fields required for next step). 
* Support selective fields and pagination with hard limits.

### 4.3 Execution discipline

* Structured tool calls only; reject natural-language “freeform” execution.
* Server-side constraints: small inputs, partial responses, selective fields. 

---

## 5. Security Architecture (RFP-mandated)

### 5.1 Identity & access

* OAuth2/OIDC at the MCP Gateway. 
* RBAC with optional PIM/PAM enforcement for privileged operations. 

### 5.2 Tool-level authorization

* Role-based tool visibility and execution:

  * “discover” permission
  * “invoke” permission
* Allowlists/denylists managed centrally via registry/admin.

### 5.3 Input validation & injection resistance

* Strict schema validation for every request. 
* Reject:

  * additionalProperties when not allowed
  * invalid enum values
  * oversized payloads
* Validate response schema too (detect backend anomalies).

### 5.4 Secrets isolation

* Secrets stored in Secrets Manager/KMS; never logged; never returned to client. 

### 5.5 PII handling (Client Direction)

* Mask/discard PII in:

  * logs/traces/events
  * dashboards
  * audit payload fields (store minimal identifiers needed for traceability)
* Ensure service-booking success still verifiable in DB check (MSIL will validate DB entry). 

### 5.6 Rate limiting parity with APIM

* Enforce parity limits at MCP gateway; also use dedicated APIM consumer identity for MCP traffic. 

---

## 6. Deployment Architecture (AWS, containerized, HA/DR-ready)

RFP explicitly calls for containerization, CI/CD integration, env segregation (Dev/QA/Prod), and DR/BCP strategy. 

### 6.1 Recommended AWS deployment (baseline)

* **Compute:** EKS (preferred for platform extensibility) or ECS Fargate (faster to stand up for demo)
* **Ingress:** ALB/NLB + WAF (if public access required)
* **Network:** VPC with private connectivity to MSIL APIM where mandated
* **Config:** Parameter Store/Secrets Manager
* **Audit store:** S3 Object Lock (WORM)
* **Observability:** CloudWatch + OpenTelemetry exporter (or MSIL’s stack)

### 6.2 HA/Resilience controls (production-grade)

* Multi-AZ deployment for gateway + runtime
* HPA/auto scaling on CPU/RPS/latency
* Timeouts, retries, circuit breakers to APIM
* Bulkheads: isolate tool packs / critical flows from noisy neighbors

### 6.3 DR/BCP (to be sized per MSIL targets)

* **Assumption:** DR targets (RTO/RPO) to be confirmed.
* Provide DR options:

  * warm standby cross-region for critical gateway
  * or IaC-based rebuild with data replication for audit store

---

## 7. Service Booking – Stage-2 Demo Implementation Plan

Stage-2 requires service booking prompt, tool discovery + invocation, dynamic inputs, DB validation, code tracing, dashboards/audit logs. 

### 7.1 Service Booking “tool bundle” (example structure)

**Inputs (expected):** date, time, mobile no, vehicle registration no, location/dealer, etc. 
**Tool set** (actual names will align to OpenAPI):

1. `ResolveCustomer` (mobile → customer context)
2. `ResolveVehicle` (vehicle reg → vehicle context)
3. `ResolveGeo` (location → lat/long) *(if required)*
4. `GetNearbyDealers` (lat/long → dealers)
5. `GetSlots` (dealer + date/time window → available slots)
6. `CreateServiceBooking` (transactional booking)
7. `GetBookingStatus` or `GetBookingDetails` (confirmation)

> These correspond directly to RFP’s example intent-aligned methods and server-side constraints. 

### 7.2 Orchestration strategy (minimal assumptions)

* MCP server does **not** implement business logic beyond:

  * validation
  * sequencing for required inputs
  * calling APIM endpoints
  * handling failures/retries safely

**Approach for missing inputs**

* If prompt missing required fields:

  * return a structured “missing_fields” response to client OR
  * invoke “resolve” APIs if available (per call notes “get it from user or other APIs”)

> This is a demo-critical behavior: the prompt can vary. 

### 7.3 Demo storyboard (what we will execute live)

1. Start MCP client (agent/chat UI).
2. Enter prompt: “Book a service appointment for tomorrow at 10 AM …” 
3. Client discovers tools via composite MCP server. 
4. Client calls tools sequentially with structured outputs; handles dynamic inputs. 
5. Booking created → capture booking ID.
6. MSIL validates:

   * DB record exists 
   * code trace shows guardrails and correct tool invocation 
   * dashboards show invocations/errors/policy decisions; audit logs captured 
7. Show “zero static coding” evidence:

   * explain how tool schema is generated from OpenAPI and updates via pipeline; show latest tool version metadata. 

---

## 8. Minimal Development Effort Strategy (how we achieve it)

RFP explicitly calls for minimal development effort via OpenAPI-driven generation and reusable templates/modules. 

### 8.1 What is coded once (platform)

* MCP protocol handling
* OpenAPI parser + tool generator
* validator
* APIM invoker (common HTTP client, retries, timeouts)
* policy enforcement module
* observability + audit integration
* CI/CD templates + security scans

### 8.2 What is configured (per MCP Product/tool bundle)

* which OpenAPI specs and which operations are included
* tool naming conventions + descriptions
* response shaping rules (field selection, compaction)
* auth policies + allow/deny lists
* caching rules for specific read tools

### 8.3 Outcome

* Onboarding a new MCP Product becomes:

  1. add/update OpenAPI
  2. update config defining tool bundle boundaries
  3. pipeline regenerates & publishes
  4. registry approves to environment

That is the “repeatable enablement blueprint” asked by MSIL. 

---

## 9. DevSecOps, Testing, and Release Gates

### 9.1 DevSecOps assets required (Stage-1)

* CI/CD pipeline artifacts: SAST/DAST, dependency/IaC scans. 
* Unit/integration tests; negative test cases: unauthorized access, malformed requests, injection attempts. 

### 9.2 Recommended pipeline stages (internal baseline)

1. Build & unit tests
2. SAST + dependency scan
3. Container image build + image scan
4. IaC validation + IaC scanning
5. Integration tests against APIM dev environment (mock if access limited)
6. DAST (where feasible)
7. Deploy to Dev → smoke tests
8. Promote to QA/Prod via approvals (release gates)

### 9.3 Test strategy

* **Contract tests:** OpenAPI contract validations (tool schema vs API schema).
* **Negative tests:** role-based denies, malformed schemas, injection patterns.
* **Resilience tests:** timeouts, APIM throttling behavior, retry safety.
* **PII redaction tests:** ensure logs/audits redact sensitive fields.

---

## 10. Observability & Audit Design (Stage-1 + Stage-2 evidence)

RFP requires structured logs/metrics/traces, dashboards, and tamper-evident audit trails. 

### 10.1 Telemetry model (must-have events)

For each tool call:

* correlation_id
* tool_name + tool_version
* caller identity (redacted/minimized)
* policy decision (allow/deny + reason)
* request size + response size (no payload bodies unless safe)
* latency, status code
* downstream APIM request id (if available)

### 10.2 Dashboards (minimum for Stage-2)

* tool invocation count by tool
* error rates by tool
* p95 latency by tool
* policy denies by reason
* throttle/rate-limit events

### 10.3 Audit retention & immutability

* 12-month retention is explicit. 
* Tamper-evident trails required. 
* Use WORM-capable store (S3 Object Lock) + lifecycle policies.

---
