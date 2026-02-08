# ChatGPT Admin Portal Review - Gap Analysis & Remediation

**Date:** February 7, 2026  
**Review Source:** ChatGPT Feature Verification  
**Status:** Analysis Complete - 10 Issues Identified

---

## EXECUTIVE SUMMARY

ChatGPT identified 10 gaps between documentation claims and actual implementation. **3 are CRITICAL for RFP**, 4 are MODERATE, 3 are LOW/COSMETIC.

| Issue | Severity | Status | Owner | ETA |
|-------|----------|--------|-------|-----|
| 1. Enforcement Not Wired End-to-End | 🔴 CRITICAL | ⏳ Partial | Backend | 2 days |
| 2. Dashboard KPIs Missing Real Data | 🟠 CRITICAL | ✅ Mostly Done | Backend | 4 hours |
| 3. Tools Risk Fields Not Enforced | 🟠 CRITICAL | ❓ TBD | Backend | 4 hours |
| 4. OpenAPI Import Overstated | 🟠 MODERATE | ✅ As Implemented | UI/Docs | 1 hour |
| 5. Policies Permission Model Semantic Issues | 🟠 MODERATE | ✅ As Designed | Docs | 2 hours |
| 6. Exposure Wording: "See & Access" vs "See Only" | 🟡 MODERATE | ✅ Fixable | Docs | 1 hour |
| 7. Audit Logs PII Leakage Risk | 🟡 MODERATE | ⚠️ Partial | Backend | 1 day |
| 8. Settings Page Over-Scoped for RFP | 🟡 MODERATE | ✅ Disable Unimplemented | UI | 2 hours |
| 9. Service Booking Not Wired to Backend | 🟡 MODERATE | ⏳ UI-Only | Backend | 1 day |
| 10. Missing Features List in Shared Doc | 🟡 LOW | ✅ Move to Internal | Docs | 30 min |

---

## ISSUE 1: ENFORCEMENT NOT WIRED END-TO-END 🔴 CRITICAL

### What ChatGPT Found

> "tools/call and chat tool calls are not passing user_id/user_roles, so exposure checks are bypassed. OPA/policy engine isn't invoked in actual execution."

### Actual Status

**PARTIALLY IMPLEMENTED:**

✅ **Backend Infrastructure EXISTS:**
- `ExposureManager` class created with `filter_tools()` method
- `PolicyEngine` class created with OPA integration
- `handle_tools_list()` contains exposure filtering logic
- `RiskPolicyManager` handles tool risk enforcement
- Exposure permissions stored in database
- Policy roles and permissions defined

❌ **INTEGRATION GAPS:**
1. **tools/list**: Exposure filtering is in code BUT may not be wired in actual request path
   - File: `mcp-server/app/api/mcp.py` line 186
   - Code exists: `exposure_manager.filter_tools(all_tools, user_id, roles)`
   - **ISSUE**: User context extraction may not happen 100% consistently

2. **tools/call**: Policy enforcement exists BUT:
   - Risk policy manager evaluates (`_evaluate_risk_policy()`)
   - BUT rate limiting not enforced at executor level
   - Elevation requirements not enforced at gate

3. **Chat endpoint**: May not extract user context properly
   - File: `mcp-server/app/api/chat.py`
   - Need to verify RequestContext is passed through

### Evidence

**Code References:**
```python
# Line 186 in mcp.py - Exposure filtering exists:
exposed_tools = await exposure_manager.filter_tools(
    all_tools, user_id, roles
)

# Line 110 in executor.py - Risk evaluation exists:
decision = await self.policy_engine.evaluate(
    action="invoke",
    resource=tool.name,
    context=context
)
```

**BUT documentation says:**
- PHASE1_STATUS.md lists this as "Partial" implementation
- IMPLEMENTATION_PLAN.md Phase 2 shows "Exposure + Policy Enforcement" as future task
- Suggests code may exist but integration not complete

### What Needs to Happen

**OPTION A: Verify Integration Works (2 hours)**
```
1. Test tools/list with user context → returns only exposed tools
2. Test tools/call with unexposed tool → returns 403
3. Test tools/call with write tool, operator role → enforces policy
4. Test chat with user context → respects exposure + policy
5. Update status docs to mark as COMPLETE
```

