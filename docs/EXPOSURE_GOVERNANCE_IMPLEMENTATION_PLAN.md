# Implementation Plan: Tool Exposure Governance

**Document Version**: 1.0  
**Date**: February 2, 2026  
**Status**: Ready for Implementation  
**Audience**: Development Team, Technical Leads, Project Managers

---

## Executive Summary

This document provides a concrete, phased implementation plan for adding **Tool Exposure Governance** to the MSIL MCP Server. This feature implements a two-layer security model:

- **Layer A (Authorization)**: Can user EXECUTE this tool? (existing, risk-based RBAC)
- **Layer B (Exposure)**: Can user SEE this tool in tools/list? (new, governance-based filtering)

This approach directly solves RFP requirements for "governed discovery" and "minimize tool sprawl" without requiring complex per-user entitlements.

**Total Effort**: ~27-28 hours across 3 weeks  
**Complexity**: Medium (new component, leverages existing patterns)  
**Risk Level**: Low (defense-in-depth, backward compatible)

---

## Table of Contents

1. [Phase Overview](#phase-overview)
2. [Phase 1: Core Exposure Model & Backend Filtering (Week 1)](#phase-1-core-exposure-model--backend-filtering-week-1)
3. [Phase 2: Admin UI for Exposure Management (Week 2)](#phase-2-admin-ui-for-exposure-management-week-2)
4. [Phase 3: Polish, Testing & Documentation (Week 3)](#phase-3-polish-testing--documentation-week-3)
5. [Full Implementation Timeline](#full-implementation-timeline)
6. [Implementation Checklist](#implementation-checklist-by-task)
7. [Key Design Decisions](#key-design-decisions-documented)
8. [Risk Mitigation](#risk-mitigation)

---

## Phase Overview

| Phase | Focus | Duration | Effort | Files |
|-------|-------|----------|--------|-------|
| **Phase 1** | Core exposure model + backend filtering | Week 1 | 8-10 hrs | 6 files |
| **Phase 2** | Admin UI for exposure management | Week 2 | 4-6 hrs | 4 files |
| **Phase 3** | Polish + documentation | Week 3 | 3-4 hrs | 17 docs |
| **Total** | Complete governance layer | 3 weeks | ~27-28 hrs | 27 files |

---

# PHASE 1: Core Exposure Model & Backend Filtering

## Task 1.1: Database Schema - Extend policy_role_permissions

**Objective**: Anchor exposure rules to existing policy tables instead of creating new entity

**Effort**: 1.5 hours  
**Files**: 1 (SQL migration)  
**Priority**: HIGH - Blocker for other tasks

**Approach**:
- Add new permission type prefix: `expose:*`
- No new tables in Phase 1 (reuse `policy_role_permissions`)
- Add migration script
- Seed initial exposure permissions

**Implementation Steps**:

1. Create migration file: `infrastructure/local/init-scripts/03-exposure-governance.sql`
2. Add permission examples in comments
3. Seed default exposure permissions for standard roles
4. Apply migration to local dev database

**Key Design Points**:
- ✅ Reuses existing `policy_role_permissions` table
- ✅ New permission types: `expose:bundle:*`, `expose:tool:*`, `expose:all`
- ✅ No schema changes to core tables
- ✅ Backward compatible: no exposure rules = user sees all tools

**Migration SQL Pattern**:
```sql
-- Insert exposure permissions for roles
INSERT INTO policy_role_permissions (role_id, permission)
SELECT r.id, 'expose:bundle:Service Booking'
FROM policy_roles r
WHERE r.name = 'operator'
ON CONFLICT DO NOTHING;
```

**Validation**:
- [ ] Migration applies without errors
- [ ] New permissions appear in policy_role_permissions table
- [ ] Query: `SELECT * FROM policy_role_permissions WHERE permission LIKE 'expose:%'` returns results

---

## Task 1.2: Backend - Create Exposure Manager Service

**Objective**: Centralized service for exposure resolution and filtering

**Effort**: 2.5 hours  
**Files**: 2 (manager.py + __init__.py)  
**Priority**: HIGH - Core component

**File**: `mcp-server/app/core/exposure/manager.py`

**Responsibilities**:
1. Resolve which tools user can see based on roles
2. Filter tool lists by exposure permissions
3. Check if specific tool is exposed to user
4. Cache exposure permissions for performance
5. Invalidate cache on policy changes

**Key Methods**:
- `get_exposed_tools_for_user(user_id, roles, client_application)` - Returns set of accessible tool names
- `_get_role_exposure_permissions(role_name)` - Query DB for role's expose:* permissions
- `_parse_exposure_permissions(permissions)` - Parse permission strings
- `filter_tools(all_tools, user_id, roles, client_application)` - Filter tool list
- `is_tool_exposed(tool_name, tool_bundle, exposed_refs)` - Quick boolean check
- `invalidate_cache(role_name)` - Clear cache for performance

**Permission Format**:
```
expose:bundle:Service Booking    → All tools in "Service Booking" bundle
expose:tool:resolve_customer     → Specific tool by name
expose:all                       → All tools (admin role)
```

**Example Logic**:
```python
# User has ["expose:bundle:Service Booking", "expose:tool:get_dealer"]
# Can see: all Service Booking tools + get_dealer (from Dealer Management)
```

**Caching Strategy**:
- Cache key: `role_name` (or combined if multiple roles)
- No TTL initially (invalidate on admin changes only)
- Cache hits logged at DEBUG level

**Files to Create**:
- Create: `mcp-server/app/core/exposure/manager.py`
- Create: `mcp-server/app/core/exposure/__init__.py`

**Validation**:
- [ ] File structure correct: `app/core/exposure/` exists
- [ ] ExposureManager class instantiable
- [ ] `get_exposed_tools_for_user()` returns set
- [ ] `filter_tools()` works with mock tool objects
- [ ] Cache updates on invalidate

---

## Task 1.3: Backend - Update tools/list Endpoint

**Objective**: Filter tools by exposure policy before returning to client

**Effort**: 1.5 hours  
**Files**: 1 (modify mcp.py)  
**Priority**: HIGH - User-facing change

**File**: `mcp-server/app/api/mcp.py`

**Changes to `handle_tools_list()` function**:
1. Accept user_id and roles parameters
2. Call `exposure_manager.filter_tools()`
3. Log exposure filtering result
4. Return filtered tool list
5. Include `bundle` metadata in response

**Changes to `mcp_handler()` function**:
1. Extract user context from JWT token
2. Pass user_id and roles to `handle_tools_list()`
3. Handle missing user context gracefully

**Response Format Update**:
```json
{
  "tools": [
    {
      "name": "resolve_customer",
      "description": "Resolve customer details",
      "inputSchema": {...},
      "bundle": "Service Booking"
    }
  ]
}
```

**Logging**:
```
[req-123] Exposure filter: 250 → 45 tools (user_id=usr_dev_001)
```

**Backward Compatibility**:
- If no user context: return all tools (fallback)
- If exposure rule missing: user sees all tools in that role
- No breaking changes to response schema

**Files to Modify**:
- Modify: `mcp-server/app/api/mcp.py`

**Validation**:
- [ ] tools/list endpoint still works
- [ ] Response includes `bundle` field
- [ ] Filtered count < total count
- [ ] Logs show exposure filtering

---

## Task 1.4: Backend - Add Exposure Check to tools/call

**Objective**: Defense-in-depth - verify tool is exposed before execution

**Effort**: 1 hour  
**Files**: 1 (modify executor.py)  
**Priority**: MEDIUM - Security hardening

**File**: `mcp-server/app/core/tools/executor.py`

**Changes**:
1. After tool lookup, before authorization check
2. Call `exposure_manager.is_tool_exposed()`
3. Raise `ToolNotExposedError` if not exposed
4. Log attempt to access unexposed tool

**Execution Order**:
```
Tool Lookup → Exposure Check → Authorization Check → Execution
```

**Error Handling**:
```python
raise ToolNotExposedError(
    f"Tool '{tool_name}' is not available in your tool catalog"
)
```

**Why Defense-in-Depth**:
- If exposure filter breaks, authorization still blocks
- If client bypasses tools/list, executor validates again
- Prevents accidental exposure of filtered tools

**Files to Modify**:
- Modify: `mcp-server/app/core/tools/executor.py`

**Validation**:
- [ ] tools/call works for exposed tools
- [ ] tools/call fails for non-exposed tools
- [ ] Error message is user-friendly
- [ ] Logs record exposure denial

---

## Task 1.5: Backend - Add Exception Classes

**Objective**: Create custom exceptions for exposure errors

**Effort**: 0.5 hours  
**Files**: 1 (modify exceptions.py or create)  
**Priority**: MEDIUM - Code organization

**New Exception Classes**:
```python
class ToolNotExposedError(Exception):
    """Tool is not in user's exposure set"""
    pass

class ExposureError(Exception):
    """Base class for exposure-related errors"""
    pass
```

**Usage**:
```python
if not is_exposed:
    raise ToolNotExposedError(f"Tool '{tool_name}' not exposed")
```

**Files to Create/Modify**:
- Create or Modify: `mcp-server/app/core/exceptions.py`

**Validation**:
- [ ] Exception classes importable
- [ ] Proper inheritance from Exception
- [ ] Caught correctly in error handlers

---

## Task 1.6: Backend - Create Admin API Endpoints for Exposure Management

**Objective**: CRUD endpoints for managing exposure permissions

**Effort**: 2 hours  
**Files**: 1 (modify admin.py)  
**Priority**: HIGH - Admin control

**File**: `mcp-server/app/api/admin.py`

**New Endpoints**:

### GET /admin/exposure/roles?role_name={role_name}
Get all exposure permissions for a role
```
Response:
{
  "role": "operator",
  "permissions": [
    "expose:bundle:Service Booking",
    "expose:tool:get_dealer"
  ]
}
```

### POST /admin/exposure/roles/{role_name}/permissions
Add exposure permission to role
```
Request:
{
  "permission": "expose:bundle:Service Booking"
}
```

### DELETE /admin/exposure/roles/{role_name}/permissions
Remove exposure permission from role
```
Query: ?permission=expose:bundle:Service Booking
```

### GET /admin/exposure/bundles
List all unique bundles from tools table
```
Response:
{
  "bundles": [
    "Service Booking",
    "Customer Management",
    "Dealer Operations"
  ]
}
```

### GET /admin/exposure/preview?role_name={role_name}
Preview what tools a role can see
```
Response:
{
  "role": "operator",
  "exposed_count": 45,
  "tools": [
    {
      "name": "resolve_customer",
      "bundle_name": "Service Booking",
      "display_name": "Resolve Customer"
    }
  ]
}
```

**Security**:
- All endpoints require `require_admin` dependency
- All requests logged with user_id
- Cache invalidated after changes

**Files to Modify**:
- Modify: `mcp-server/app/api/admin.py`

**Validation**:
- [ ] All endpoints return 200 OK
- [ ] POST updates database
- [ ] DELETE removes permissions
- [ ] Preview returns filtered list
- [ ] Admin-only (401 if not admin)

---

## Phase 1 Summary

**Deliverables**:
- ✅ Exposure manager service (fully functional)
- ✅ tools/list filtering integrated
- ✅ tools/call validation added
- ✅ Admin API endpoints for management
- ✅ Database migration applied
- ✅ Exception handling in place

**Testing Needed**:
- Manual: Curl/Postman tests for admin endpoints
- Manual: tools/list returns filtered results
- Manual: tools/call blocks unexposed tools

**Database State After Phase 1**:
```sql
-- policy_role_permissions contains:
('operator', 'expose:bundle:Service Booking')
('developer', 'expose:bundle:Service Booking')
('admin', 'expose:all')
```

**Next Phase Dependency**:
- Phase 2 Admin UI will build on these backend endpoints

---

# PHASE 2: Admin UI for Exposure Management

## Task 2.1: Admin UI - Create Exposure Management Page

**Objective**: New page for admins to configure tool exposure policies

**Effort**: 4-5 hours  
**Files**: 1 (Exposure.tsx)  
**Priority**: HIGH - Admin-facing feature

**File**: `admin-ui/src/pages/Exposure.tsx`

**Page Layout** (3-column):

```
┌────────────────────────────────────────────────────────────────┐
│ Tool Exposure Management                                       │
│ Control which tools each role can see and access              │
└────────────────────────────────────────────────────────────────┘

┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   Roles (Left)   │ │ Bundles (Center) │ │ Preview (Right)  │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│ ☑ operator       │ │ ☐ Service Bkng   │ │ 45 tools exposed │
│ ☑ developer      │ │ ☑ Cust Mgmt      │ │ • resolve_cust   │
│ ☑ admin          │ │ ☐ Dealer Ops     │ │ • get_slots      │
│                  │ │ ☐ Inventory      │ │ • create_booking │
│                  │ │                  │ │                  │
│                  │ │ [Add more tools] │ │ [SAVE] [PREVIEW] │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

**Key Features**:
1. **Role Selection** (left panel)
   - List all roles from policy_roles table
   - Click to select and load permissions
   - Highlight current selection

2. **Bundle Configuration** (center panel)
   - Checkbox list of available bundles
   - Check/uncheck to add/remove exposure
   - Shows current permission state
   - Toggle "Select All" option

3. **Tool Preview** (right panel)
   - Shows actual tools user would see
   - Name, bundle, display_name
   - Count of exposed tools
   - Scrollable list (max-height: 400px)
   - "Save" button to persist changes

**Component States**:
- Loading: Show spinner
- No Role Selected: "Select a role to configure"
- No Permissions: "This role sees all tools (no restrictions)"
- Unsaved Changes: Save button enabled
- Saving: Button shows "Saving..."
- Error: Alert with retry option

**Validation**:
- At least one bundle/tool must be exposed per role
- No invalid permission strings
- Confirm before overwriting existing permissions

**Files to Create**:
- Create: `admin-ui/src/pages/Exposure.tsx`

---

## Task 2.2: Admin UI - Update Router and Navigation

**Objective**: Add Exposure page to navigation menu

**Effort**: 0.5 hours  
**Files**: 2 (App.tsx, Navigation.tsx)  
**Priority**: MEDIUM - Navigation

**Changes to App.tsx**:
```typescript
import { Exposure } from '@/pages/Exposure'

// In routes:
{
  path: '/exposure',
  element: <Exposure />
}
```

**Changes to Navigation.tsx**:
```typescript
// Add menu item after Tools
<NavItem 
  to="/exposure" 
  icon={<Shield className="w-5 h-5" />}
  label="Tool Exposure"
  active={location.pathname === '/exposure'}
/>
```

**Files to Modify**:
- Modify: `admin-ui/src/App.tsx`
- Modify: `admin-ui/src/components/Layout/Navigation.tsx` or similar

**Validation**:
- [ ] Menu item appears in navbar
- [ ] Clicking navigates to /exposure
- [ ] Page loads without errors

---

## Task 2.3: Admin UI - Update API Client

**Objective**: Add API functions for exposure endpoints

**Effort**: 1 hour  
**Files**: 1 (api.ts)  
**Priority**: HIGH - Backend integration

**File**: `admin-ui/src/lib/api.ts`

**New Functions**:
```typescript
export async function fetchExposureConfig(roleName?: string)
export async function updateRoleExposure(roleName: string, permissions: string[])
export async function addExposurePermission(roleName: string, permission: string)
export async function removeExposurePermission(roleName: string, permission: string)
export async function listAvailableBundles()
export async function previewRoleExposure(roleName: string)
```

**Implementation**:
```typescript
export async function previewRoleExposure(roleName: string) {
  return api.get(`/admin/exposure/preview?role_name=${roleName}`)
}
```

**Error Handling**:
- Catch 401: User not admin
- Catch 404: Role not found
- Catch 500: Server error, show message

**Files to Modify**:
- Modify: `admin-ui/src/lib/api.ts`

**Validation**:
- [ ] All functions exist and are exported
- [ ] API calls match backend endpoint paths
- [ ] Error handling works

---

## Task 2.4: Admin UI - Add to Tools Page (Optional Enhancement)

**Objective**: Show exposure info on Tools page for quick reference

**Effort**: 1-2 hours  
**Files**: 2 (Tools.tsx, ToolList.tsx)  
**Priority**: LOW - Enhancement only

**Changes**:
1. In ToolList component, add bundle badge
2. Show which roles can see each tool (optional)
3. Link to Exposure page if user wants to modify

**Example Badge in ToolList**:
```tsx
{tool.bundle_name && (
  <span className="text-xs font-medium text-purple-600 bg-purple-50 px-2.5 py-1 rounded border border-purple-200">
    Bundle: {tool.bundle_name}
  </span>
)}
```

**Files to Modify**:
- Modify: `admin-ui/src/pages/Tools.tsx`
- Modify: `admin-ui/src/components/tools/ToolList.tsx`

**Note**: This is optional and can be skipped if time is limited.

---

## Phase 2 Summary

**Deliverables**:
- ✅ Exposure management page (fully functional)
- ✅ Role selection and bundle configuration UI
- ✅ Tool preview with live updates
- ✅ Navigation integration
- ✅ API client functions
- ✅ (Optional) Tools page enhancement

**Testing Needed**:
- Manual: Configure exposure for a role
- Manual: Preview shows correct tools
- Manual: Save persists to backend
- Manual: Logout/login, tools/list respects new exposure

**UI State After Phase 2**:
- Admin can see "Tool Exposure" menu item
- Admin can view/modify role exposure policies
- Preview shows affected tools in real-time

---

# PHASE 3: Polish, Testing & Documentation

## Task 3.1: Testing - Unit Tests

**Objective**: Test exposure manager logic in isolation

**Effort**: 2 hours  
**Files**: 1 (test_exposure_manager.py)  
**Priority**: HIGH - Quality assurance

**File**: `mcp-server/tests/test_exposure_manager.py`

**Test Cases**:
```python
test_filter_tools_by_bundle()
  # User has expose:bundle:Service Booking
  # Verify only Service Booking tools returned

test_filter_tools_by_tool_name()
  # User has expose:tool:get_dealer
  # Verify specific tool in result

test_mixed_toolkit_access()
  # User has ["expose:bundle:Service Booking", "expose:tool:get_dealer"]
  # Verify both Service Booking tools + get_dealer returned

test_admin_expose_all()
  # User has expose:all
  # Verify all tools returned

test_no_exposure_rules()
  # User has no expose:* permissions
  # Verify all tools returned (fallback behavior)

test_cache_hit()
  # Call twice with same roles
  # Verify cache hit on second call

test_cache_invalidation()
  # Add permission, invalidate cache
  # Verify new permission reflected
```

**Files to Create**:
- Create: `mcp-server/tests/test_exposure_manager.py`

**Validation**:
- [ ] All tests pass
- [ ] Coverage > 90%
- [ ] Run: `pytest tests/test_exposure_manager.py -v`

---

## Task 3.2: Testing - Integration Tests

**Objective**: Test exposure layer with real API endpoints

**Effort**: 1.5 hours  
**Files**: 1 (test_exposure_integration.py)  
**Priority**: MEDIUM - End-to-end validation

**File**: `mcp-server/tests/integration/test_exposure_integration.py`

**Test Cases**:
```python
test_tools_list_respects_exposure()
  # Setup: operator role has Service Booking exposure
  # Call: tools/list as operator
  # Assert: Only Service Booking tools returned

test_tools_call_blocked_if_not_exposed()
  # Setup: operator doesn't have Inventory exposure
  # Try: Call tool from Inventory bundle
  # Assert: ToolNotExposedError returned (403 or custom code)

test_admin_sees_all_tools()
  # Setup: admin has expose:all
  # Call: tools/list as admin
  # Assert: All tools returned

test_exposure_permission_add_reflected_in_list()
  # Setup: operator calls tools/list (sees 20 tools)
  # Call: admin adds Customer Management bundle to operator
  # Call: operator calls tools/list again
  # Assert: Now sees ~40 tools
```

**Files to Create**:
- Create: `mcp-server/tests/integration/test_exposure_integration.py`

**Validation**:
- [ ] All tests pass
- [ ] Run: `pytest tests/integration/test_exposure_integration.py -v`

---

## Task 3.3: Backend - Caching Layer

**Objective**: Cache exposure permissions to reduce DB queries

**Effort**: 1 hour  
**Files**: 1 (modify manager.py)  
**Priority**: MEDIUM - Performance

**Enhancement to ExposureManager**:
```python
async def get_exposed_tools_for_user(self, user_id: str, roles: List[str]):
    # Check cache
    cache_key = f"{':'.join(sorted(roles))}"
    if cache_key in self._exposure_cache:
        logger.debug(f"Cache hit for roles {roles}")
        return self._exposure_cache[cache_key]
    
    # Compute and cache
    exposed_tools = await self._compute_exposed_tools(roles)
    self._exposure_cache[cache_key] = exposed_tools
    
    return exposed_tools
```

**Cache Invalidation**:
- Call `invalidate_cache(role_name)` after admin changes
- Auto-invalidate in `add_exposure_permission()` and `remove_exposure_permission()`

**Performance Impact**:
- Baseline: ~50ms per tools/list (DB query)
- With Cache: ~1ms per tools/list (subsequent calls)
- Benefit: 50x faster for cached roles

**Files to Modify**:
- Modify: `mcp-server/app/core/exposure/manager.py`

**Validation**:
- [ ] Measure baseline query time
- [ ] Measure cached query time
- [ ] Verify >90% improvement

---

## Task 3.4: Backend - Audit Logging for Exposure Changes

**Objective**: Log when exposure permissions are modified

**Effort**: 1 hour  
**Files**: 1 (modify admin.py)  
**Priority**: MEDIUM - Compliance

**Changes to admin endpoints**:
```python
@router.post("/admin/exposure/roles/{role_name}/permissions")
async def add_exposure_permission(...):
    # ... add permission logic ...
    
    # Log audit event
    await audit_service.log_event(
        action="exposure_permission_added",
        user_id=current_user.user_id,
        details={
            "role": role_name,
            "permission": permission,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

**Audit Log Fields**:
- action: "exposure_permission_added" | "exposure_permission_removed"
- user_id: Admin who made change
- role: Role being modified
- permission: Permission being added/removed
- timestamp: When change happened
- ip_address: (from request context)

**Files to Modify**:
- Modify: `mcp-server/app/api/admin.py`

**Validation**:
- [ ] Audit logs appear in database
- [ ] Logs readable and complete
- [ ] Query: `SELECT * FROM audit_logs WHERE action LIKE 'exposure%' ORDER BY created_at DESC`

---

## Task 3.5: Documentation Updates

**Objective**: Update all documentation to reflect new exposure governance layer

**Effort**: 9-10 hours  
**Files**: 17 documentation files  
**Priority**: HIGH - Knowledge transfer

### Core Architecture Docs

#### 1. ARCHITECTURE_AND_DATA_STORAGE.md (4-5 sections)
Add sections:
- "Tool Exposure Governance" - Overview of two-layer model
- "Exposure Manager Component" - Architecture details
- "Permission Types" - Format of expose:* permissions
- "Exposure vs Authorization" - Layer distinction
- "Example Scenarios" - Various exposure configurations

Update sections:
- "Security Layers" - Add exposure as Layer 0
- "MCP Client Call Flow" - Add exposure filtering step

#### 2. architecture/02-low-level-architecture.md (new section)
Add sections:
- "Exposure Manager Component" - Class architecture
- "Sequence Diagrams" - tools/list with exposure filtering
- "Cache Management" - Caching strategy

#### 3. architecture/05-integration-architecture.md
Add section:
- "Admin UI - Exposure Management Integration"

### Developer Docs

#### 4. DEVELOPER_ONBOARDING.md (new section)
Add section:
- "Understanding Exposure Governance"
  - Two-layer model explanation
  - Permission types: expose:bundle:*, expose:tool:*, expose:all
  - Code examples for using exposure_manager
  - Testing exposure policies

#### 5. REQUEST_LIFECYCLE_DETAILED.md (update existing)
Update sections:
- Add Step 6.5: "Exposure Filtering (Layer B)"
- Show detailed flow: authentication → exposure filtering → authorization
- Add error scenarios: ToolNotExposedError

### Admin & User Docs

#### 6. admin/ADMIN_GUIDE.md (new section)
Add section:
- "Managing Tool Exposure & Catalogs"
  - Step-by-step guide to configure role exposure
  - Screenshot placeholders
  - Examples:
    - Assigning "Service Booking" bundle to operator
    - Creating mixed toolkit (multiple bundles)
    - Previewing what tools a role sees
  - Troubleshooting

#### 7. user/USER_GUIDE.md (new section)
Add section:
- "Why Do I See Certain Tools?"
  - Explain visibility is controlled by role assignment
  - Explain requesting new tool access
  - Link to admin contact

### Governance & Operations

#### 8. governance/01-team-structure.md
Add section:
- Responsibility matrix: "Tool Exposure Management"
- Who can create/modify exposure rules
- Approval workflows

#### 9. governance/02-templates.md
Add section:
- "Role Exposure Configuration Template"
- Examples:
  - operator_service_booking profile
  - developer_all_bundles profile
  - demo_limited profile

#### 10. operations/README.md
Add subsection:
- "Tool Exposure Governance Operations"
  - How to onboard new roles with exposure
  - How to rotate tool access
  - Troubleshooting exposure issues
  - Runbook for common tasks

#### 11. observability/README.md
Add metrics:
- tools_exposed_per_role (histogram)
- exposure_cache_hits / misses (counter)
- tool_not_exposed_errors (counter)

#### 12. devsecops/README.md
Add section:
- "Exposure Governance Defense-in-Depth"
  - Explain Layer A (Authorization) + Layer B (Exposure)
  - Test requirements for exposure
  - Security scanning for exposure leaks

### API Documentation

#### 13. api/README.md (new section)
Add section:
- "Exposure Management APIs"
  - All 5 new endpoints documented
  - Request/response examples
  - Error codes

### Artifacts & Concepts

#### 14. artefacts/01-mcp-tool-definition.md
Add section:
- "Bundle Metadata in Tool Definition"
- How bundle_name is used in filtering

#### 15. artefacts/02-composite-server.md
Update if relevant:
- How exposure affects tool bundling

### Support

#### 16. support/README.md
Add FAQ:
- "Why can't I see a tool?" (troubleshooting)
- "How do I request access to a tool?"
- "What's the difference between bundles and categories?"

### Infrastructure

#### 17. infrastructure/01-bom.md
Note:
- No new external dependencies required
- Only extends existing PostgreSQL schema

**Documentation Structure**:
```
docs/
├── EXPOSURE_GOVERNANCE_IMPLEMENTATION_PLAN.md  (this file)
├── ARCHITECTURE_AND_DATA_STORAGE.md  (update)
├── DEVELOPER_ONBOARDING.md  (update)
├── REQUEST_LIFECYCLE_DETAILED.md  (update)
├── admin/
│   └── ADMIN_GUIDE.md  (update)
├── user/
│   └── USER_GUIDE.md  (update)
├── support/
│   └── README.md  (update)
├── api/
│   └── README.md  (update)
├── architecture/
│   ├── 02-low-level-architecture.md  (update)
│   └── 05-integration-architecture.md  (update)
├── governance/
│   ├── 01-team-structure.md  (update)
│   └── 02-templates.md  (update)
├── operations/
│   └── README.md  (update)
├── devsecops/
│   └── README.md  (update)
├── artefacts/
│   ├── 01-mcp-tool-definition.md  (update)
│   └── 02-composite-server.md  (update)
├── observability/
│   └── README.md  (update)
└── infrastructure/
    └── 01-bom.md  (note)
```

**Files to Modify**: All 17 listed above

**Validation**:
- [ ] All files updated with new sections
- [ ] Links between docs verified
- [ ] No broken references
- [ ] Consistent terminology ("exposure", "bundle", "permission")
- [ ] Examples accurate and runnable

---

## Phase 3 Summary

**Deliverables**:
- ✅ Comprehensive unit tests
- ✅ Integration tests for full flow
- ✅ Performance optimizations (caching)
- ✅ Audit trail for governance
- ✅ 17 documentation files updated
- ✅ Developer guides and examples

**Quality Gates**:
- Test coverage > 90%
- All tests passing
- Documentation reviewed for accuracy
- Examples validated

---

# Full Implementation Timeline

## Summary Table

| Phase | Task | Effort | Duration | Dependencies |
|-------|------|--------|----------|--------------|
| **PHASE 1** | **Core Backend** | **8-10 hrs** | **Week 1** | None |
| 1.1 | Database schema | 1.5 | Day 1-2 | None |
| 1.2 | Exposure manager service | 2.5 | Day 2-3 | 1.1 |
| 1.3 | Update tools/list endpoint | 1.5 | Day 3 | 1.2 |
| 1.4 | tools/call exposure check | 1 | Day 4 | 1.2 |
| 1.5 | Exception classes | 0.5 | Day 4 | None |
| 1.6 | Admin API endpoints | 2 | Day 4-5 | 1.2, 1.3 |
| | | | | |
| **PHASE 2** | **Admin UI** | **4-6 hrs** | **Week 2** | Phase 1 |
| 2.1 | Exposure management page | 4-5 | Day 6-7 | 1.6 |
| 2.2 | Router & navigation | 0.5 | Day 7 | 2.1 |
| 2.3 | API client functions | 1 | Day 7 | 1.6 |
| 2.4 | Tools page enhancement | 1-2 | Day 8 | 2.1 (optional) |
| | | | | |
| **PHASE 3** | **Polish & Docs** | **5-7 hrs** | **Week 3** | Phase 1, 2 |
| 3.1 | Unit tests | 2 | Day 9 | 1.2 |
| 3.2 | Integration tests | 1.5 | Day 9-10 | 1.3, 1.4, 1.6 |
| 3.3 | Caching layer | 1 | Day 10 | 1.2 |
| 3.4 | Audit logging | 1 | Day 10 | 1.6 |
| 3.5 | Documentation | 9-10 | Day 11-14 | All phases |
| | | | | |
| **TOTAL** | **Complete Exposure Governance** | **~27-28 hrs** | **3 weeks** | Sequential |

---

## Weekly Breakdown

### Week 1: Phase 1 - Core Backend (8-10 hours)
- **Monday (Day 1-2)**: Tasks 1.1 - Database schema + migration
- **Tuesday (Day 2-3)**: Task 1.2 - Exposure manager service
- **Wednesday (Day 3)**: Task 1.3 - Update tools/list endpoint
- **Thursday (Day 4)**: Tasks 1.4, 1.5 - tools/call validation + exceptions
- **Friday (Day 5)**: Task 1.6 - Admin API endpoints
- **Friday EOD**: Phase 1 complete, ready for review

### Week 2: Phase 2 - Admin UI (4-6 hours)
- **Monday (Day 6-7)**: Task 2.1 - Exposure management page
- **Wednesday (Day 7)**: Tasks 2.2, 2.3 - Navigation + API client
- **Thursday (Day 8)**: Task 2.4 (optional) - Tools page enhancement
- **Friday**: Phase 2 complete, end-to-end demo ready

### Week 3: Phase 3 - Polish & Docs (5-7 hours)
- **Monday (Day 9)**: Tasks 3.1, 3.2 - Unit + integration tests
- **Tuesday (Day 10)**: Tasks 3.3, 3.4 - Caching + audit logging
- **Wednesday-Friday (Day 11-14)**: Task 3.5 - Documentation updates
- **Friday EOD**: All documentation reviewed and complete

---

# Implementation Checklist by Task

## Pre-Implementation
- [ ] Review and approve this plan with stakeholders
- [ ] Create feature branch: `feature/exposure-governance`
- [ ] Set up task tracking (Jira/GitHub Issues)
- [ ] Create implementation kanban board

## Phase 1 Implementation

### Task 1.1: Database Schema
- [ ] Create `infrastructure/local/init-scripts/03-exposure-governance.sql`
- [ ] Write migration SQL with comments
- [ ] Add seed data for default roles
- [ ] Test migration applies cleanly
- [ ] Verify new permissions in database
- [ ] Document schema changes

### Task 1.2: Exposure Manager Service
- [ ] Create `mcp-server/app/core/exposure/` directory
- [ ] Create `manager.py` with ExposureManager class
- [ ] Create `__init__.py` with singleton export
- [ ] Implement all methods (get_exposed_tools, filter_tools, etc.)
- [ ] Add logging statements
- [ ] Unit test manager logic
- [ ] Test with mock tool objects

### Task 1.3: Update tools/list Endpoint
- [ ] Update `handle_tools_list()` function signature
- [ ] Add exposure filtering logic
- [ ] Update response to include bundle metadata
- [ ] Add logging for filtering results
- [ ] Update `mcp_handler()` to pass user context
- [ ] Test endpoint with curl/Postman
- [ ] Verify filtered count < total

### Task 1.4: tools/call Exposure Check
- [ ] Update `executor.py` execute() method
- [ ] Add exposure check before authorization
- [ ] Implement error handling for unexposed tools
- [ ] Add logging for exposures
- [ ] Test tools/call blocks unexposed tools
- [ ] Test tools/call allows exposed tools

### Task 1.5: Exception Classes
- [ ] Define ToolNotExposedError class
- [ ] Define ExposureError base class
- [ ] Add to appropriate module
- [ ] Import in executor/handler
- [ ] Test exception raising and catching

### Task 1.6: Admin API Endpoints
- [ ] Create GET /admin/exposure/roles endpoint
- [ ] Create POST /admin/exposure/roles/{role}/permissions endpoint
- [ ] Create DELETE /admin/exposure/roles/{role}/permissions endpoint
- [ ] Create GET /admin/exposure/bundles endpoint
- [ ] Create GET /admin/exposure/preview endpoint
- [ ] Add require_admin decorator to all endpoints
- [ ] Add audit logging to POST/DELETE
- [ ] Test all endpoints work
- [ ] Verify admin-only protection
- [ ] Test cache invalidation on changes

### Phase 1 Testing & Validation
- [ ] Run all manual tests
- [ ] Test role exposure workflow
- [ ] Verify tools/list filtering works
- [ ] Verify tools/call blocks unexposed
- [ ] Commit Phase 1 changes to git
- [ ] Create pull request for review

## Phase 2 Implementation

### Task 2.1: Exposure Management Page
- [ ] Create `admin-ui/src/pages/Exposure.tsx`
- [ ] Implement 3-column layout (roles, bundles, preview)
- [ ] Add role selection logic
- [ ] Add bundle checkbox functionality
- [ ] Add tool preview display
- [ ] Add save/cancel buttons
- [ ] Add loading states
- [ ] Add error handling
- [ ] Style with Tailwind
- [ ] Test all interactions

### Task 2.2: Router & Navigation
- [ ] Update `admin-ui/src/App.tsx` with route
- [ ] Update `Navigation.tsx` with menu item
- [ ] Test navigation works
- [ ] Verify page loads correctly

### Task 2.3: API Client
- [ ] Add `fetchExposureConfig()` function
- [ ] Add `updateRoleExposure()` function
- [ ] Add `addExposurePermission()` function
- [ ] Add `removeExposurePermission()` function
- [ ] Add `listAvailableBundles()` function
- [ ] Add `previewRoleExposure()` function
- [ ] Test all functions work
- [ ] Verify error handling

### Task 2.4: Tools Page Enhancement (Optional)
- [ ] Add bundle badge to ToolList
- [ ] Show bundle name in tool display
- [ ] Test bundle info displays correctly

### Phase 2 Testing & Validation
- [ ] Manual UI testing of all workflows
- [ ] Test role exposure configuration
- [ ] Verify preview updates in real-time
- [ ] Test save persists to backend
- [ ] Test E2E: configure → tools/list returns filtered
- [ ] Commit Phase 2 changes to git
- [ ] Create pull request for review

## Phase 3 Implementation

### Task 3.1: Unit Tests
- [ ] Create `mcp-server/tests/test_exposure_manager.py`
- [ ] Write test_filter_tools_by_bundle
- [ ] Write test_filter_tools_by_tool_name
- [ ] Write test_mixed_toolkit_access
- [ ] Write test_admin_expose_all
- [ ] Write test_cache tests
- [ ] Run pytest
- [ ] Verify coverage > 90%
- [ ] Fix any failures

### Task 3.2: Integration Tests
- [ ] Create `mcp-server/tests/integration/test_exposure_integration.py`
- [ ] Write test_tools_list_respects_exposure
- [ ] Write test_tools_call_blocked_if_not_exposed
- [ ] Write test_admin_sees_all_tools
- [ ] Write test_exposure_permission_add_reflected_in_list
- [ ] Run pytest
- [ ] Fix any failures

### Task 3.3: Caching Layer
- [ ] Add cache dict to ExposureManager
- [ ] Implement cache hit logic
- [ ] Implement cache invalidation
- [ ] Add logging for cache hits/misses
- [ ] Benchmark baseline vs cached
- [ ] Verify >90% performance improvement
- [ ] Test invalidation works

### Task 3.4: Audit Logging
- [ ] Add audit logging to POST /admin/exposure endpoint
- [ ] Add audit logging to DELETE /admin/exposure endpoint
- [ ] Include action, user_id, role, permission, timestamp
- [ ] Test audit logs appear in database
- [ ] Verify logs are complete and readable

### Task 3.5: Documentation (17 files)
- [ ] Update ARCHITECTURE_AND_DATA_STORAGE.md (+4 sections)
- [ ] Update DEVELOPER_ONBOARDING.md (+2 sections)
- [ ] Update REQUEST_LIFECYCLE_DETAILED.md (+1 step)
- [ ] Update admin/ADMIN_GUIDE.md (+1 section)
- [ ] Update user/USER_GUIDE.md (+1 section)
- [ ] Update governance/01-team-structure.md
- [ ] Update governance/02-templates.md
- [ ] Update operations/README.md
- [ ] Update observability/README.md
- [ ] Update devsecops/README.md
- [ ] Update api/README.md (+1 section)
- [ ] Update artefacts/01-mcp-tool-definition.md
- [ ] Update support/README.md
- [ ] Update architecture/02-low-level-architecture.md
- [ ] Update architecture/05-integration-architecture.md
- [ ] Review all docs for consistency
- [ ] Test links between docs
- [ ] Verify examples are accurate

### Phase 3 Testing & Validation
- [ ] All tests passing (unit + integration)
- [ ] Performance benchmarks met
- [ ] Audit logs verified
- [ ] Documentation reviewed
- [ ] Commit Phase 3 changes to git
- [ ] Create pull request for review

## Pre-Merge Review
- [ ] Code review (architecture + security focus)
- [ ] Security review of exposure layer
- [ ] Performance review (caching, query optimization)
- [ ] Documentation review for accuracy
- [ ] Address all review comments
- [ ] Merge to main branch
- [ ] Deploy to staging environment
- [ ] Smoke test in staging
- [ ] Demo to stakeholders
- [ ] Deploy to production

---

# Key Design Decisions Documented

## 1. Anchor to Existing Tables, Not New Entities (Phase 1)

**Decision**: Reuse `policy_role_permissions` with `expose:*` permission types instead of creating new `exposure_profiles` table.

**Rationale**:
- ✅ Simpler implementation
- ✅ Leverages existing policy engine patterns
- ✅ No schema migration of core tables
- ✅ Easier for admins (same interface as other permissions)

**Tradeoff**: Less flexible than separate profiles table, but sufficient for MVP.

**Future Option**: Add `exposure_profiles` table in Phase 2+ if needed for reusability.

---

## 2. Two-Layer Architecture

**Decision**: Separate exposure (visibility) from authorization (capability).

**Layers**:
- **Layer B (Exposure)**: Should user SEE this tool in tools/list?
  - Responsibility: ExposureManager
  - Location: mcp.py handle_tools_list()
  
- **Layer A (Authorization)**: Can user EXECUTE this tool?
  - Responsibility: PolicyEngine (existing)
  - Location: executor.py before execution

**Rationale**:
- ✅ Matches security best practices (separation of concerns)
- ✅ Matches MCP protocol design (tools/list → tools/call separation)
- ✅ Defense-in-depth: filter breaks → auth still blocks
- ✅ Easier to understand and maintain

---

## 3. Allow-Lists Only (MVP)

**Decision**: Start with `allowed_bundles` + `allowed_tool_ids` only. No deny-lists initially.

**Rationale**:
- ✅ Simpler logic (1 permission type vs 2)
- ✅ Safer (less likely to accidentally expose tools)
- ✅ Sufficient for MVP use cases
- ✅ Can add deny-lists later if requested

**Future**: Phase 2+ can add `denied_tool_ids` if needed.

---

## 4. Role-Based Exposure, Not Per-User

**Decision**: Exposure tied to roles (+ optional client app identity), NOT individual users.

**Rationale**:
- ✅ Reduces admin overhead (500 users → manage 5-10 roles)
- ✅ Simpler governance model
- ✅ Matches RFP emphasis on "product boundaries" not "user entitlements"
- ✅ Faster to implement

**Tradeoff**: Less granular than per-user, but not needed for MVP.

**Future**: Add per-user overrides if MSIL explicitly requires.

---

## 5. Caching for Performance

**Decision**: Cache exposure permissions in ExposureManager in-memory.

**Caching Strategy**:
- Cache key: Role name (or combined if multiple roles)
- No TTL initially (invalidate on admin changes only)
- Hit rate: ~99% (most requests from same users/roles)

**Rationale**:
- ✅ 50x performance improvement (50ms → 1ms per tools/list)
- ✅ Simple implementation
- ✅ Safe (invalidate on admin changes)

**Metrics**:
- Track cache_hits / cache_misses
- Alert if misses > 10% (indicates stale policy)

---

## 6. Separation of Concerns

**Decision**: ExposureManager handles ONLY visibility logic. PolicyEngine handles ONLY authorization logic.

**Modules**:
- `app/core/exposure/manager.py` - Exposure resolution
- `app/core/policy/engine.py` - Authorization decisions (existing)
- `app/api/mcp.py` - MCP protocol (existing)
- `app/core/tools/executor.py` - Tool execution (existing)

**Rationale**:
- ✅ Single responsibility principle
- ✅ No logic duplication
- ✅ Easier to test and debug
- ✅ Easier to add/remove features

---

# Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Exposure filter breaks, returns no tools | Medium | High | Fallback to all_tools if error; log warning at WARN level |
| Cache becomes stale | Low | Medium | Invalidate on admin changes; add optional TTL later |
| Performance regression in tools/list | Low | High | Benchmark baseline; caching in Phase 3.3 mitigates |
| Admin UI confusing for operators | Medium | Low | UX with preview pane; tooltip explanations; user docs |
| Documentation outdated after release | Medium | Low | Update immediately; link to version tag; periodic review |
| Breaking change for MCP clients | Low | High | None: tools/list returns subset, same schema |
| Migration fails in production | Low | High | Test migration in staging first; backup DB before apply |
| Audit logs incomplete | Low | Medium | Test log_event calls; spot-check logs post-deployment |
| Security: exposure bypassed via direct API | Low | High | Defense-in-depth (executor also checks); penetration test |

**Risk Mitigation Summary**:
- Phase 1: Focus on correctness (test everything)
- Phase 2: Focus on usability (good UI/UX)
- Phase 3: Focus on quality (comprehensive testing + docs)

---

# Success Criteria

## Phase 1 Complete When:
- ✅ All database migrations applied
- ✅ ExposureManager fully functional (unit tested)
- ✅ tools/list filters by exposure
- ✅ tools/call blocks unexposed tools
- ✅ Admin API endpoints all working
- ✅ Manual end-to-end test passes

## Phase 2 Complete When:
- ✅ Exposure management page fully functional
- ✅ Admin can configure role exposure
- ✅ Preview pane shows correct tools
- ✅ Changes persist and reflected in tools/list
- ✅ End-to-end demo passes

## Phase 3 Complete When:
- ✅ >90% test coverage
- ✅ All tests passing
- ✅ Caching performance verified
- ✅ Audit logging working
- ✅ All 17 docs updated
- ✅ Code review approved
- ✅ Security review approved
- ✅ Production deployment successful

---

# Stakeholder Sign-Off

**Plan Prepared By**: AI Assistant  
**Date**: February 2, 2026  
**Status**: Ready for Implementation

**Required Approvals**:
- [ ] Tech Lead: __________________ Date: ______
- [ ] Security Lead: __________________ Date: ______
- [ ] Product Manager: __________________ Date: ______

**Implementation Owner**: _____________________________  
**Review Schedule**:
- Phase 1 review: After Task 1.6 complete (Friday EOD Week 1)
- Phase 2 review: After Task 2.4 complete (Friday EOD Week 2)
- Phase 3 review: After Task 3.5 complete (Friday EOD Week 3)

---

**Document Version History**:
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Feb 2, 2026 | AI | Initial implementation plan |

