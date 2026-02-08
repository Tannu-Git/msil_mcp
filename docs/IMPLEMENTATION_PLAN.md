Implementation Plan - Address Security, Governance, and Analytics Gaps

Date: 2026-02-07
Scope: MSIL MCP Server + Admin UI + Chat UI
Source: Code review gaps and validation checklist

Phase 0 - Alignment and Scope Freeze (0.5-1 day)
- Confirm which gaps are in-scope for the next demo/RFP defense and which are deferred.
- Define auth posture per environment (dev/demo/prod): AUTH_REQUIRED, DEMO_MODE, OIDC on/off.
- Confirm audit/analytics data sources (in-memory vs DB vs S3 WORM).
Deliverables:
- Approved scope list and environment policy matrix.
- Config flags list and defaults.

Phase 1 - Unified Request Context + Auth Enforcement (2-3 days)
Goal: All sensitive endpoints require a validated, consistent user context.
Tasks:
- Add RequestContext dataclass (user_id, roles, scopes, client_id, correlation_id, ip, env).
- Add FastAPI dependency get_request_context():
  - Extract correlation_id.
  - Validate JWT/OIDC based on config.
  - Reject missing/invalid tokens when AUTH_REQUIRED=true.
- Update MCP tools/list and tools/call to use RequestContext.
- Update Chat /api/chat/send to require RequestContext.
Acceptance:
- MCP tools/list/tools/call return 401 without token (when AUTH_REQUIRED=true).
- Chat /api/chat/send returns 401 without token (when AUTH_REQUIRED=true).
- Correlation ID consistent in logs and responses.

Phase 2 - Exposure + Policy Enforcement (2-4 days)
Goal: Visible tools and invoked tools are governed by exposure + policy.
Tasks:
- tools/list:
  - Filter by exposure permissions.
  - Apply policy engine for discovery (OPA/RBAC).
- tools/call:
  - Enforce exposure check.
  - Evaluate policy for invocation (risk tier, role, elevation requirement).
  - Standardize deny responses: 403 with reason code.
- Log policy decisions to audit.
Acceptance:
- Roles without expose:bundle:X cannot see bundle tools.
- Calling a non-exposed tool returns 403.
- OPA enabled: decisions enforced and logged; OPA disabled: RBAC enforced.
- Policy decisions appear in audit logs.

Phase 3 - Rate Limiting + Idempotency (2-3 days)
Goal: Protect downstream APIs and enforce consistent write behavior.
Tasks:
- Apply rate limiting in:
  - MCP tools/list
  - MCP tools/call
  - Chat tool execution
- Rate limit key: user_id/client_id + tool_name + risk tier.
- Return 429 with Retry-After.
- Wire Redis-backed IdempotencyStore into tool executor.
- Generate deterministic idempotency key for write/privileged tools.
Acceptance:
- 429 returned when limits exceeded.
- Repeated write with same idempotency key returns cached response.
- Rate-limit events appear in metrics.

Phase 4 - Audit Logging + PII Redaction (2-3 days)
Goal: Every tool execution and decision is auditable.
Tasks:
- Add audit logging in MCP tool invocation and Chat tool execution.
- Mask PII in inputs/results using existing masker.
- Use DB/S3 WORM when configured; in-memory only in demo/dev.
- Verify retention policy config (12 months default).
Acceptance:
- Every tools/call generates an audit record with correlation ID, tool, latency, outcome.
- When S3 enabled, events stored with object lock retention.
- Admin UI Audit Logs show real data.

Phase 5 - Analytics and UI Fixes (1-2 days)
Goal: Remove demo-breaking gaps.
Tasks:
- Fix analytics route registration for /metrics/recent-activity.
- Replace placeholder analytics with real metrics from collector/audit store.
- Fix Exposure UI API client wiring and verify end-to-end.
Acceptance:
- Dashboard charts show real data.
- Exposure page can list/modify permissions without errors.
- Recent activity endpoint returns actual executions.

Phase 6 - SSE Streaming Decision (1 day)
Goal: Align claims with implementation.
Option A: Wire SSE streaming into MCP tool/batch execution.
Option B: Remove streaming claims from demo/RFP.
Acceptance:
- If wired: endpoint streams progress updates.
- If not wired: no streaming claims.

Phase 7 - Test Coverage (2-4 days)
Goal: Prevent regressions and prove compliance.
Tests to add:
- Auth required for MCP/Chat.
- Exposure filtering in tools/list.
- Tool invocation denied when not exposed.
- Policy enforcement with OPA on/off.
- Rate limiting returns 429.
- Idempotency returns cached response.
- Audit record created per tool call.
Acceptance:
- Green test suite with coverage of all critical security paths.