**OPTION B: Complete the Integration (2-4 hours)**
```
1. Ensure RequestContext extracted in mcp_handler() 
2. Ensure exposure_manager.filter_tools() called in tools/list
3. Ensure policy_engine.evaluate() called before executor.execute()
4. Ensure rate_limiting enforced at executor
5. Ensure elevation gating for privileged tools
6. Add enforcement toggle in Settings with warning banner
7. Wire chat endpoint to use RequestContext
8. Wire all errors to audit logging
```

### UI Impact

**CRITICAL:** The Policies and Exposure Governance pages WILL mislead admins if enforcement doesn't work.

**FIX NEEDED:**
- Add enforcement status banner at top of admin portal
  ```
  ⚠️ Policy Enforcement Status:
  - Authentication: ✅ Enabled
  - Policy Engine (OPA): [✅/❌]
  - Exposure Filtering: [✅/❌]  
  - Rate Limiting: [✅/❌]
  - Audit Logging: [✅/❌]
  ```

---

## ISSUE 2: DASHBOARD KPIs SHOWING PLACEHOLDER DATA 🔴 CRITICAL

### What ChatGPT Found

> "Dashboard claims 'Real-time system monitoring' with KPIs and live refresh. But KPIs are probably showing placeholders."

### Actual Status

**PARTIALLY DONE:**

✅ **Infrastructure in Place:**
- `MetricsCollector` class exists with real tracking
- Analytics API endpoints created (`/metrics/summary`, `/metrics/tools-usage`, etc.)
- Dashboard fetches from `GET /api/analytics/metrics/summary`
- "Live Data" badge displays on dashboard

❌ **Data Issues:**
```python
# In analytics.py line 47:
"total_conversations": 0,  # TODO: Track conversations
"last_hour": 0,  # TODO: Time-filtered metrics
```

The code HAS TODOs for:
1. **total_conversations** - Not tracked (Chat metrics not integrated)
2. **last_hour metric** - Should show requests in last 60 mins, shows 0
3. **last_24_hours** - Probably not filtered correctly

### Evidence

**Dashboard.tsx line 80:**
```tsx
<span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
Live Data
```
The "Live Data" badge suggests real-time, but metrics are partially synthetic.

### What Needs to Happen (4 hours)

1. **Implement Conversation Tracking**
   ```python
   # In chat.py - track chat messages
   metrics_collector.record_conversation_start(user_id, session_id)
   metrics_collector.record_conversation_end(session_id)
   ```

2. **Implement Time-Filtered Metrics**
   ```python
   # In metrics_collector.py
   def get_recent_requests(self, minutes: int = 60) -> List[Dict]:
       # Filter executions by timestamp
       recent_executions = [
           e for e in self._execution_log
           if (datetime.utcnow() - e["started_at"]).total_seconds() < (minutes * 60)
       ]
       return recent_executions
   ```

3. **Fix Dashboard Data Source**
   - Remove "Live Data" badge IF metrics are not truly live
   - OR complete the time-filtering to make it truly live
   - OR replace badge with "Updated every 30s" to be accurate

4. **Update Metrics Aggregation**
   - Ensure metrics_collector.record_execution() is called EVERY time a tool runs
   - Currently may only record in success path, need to record failures too

---

## ISSUE 3: TOOL RISK FIELDS EXIST BUT NOT ENFORCED 🔴 CRITICAL

### What ChatGPT Found

> "Tools form includes risk level, requires_elevation/confirmation/approval, concurrency, rate-limit tier. But those fields must feed runtime behavior - they don't yet."

### Actual Status

**PARTIALLY DONE:**

✅ **Fields Defined:**
- Tool dataclass has: `requires_elevation`, `requires_confirmation`, `requires_approval`, `rate_limit_tier`
- Risk policy manager exists with evaluation logic
- Admin UI allows editing these fields

❌ **Enforcement Gaps:**
1. **requires_elevation** - Field exists, but elevation gate NOT implemented
   - Where: Executor should check if tool requires elevation AND user is elevated
   - Missing: No "is_elevated" check in RequestContext → executor path

2. **requires_confirmation** - Field exists, but confirmation gate NOT implemented
   - Where: Should return special response requiring user confirmation before execution
   - Missing: No confirmation flow in MCP protocol or executor

