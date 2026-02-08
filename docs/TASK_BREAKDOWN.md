Task Breakdown - Detailed Implementation Steps

Date: 2026-02-07
Owner: MSIL MCP Team

Legend:
- FE = Admin UI / Chat UI
- BE = FastAPI MCP Server
- INF = Config/Infra
- TEST = Automated tests

Phase 1 - RequestContext + Auth Enforcement
1.1 BE - Add RequestContext module
- Add dataclass: user_id, roles, scopes, client_id, correlation_id, ip, env.
- Add helper to parse claims from JWT/OIDC.
- Add helper to normalize correlation_id.
Acceptance: RequestContext created consistently for each request.

1.2 BE - Add get_request_context dependency
- Validate JWT (local or OIDC) based on config.
- Support DEMO_MODE bypass when configured.
- Return 401 when AUTH_REQUIRED=true and token invalid/missing.
Acceptance: Auth enforced on target endpoints.

1.3 BE - Wire RequestContext in MCP
- tools/list uses RequestContext for filtering.
- tools/call uses RequestContext for authorization.
Acceptance: tools/list/tools/call fail without auth (when required).

1.4 BE - Wire RequestContext in Chat
- /api/chat/send requires RequestContext.
- Ensure correlation_id propagation.
Acceptance: chat endpoint fails without auth (when required).

Phase 2 - Exposure + Policy Enforcement
2.1 BE - Exposure filtering for tools/list
- Use exposure_manager.filter_tools with RequestContext roles/user_id.
- If no roles, return empty list (unless DEMO_MODE).
Acceptance: exposure rules applied.

2.2 BE - Policy evaluation for discovery
- Evaluate policy for tool discovery (OPA/RBAC).
- Return only allowed tools.
Acceptance: tool visibility aligns with policy decisions.

2.3 BE - Policy evaluation for invocation
- Evaluate risk tier + RBAC/OPA.
- Enforce privileged tool requirements (elevation/confirmation) if configured.
Acceptance: unauthorized invocation returns 403 with reason.

2.4 BE - Standardize error responses
- 401 unauthenticated, 403 unauthorized, 429 throttled, 400 invalid input.
- Include reason codes for denial.
Acceptance: consistent error format.

Phase 3 - Rate Limiting + Idempotency
3.1 BE - Apply rate limiting in MCP
- Check per-user and per-tool rate limits.
- Include risk tier multiplier.
- Return 429 with Retry-After.
Acceptance: throttling works.

3.2 BE - Apply rate limiting in Chat tool execution
- Use same limiter as MCP.
Acceptance: throttling works for chat tool calls.

3.3 BE - Wire IdempotencyStore
- Initialize with Redis and inject into ToolExecutor singleton.
- Generate deterministic idempotency keys for write tools.
Acceptance: identical write calls return cached response.

Phase 4 - Audit Logging + PII Redaction
4.1 BE - Audit logging for tools/call
- Log tool invocation with masked inputs/results.
- Include correlation_id, tool, latency, outcome.
Acceptance: audit entries appear in DB/S3 (when configured).

4.2 BE - Audit logging for Chat tool calls
- Same as MCP.
Acceptance: chat tool calls audited.

4.3 BE - Enforce retention policy
- Ensure S3 WORM is used when enabled; in-memory only in demo/dev.
Acceptance: retention defaults to 12 months.

Phase 5 - Analytics + UI Fixes
5.1 BE - Fix recent-activity route registration
- Move route definition out of nested function.
Acceptance: /api/analytics/metrics/recent-activity returns data.

5.2 BE - Replace placeholder analytics
- Use metrics_collector/audit logs instead of mock values.
Acceptance: dashboard charts reflect real usage.

5.3 FE - Fix Exposure UI API client wiring
- Replace missing apiClient with existing API wrapper.
Acceptance: Exposure UI works end-to-end.

Phase 6 - SSE Streaming Decision
6.1 BE - Implement SSE endpoint (optional)
- Add /mcp/stream endpoint and wire progress updates.
Acceptance: SSE demo works.

6.2 Docs - If not implemented, remove streaming claims.
Acceptance: no mismatch between claims and code.

Phase 7 - Tests
7.1 TEST - Auth enforcement
- MCP tools/list/tools/call returns 401 without auth.
- Chat endpoint returns 401 without auth.

7.2 TEST - Exposure filtering
- Verify tools/list returns only exposed tools.
- Verify tools/call fails if not exposed.

7.3 TEST - Policy enforcement
- OPA enabled vs disabled paths.
- Privileged tool requires elevation/confirmation if configured.

7.4 TEST - Rate limiting
- 429 and Retry-After enforced.

7.5 TEST - Idempotency
- Same write call returns cached response.

7.6 TEST - Audit logging
- Audit record created per tool call.

Deliverables
- Updated backend and UI code.
- Updated configs and environment flags.
- Test suite updates with passing results.
- Short demo runbook for pre-prod.