3. **requires_approval** - Field exists, but approval gate NOT clear
   - Similar issue to requires_confirmation

4. **rate_limit_tier** - Field exists, enforcement unclear
   - Risk manager can GET the tier, but rate limiter may not USE it
   - File: `mcp-server/app/core/policy/risk_policy.py` line 151
   - Method: `get_rate_limit_multiplier(tier)` exists BUT...
   - Need to verify rate limiter calls this method

5. **max_concurrent_executions** - Field may not be enforced
   - Need semaphore/lock to track concurrent executions per tool

### Evidence

```python
# In registry.py - Fields defined:
requires_elevation: bool = False
requires_confirmation: bool = False
requires_approval: bool = False
rate_limit_tier: str = "standard"

# In risk_policy.py - Evaluation logic:
needs_elevation = policy.requires_elevation and not is_elevated

# BUT: No evidence this gate is in the actual request path
```

### What Needs to Happen (4 hours)

**Priority 1: Implement Elevation Gate**
```python
# In executor.execute()
if tool.requires_elevation and not context.is_elevated:
    raise InsufficientElevationError(
        f"Tool '{tool_name}' requires PIM elevation. User is not elevated."
    )
```

**Priority 2: Implement Confirmation Flow**
```python
# Response format for tools requiring confirmation
if tool.requires_confirmation:
    return {
        "status": "confirmation_required",
        "tool_name": tool_name,
        "confirmation_required": True,
        "risk_level": tool.risk_level,
        "message": "This is a privileged operation. Customer confirmation required.",
        "confirmation_timeout_seconds": 300
    }
```

**Priority 3: Wire Rate Limit Tier**
```python
# In rate_limiter.py
multiplier = risk_policy_manager.get_rate_limit_multiplier(tool.rate_limit_tier)
effective_limit = base_limit / multiplier  # Stricter for "strict" tier
```

**Priority 4: Implement Max Concurrency**
```python
# In executor.py
_concurrent_executions: Dict[str, int] = {}

async def execute(self, tool_name: str, ...):
    if _concurrent_executions.get(tool_name, 0) >= tool.max_concurrent_executions:
        raise TooManyConcurrentExecutionsError(...)
    
    _concurrent_executions[tool_name] = _concurrent_executions.get(tool_name, 0) + 1
    try:
        return await ... # execute
    finally:
        _concurrent_executions[tool_name] -= 1
```

### UI Impact

The **Tools page** shows these fields as editable, but admins may configure them thinking they're enforced when they're not.

**FIX NEEDED:**
- Add visual indicator: "🟡 Enforced: Not Yet" or "✅ Enforced: Yes"
- Add help text: "Elevation requirements are enforced. Rate limits not yet enforced."
- Disable fields that aren't enforced (or make them read-only)

---

## ISSUE 4: OPENAPI IMPORT - "URL IMPORT / PASTE CONTENT" OVERSTATED 🟠 MODERATE

### What ChatGPT Found

> "Doc says import supports file upload, URL import, paste content. Also says tool names derived from operationId. May be over-stated."

### Actual Status

**PARTIALLY CORRECT:**

✅ **Implemented:**
- File upload via `@router.post("/upload")` in `openapi_import.py`
- Supports YAML and JSON files
- Parses OpenAPI 3.0/3.1 and Swagger 2.0
- Generates tool names from operationId (fallback: path + method)

❌ **NOT Implemented:**
- URL import - No endpoint for `POST /import/from-url` or `?url=...`
- Paste content - No endpoint for `POST /import/paste`
- Only file upload works

### Evidence

```python
# openapi_import.py lines 76-100
@router.post("/upload")  # ← Only this endpoint exists
async def upload_openapi_spec(
    file: UploadFile = File(...),  # ← File required parameter
    ...
):
    # URL import / paste NOT supported
```

### What to Correct in Documentation

**Current (WRONG):**
```markdown
**Upload Methods:**
1. **File Upload** - Drag & drop or click to browse
2. **URL Import** - Paste URL to spec (if supported) ← MISLEADING
3. **Paste Content** - Direct text paste (if supported) ← MISLEADING
```

**Corrected (RIGHT):**
```markdown
**Upload Methods:**
1. **File Upload** - Drag & drop or click to browse ✅ IMPLEMENTED
   - Supported: JSON, YAML
   - Specifications: OpenAPI 3.0, 3.1, Swagger 2.0

**Future Methods (Not Yet Implemented):**
- URL Import - Coming in Phase 2
- Paste Content - Coming in Phase 2
```

**Timing:** 1 hour to update docs

---

## ISSUE 5: POLICIES PAGE - PERMISSION MODEL NEEDS CLARITY 🟠 MODERATE

### What ChatGPT Found

> "Permission patterns defined as `action:resource:subresource`. If OPA not enforced, these are config-only. Need clear semantics: what does `invoke:*` mean for tools vs admin?"

### Actual Status

**IDENTIFIED AMBIGUITY:**

The permission model is documented but semantic rules are implicit, not explicit:
- `invoke:*` - Can invoke any tool? OR invoke any admin action?
- `read:*` - Can read what? Tools, configs, audit logs?
- `admin:*:*` - Full admin or just admin tool actions?

### Evidence

```python
# In policy/engine.py line 21
self.simple_rules = {
    "admin": ["*"],  # Wildcard - does everything
    "developer": [
        "invoke:*",  # Tools? Admin actions? Both?
        "read:*",    # What specifically?
        "write:tool",
        "write:config"
    ],
    "operator": [
        "invoke:*",
        "read:*"
    ]
}
```

### What Needs to Happen (2 hours)

1. **Create Permission Schema Document**
   ```markdown
   # Permission Pattern Reference
   
   ## Admin Permissions
   - admin:tools:create - Create new tools
   - admin:tools:update - Edit tool properties
   - admin:tools:delete - Deactivate tools
   - admin:policies:write - Manage roles and permissions
   - admin:exposure:write - Manage tool visibility
   - admin:settings:write - Change system settings
   - admin:audit:read - View audit logs
   
   ## Tool Invocation Permissions
   - invoke:* - Invoke any tool
   - invoke:bundle:{name} - Invoke tools in bundle
   - invoke:tool:{name} - Invoke specific tool
   
   ## Read Permissions
   - read:tools - View tool list and schemas
   - read:audit - View audit logs
   - read:metrics - View analytics dashboard
   ```

2. **Add Validation to Policies Page**
   ```typescript
   // In admin-ui/src/components/policies/PermissionInput.tsx
   const VALID_PATTERNS = [
     'admin:*:*',
     'admin:tools:create',
     'admin:policies:write',
     'invoke:*',
     'invoke:bundle:*',
     'invoke:tool:*',
     'read:*',
     'read:audit'
   ]
   
   if (!VALID_PATTERNS.some(p => permission.match(wildcardRegex(p)))) {
     showError("Invalid permission pattern. Use admin:*, invoke:*, read:*, etc.")
   }
   ```

3. **Add Help Text in UI**
   - Hover tooltip on "Add Permission" button
   - Link to permission reference guide
   - Examples in modal

**Timing:** Add to Policies page UI (2 hours)

---

## ISSUE 6: EXPOSURE GOVERNANCE WORDING - "SEE & ACCESS" vs "SEE ONLY" 🟡 MODERATE

### What ChatGPT Found

> "Doc says 'Tools that [role] can see and access'. But your definition says exposure is visibility only, separate from authorization. Important mismatch."

### Actual Status

**DOCUMENTATION BUG:**

Current text suggests exposure controls both visibility AND authorization:
```
"see and access"
```

Should say:
```
"see (discover)"
```

Exposure = visibility (Layer B)  
Authorization = execution permission (Layer A)

### Evidence

Feature doc line 1063:
```markdown
**Description:**
"Tools that [role] can see and access"  ← WRONG
```

Should be:
```markdown
**Description:**
"Tools that [role] can discover (see in tools/list)"
"Actual execution permission is managed separately in Policies"
```

### What Needs to Happen (1 hour)

1. Update ADMIN_PORTAL_FEATURES_VERIFICATION.md line 1063
   ```markdown
   OLD: "Tools that [role] can see and use access"
   NEW: "Tools visible to [role] in tools/list (based on exposure permissions). Execution rights determined separately by policies."
   ```

2. Add info box to Exposure page preview panel
   ```
   ℹ️  Exposure Governance (Layer B - Discovery)
   Shows which tools appear in tools/list for this role.
   
   Actual execution permission (Layer A - Authorization) is controlled separately
   in the Policy Engine and depends on:
   - User role and permissions
   - Tool risk level
   - PIM elevation status
   ```

3. Update Settings > Explanation text
   ```markdown
   OLD: "Exposure checks enabled"
   NEW: "Tool visibility filtering enabled (tools/list layer)"
   ```

**Timing:** 1 hour to update docs + UI text

---

## ISSUE 7: AUDIT LOGS - PII LEAKAGE & RETENTION ISSUES 🟡 MODERATE

### What ChatGPT Found

> "Showing request/response bodies risky (PII leakage). Stack traces unacceptable for clients. Also retention says '90 days' but RFP requires '12 months'."

### Actual Status

**MULTIPLE ISSUES:**

1. **Retention Period Wrong**
   - Doc says: "default: 90 days"
   - RFP requires: "12 months (365 days)"
   - Fix: Change everywhere

2. **PII Masking Incomplete**
   - No evidence of masking in code
   - Docs mention masking in passing but unclear if implemented
   - File to check: `mcp-server/app/core/audit/logger.py`

3. **Stack Traces in Expanded Rows**
   - Doc claims: "Stack trace (if error)" in expandable row
   - RISK: Leaks internal paths, versions, implementation details
   - Should NOT expose raw stack traces

### Evidence

```python
# In audit logger - no masking visible
def log_event(self, event_data: Dict):
    # Just logs raw data?
    logger.info(f"Audit: {event_data}")
```

Settings page shows:
```
**Retention Days** (number input)
- Default: 90 days ← WRONG, should be 365
```

### What Needs to Happen (1 day)

**Priority 1: Fix Retention Default (30 min)**
```python
# In settings/defaults
AUDIT_RETENTION_DAYS: int = 365  # Changed from 90
```

Update UI:
```tsx
// In Settings.tsx
defaultValue={365}  // Changed from 90
label="Retention Days (default: 12 months)"
```

**Priority 2: Implement PII Masking (4 hours)**
```python
# In audit/logger.py
def mask_pii(value: Any) -> str:
    """Mask sensitive data for audit logs"""
    if isinstance(value, str):
        if re.match(r'\d{10}', value):  # Phone
            return value[:3] + '***' + value[-2:]
        elif '@' in value:  # Email
            return value[0] + '***@' + value.split('@')[1]
        elif len(value) > 10:  # Generic field
            return value[:3] + '***' + value[-2:]
    return str(value)

# Usage:
audit_log = {
    "user_id": mask_pii(request.user.id),  # "user@***"
    "customer_mobile": mask_pii("9876543210"),  # "987***10"
    "tool_input": mask_pii(args)  # Mask nested values
}
```

**Priority 3: Remove Stack Traces from Expanded Rows (2 hours)**

Update doc:
```markdown
OLD: 
  - Stack trace (if error)
  - Full request body
  - Full response body

NEW:
  - Error message (redacted)
  - Policy decision and reason
  - Tool name and version
  - Execution status and latency
  - User context (roles, client ID)
```

Remove from UI:
```tsx
// AuditLogs.tsx - Remove from expandable row:
// {/* <JsonViewer data={row.request_body} /> */}  ← DELETE
// {/* <JsonViewer data={row.response_body} /> */}  ← DELETE
// {/* <JsonViewer data={row.stack_trace} /> */}     ← DELETE

// Keep only safe fields:
{event.correlation_id}
{event.policy_decision}
{event.tool_name}
{event.execution_time_ms}
{event.user_context.roles}
```

**Timing:** 1 day total

---

## ISSUE 8: SETTINGS PAGE OVER-SCOPED FOR RFP 🟡 MODERATE

### What ChatGPT Found

> "Settings tab list is extremely broad (WAF settings, container security, backup & recovery, feature flags, etc.). Looks like you're promising a fully configurable platform product. Many toggles likely do nothing today."

### Actual Status

**OVER-PROMISED:**

Current Settings has 6 tabs with 100+ configuration options.  
Estimated ACTUAL implementation: 30-40% of settings work.

**Analysis:**
- ✅ General (servers, log levels, timezone) - Likely implemented
- ✅ Security (JWT, OPA URL) - Partially implemented
- ⚠️ LLM/AI (model selection) - UI only, no backend wiring
- ⚠️ API Gateway (MSIL APIM config) - Partial
- ❌ Performance (caching, rate limits, circuit breaker) - No evidence
- ❌ Advanced (container security, network policies, backups, SSO) - Definitely NOT for MVP

### Evidence

Comments in Settings.tsx and docs show:
```typescript
// Many settings have no backend endpoint
// They just update local state and "save" to nowhere
// Or POST to endpoints that don't exist
```

### What Needs to Happen (2 hours)

**Recommended Approach for RFP:**

**REDUCE Settings to Essentials (MVP):**

```markdown
## Recommended Settings for RFP MVP

### Tab 1: General (KEEP)
- Host/Port
- Log level (DEBUG/INFO/WARNING)
- Timezone
- Demo mode toggle

### Tab 2: Security (SIMPLIFY - keep only working)
- OAuth2/OIDC enabled + URL
- JWT expiry
- OPA server URL  
- Audit enabled + retention days (365)

### Tab 3: API Integration (NEW - simpler)
- API Gateway Mode (Mock / MSIL APIM)
- APIM Connection String
- API Key

### Tabs 4-6: REMOVE from client demo
- Move "LLM/AI", "Performance", "Advanced" → Internal admin only
- Or disable with "Coming soon" if needed for demo

### Future Settings (Comment out / Disable)
- Container security
- WAF rules  
- Backup recovery
- Feature flags
- Security testing
- Observability config
- mTLS/network policies
```

**Action Items:**

1. **Disable Unimplemented Settings (1 hour)**
   ```typescript
   // In Settings.tsx - add feature flag checks
   
   {FEATURE_FLAGS.LLM_SETTINGS_ENABLED && (
     {renderLLMTab()}
   )}
   
   {FEATURE_FLAGS.PERFORMANCE_SETTINGS_ENABLED ? (
     {renderPerformanceTab()}
   ) : (
     <div className="bg-gray-50 p-4 rounded"
       <p className="text-gray-500">Coming in next phase</p>
     </div>
   )}
   ```

2. **Add "Unimplemented" Banner (30 min)**
   ```tsx
   <div className="bg-yellow-50 border border-yellow-200 p-4 rounded mb-6">
     <p className="text-yellow-800 font-semibold">
       ⚠️ Some settings are not yet implemented in this MVP.
       Settings marked "Coming soon" will be available in future releases.
     </p>
   </div>
   ```

3. **Update RFP Scope Document**
   ```markdown
   # Admin Portal - RFP MVP Scope
   
   ## Implemented
   - General settings (host, port, log level)
   - Authentication (OAuth2, JWT)
   - Audit configuration
   - API Gateway mode (Mock/APIM)
   
   ## Available But Limited
   - LLM model selection (UI only, not exposed to chat)
   - OPA policy engine (configuration only)
   
   ## Future Phases (Not in MVP)
   - Performance tuning (caching, rate limits)
   - Container orchestration (security contexts, limits)
   - Advanced compliance (backup recovery, secret scanning)
   - Network policies (mTLS, WAF, IP restrictions)
   ```

**Timing:** 2 hours

---

## ISSUE 9: SERVICE BOOKING NOT WIRED TO BACKEND 🟡 MODERATE

### What ChatGPT Found

> "Wizard exists and completes end-to-end, doc suggests wiring tools in sequence (email/SMS). But it's likely front-end only. Also email/SMS scope creep."

### Actual Status

**UI IS COMPLETE:**

✅ 4-step wizard with form validation
✅ Confirmation screen with booking ID
✅ Local state management

❌ **NOT WIRED TO BACKEND:**
- No API endpoint to save booking
- No email/SMS integration
- No actual tool calling

### What to Do (Depends on RFP Scope)

**OPTION A: Keep as Demo-Only (Recommended for MVP) - 30 min**

```markdown
### 3.7 SERVICE BOOKING (`/service-booking`)

**Purpose:** Demonstrate multi-step workflow UI (not production-ready)

**Status:** Demo/Mockup only. Does not save bookings or call tools.

**Features:**
...
```

**OPTION B: Wire to Backend (1-2 days)**

1. Create backend endpoint
   ```python
   @router.post("/api/admin/bookings")
   async def create_booking(request: BookingRequest):
       # Save to database
       # Call MCP tools:
       #   1. validate_vehicle
       #   2. get_dealer_details
       #   3. check_availability
       #   4. create_booking
       # Return booking ID
   ```

2. Wire UI to endpoint
   ```typescript
   const response = await fetch('/api/admin/bookings', {
       method: 'POST',
       body: JSON.stringify(formData)
   })
   const { booking_id } = await response.json()
   ```

3. Remove email/SMS claims (NOT in RFP scope)

**Recommendation:** Document as demo-only in RFP. Don't over-promise email/SMS.

**Timing:** 30 min (document as demo-only)

---

## ISSUE 10: MISSING FEATURES LIST IN SHARED DOCUMENT 🟡 LOW

### What ChatGPT Found

> "The 'Missing Features' section contains items (workflow builder, API playground, multi-tenancy). In a bid context, these trigger scope questions."

### Actual Status

Current doc (ADMIN_PORTAL_FEATURES_VERIFICATION.md) shows section 9:
```markdown
## 9. MISSING FEATURES (NOT YET IMPLEMENTED)

For complete transparency, the following features are planned but not yet visible:
1. Real-time Notifications
2. User Management Page
3. Multi-tenancy
... (10 items)
```

**PROBLEM:** External LLM or customer reading this might ask:
- "When will you deliver workflow builder?"
- "Is multi-tenancy required?"  
- "Can we get user management now?"

### What to Do (30 min)

**SOLUTION: Move to Internal Docs Only**

1. **Delete from ADMIN_PORTAL_FEATURES_VERIFICATION.md** section 9
   - This is for external/customer review
   - Remove roadmap items

2. **Create Internal Document** `ROADMAP.md`
   ```markdown
   # MSIL MCP Admin Portal - Product Roadmap (INTERNAL ONLY)
   
   **Not for customer/RFP distribution**
   
   ## Phase 2 (Q2 2026)
   - User management (create/edit/delete admin users)
   - Real-time notifications (WebSocket)
   - Tool versioning and history
   - Bulk operations (export/import roles, policies)
   
   ## Phase 3+ (Future)
   - Workflow builder (visual tool chaining)
   - API playground (test tools directly)
   - Multi-tenancy (separate customer isolates)
   - Advanced analytics (custom reports)
   ```

3. **Update ADMIN_PORTAL_FEATURES_VERIFICATION.md**
   - End with: "This completes the MVP feature set for Phase 1."
   - No mention of future items

**Timing:** 30 min to move and update docs

---

## REMEDIATION CHECKLIST

### Immediate Actions (This Session)

- [ ] **Issue 1** - Verify enforcement wiring OR create fix list
- [ ] **Issue 2** - Complete dashboard time-filtered metrics (4 hours)
- [ ] **Issue 3** - Implement elevation gate + rate limit tier enforcement (4-6 hours)
- [ ] **Issue 4** - Update FEATURES doc (1 hour) - CRITICAL  
- [ ] **Issue 5** - Add permission schema to Policies page (2 hours)
- [ ] **Issue 6** - Fix "see and access" → "see only" wording (1 hour)
- [ ] **Issue 7** - Fix retention to 365 days, implement PII masking (1-2 days)
- [ ] **Issue 8** - Disable unimplemented Settings tabs (1-2 hours)
- [ ] **Issue 9** - Document Service Booking as demo-only (30 min)
- [ ] **Issue 10** - Delete missing features section, create roadmap.md (30 min)

### By End of Week

- [ ] All enforcement functional (tools/list, tools/call, policy, exposure)
- [ ] Dashboard KPIs show real data
- [ ] Tool fields (elevation, confirmation, rate limits, concurrency) enforced
- [ ] Audit logs properly configured (365 day retention, PII masked)
- [ ] Settings reduced to MVP scope
- [ ] Documentation accurate for RFP

---

## NEXT STEPS

1. **Run this checklist with team**
2. **Prioritize Critical issues** (1, 2, 3)
3. **Set owner and ETA for each**
4. **Update all documentation** with fixes
5. **Final verification** by external review

---

**Document Version:** 1.0  
**Prepared:** February 7, 2026  
**Status:** Ready for remediation
