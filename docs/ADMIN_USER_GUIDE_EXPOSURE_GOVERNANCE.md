# Exposure Governance - Admin User Guide

**Version**: 1.0  
**Last Updated**: February 2, 2026  
**Audience**: System Administrators, Security Officers  

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Understanding Exposure Governance](#understanding-exposure-governance)
4. [Managing Permissions](#managing-permissions)
5. [Common Scenarios](#common-scenarios)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)
8. [Access Matrices](#access-matrices)

---

## Introduction

The **Exposure Governance** system provides fine-grained control over which tools users can see and access. It operates as a two-layer security model:

- **Layer B (Exposure)**: Controls tool visibility (what users SEE)
- **Layer A (Authorization)**: Controls tool execution (what users CAN DO)

This guide covers Layer B administration. Only authorized administrators can manage tool exposure.

### Key Concepts

| Concept | Definition |
|---------|-----------|
| **Role** | A group of users with assigned permissions (e.g., operator, analyst) |
| **Permission** | Grant of exposure to tool(s) in a specific format |
| **Tool** | A callable service/API available through the MCP |
| **Bundle** | A logical grouping of related tools |
| **Exposure** | The visibility of tools to a user in the tools/list response |

---

## Getting Started

### Accessing the Admin Portal

1. **Navigate to Admin UI**
   ```
   http://localhost:3000/admin
   ```

2. **Authenticate**
   - Use your admin credentials
   - You must have the `admin` role assigned

3. **Access Exposure Management**
   - Click "Exposure Governance" in left sidebar
   - Or navigate to `/admin/exposure`

### Admin Interface Overview

```
┌─────────────────────────────────────────────────────────────┐
│  EXPOSURE GOVERNANCE                                  [Search]│
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Select Role:  [Operator ▼] [Analyst ▼] [Viewer ▼] [Custom]│
│                                                               │
├──────────────────────┬──────────────────┬──────────────────┤
│  PERMISSIONS         │  ADD PERMISSION  │  PREVIEW TOOLS   │
│  (Left Panel)        │  (Center Panel)  │  (Right Panel)   │
│                      │                  │                  │
│ • expose:all         │ Permission Type: │ Tools visible to │
│ • expose:bundle:*    │  ○ All Access    │ this role:       │
│ • expose:tool:*      │  ○ Bundle Access │                  │
│                      │  ○ Tool Access   │ ✓ Tool A         │
│ [+ Add]              │                  │ ✓ Tool B         │
│ [- Remove]           │ Select Bundle:   │ ✓ Tool C         │
│                      │ [Customer ▼]     │                  │
│                      │                  │ Granting access  │
│                      │ [Preview] [Save] │ to 3 tools       │
└──────────────────────┴──────────────────┴──────────────────┘
```

### Key UI Components

**Left Panel: Permissions List**
- Shows all current permissions for selected role
- Each permission as a removable tag
- Color-coded by type:
  - 🔵 Blue: All Access (expose:all)
  - 🟡 Yellow: Bundle Access (expose:bundle:*)
  - 🟢 Green: Tool Access (expose:tool:*)

**Center Panel: Add Permission**
- Choose permission type
- Select target (bundle or tool)
- Preview impact
- Save changes

**Right Panel: Preview**
- Live view of tools user will see
- Updates in real-time as permissions change
- Shows affected bundles
- Expandable bundle view

---

## Understanding Exposure Governance

### Two-Layer Security Model

```
REQUEST: User asks for tools/list

         ┌─────────────────────────────┐
         │   LAYER B: EXPOSURE         │
         │   Who can SEE the tool?     │
         │                             │
         │  Check user role against    │
         │  exposure permissions:      │
         │  • expose:all               │
         │  • expose:bundle:*          │
         │  • expose:tool:*            │
         └──────────┬──────────────────┘
                    │
                    ▼ Filter by exposure
         ┌─────────────────────────────┐
         │   LAYER A: AUTHORIZATION    │
         │   Who can EXECUTE the tool? │
         │                             │
         │  Check user permissions &   │
         │  credentials (RBAC/ACL)     │
         └──────────┬──────────────────┘
                    │
                    ▼ Filter by authorization
         ┌─────────────────────────────┐
         │   RESPONSE: Filtered Tools  │
         │   (Visible AND Executable)  │
         └─────────────────────────────┘
```

### Permission Types

#### 1. All Access (`expose:all`)
Grants visibility to **ALL tools** in the system.

```
Permission Format: expose:all
Example: expose:all
```

**Use Case**: Administrator or power user roles

**Impact**: 
- User can see all 250+ tools
- No tool filtering applied
- Fastest response (cached)

**Granted via UI**:
- Permission Type: "All Access"
- No additional selection needed

---

#### 2. Bundle Access (`expose:bundle:BUNDLE_NAME`)
Grants visibility to **all tools in a specific bundle**.

```
Permission Format: expose:bundle:BUNDLE_NAME
Example: expose:bundle:customer-service
Example: expose:bundle:data-analysis
```

**Use Cases**:
- Operators managing customer interactions
- Teams specialized in data processing
- Department-specific tool access

**Available Bundles**:
- `customer-service` - Customer-facing tools (15 tools)
- `data-analysis` - Analytics tools (22 tools)
- `integration-hub` - System integration tools (18 tools)
- `security-ops` - Security and compliance tools (12 tools)
- `dev-tools` - Developer utilities (25 tools)

**Impact**:
- User can see only tools in the bundle
- Focused, relevant toolset
- Reduced token usage (10-15 tokens/day vs 50+ for all)

**Granted via UI**:
- Permission Type: "Bundle Access"
- Select Bundle: [Dropdown list]
- Shows number of tools in preview

---

#### 3. Tool Access (`expose:tool:TOOL_NAME`)
Grants visibility to **a specific individual tool**.

```
Permission Format: expose:tool:TOOL_NAME
Example: expose:tool:create-customer
Example: expose:tool:generate-report
```

**Use Cases**:
- Minimal access principle
- Specific integration requirements
- Restricted user roles

**Impact**:
- User can see only 1 tool
- Maximum security (least access)
- Minimal token usage (1-2 tokens/day)

**Granted via UI**:
- Permission Type: "Tool Access"
- Select Tool: [Search/Dropdown]
- Shows tool details in preview

---

### Permission Evaluation Flow

```
FOR EACH TOOL IN SYSTEM:
  
  IF user has "expose:all" permission:
    ✓ INCLUDE tool in response
    
  ELSE IF user has "expose:bundle:BUNDLE" AND tool.bundle == BUNDLE:
    ✓ INCLUDE tool in response
    
  ELSE IF user has "expose:tool:TOOL" AND tool.name == TOOL:
    ✓ INCLUDE tool in response
    
  ELSE:
    ✗ EXCLUDE tool from response
    
RETURN filtered tools to user
```

---

## Managing Permissions

### Step 1: Select a Role

1. Click the role button at the top
2. Choose from available roles:
   - **Operator** - Limited access (customer-facing tools)
   - **Analyst** - Medium access (data + customer tools)
   - **Viewer** - Read-only access (monitoring tools)
   - **Custom** - User-defined role

### Step 2: View Current Permissions

The left panel displays current permissions for the selected role:

```
PERMISSIONS FOR: Operator

expose:bundle:customer-service  [×]
expose:bundle:data-analysis     [×]

[+ Add Permission] [Clear All]
```

Click **[×]** to remove a permission immediately (with confirmation).

### Step 3: Add a New Permission

1. Click **[+ Add Permission]** button
2. Dialog opens with three options:
   - **All Access**: Grant access to all tools
   - **Bundle Access**: Select specific bundle
   - **Tool Access**: Select specific tool

3. For Bundle or Tool Access:
   - Use dropdown or search to find target
   - Preview shows affected tools
   - Confirmation shows count of new tools

4. Click **[Add]** to grant permission
5. Permission appears in left panel
6. Preview panel updates live

### Step 4: Preview Changes

Before saving, review the **Preview Tools** panel on the right:

```
PREVIEW: Operator Role
Tools Visible: 37 (will be 45 after adding)

BUNDLES:
  ✓ customer-service (15 tools)
    • create-customer
    • update-customer
    • delete-customer
    ... [+ 12 more]
  
  ✓ data-analysis (22 tools)
    [Collapsed]
```

Click any bundle header to expand/collapse tools.

### Step 5: Save Changes

Click **[Save Changes]** button:
- Permission is saved to database
- Admin audit log is created
- Caches are invalidated
- User will immediately see exposure change
- Success notification appears

### Removing Permissions

**Option 1: Quick Remove**
- Hover over permission tag
- Click **[×]** button
- Confirm removal

**Option 2: Batch Remove**
- Click **[Clear All]**
- Confirms all permissions for role will be removed
- User will see NO tools

---

## Common Scenarios

### Scenario 1: Onboard New Operator

**Goal**: Give a new operator access to customer service tools

**Steps**:
1. Select "Operator" role from top menu
2. Click **[+ Add Permission]**
3. Select "Bundle Access"
4. Choose "customer-service" bundle
5. Preview shows 15 customer tools
6. Click **[Add]**
7. Permission "expose:bundle:customer-service" appears
8. Click **[Save Changes]**

**Result**: Operator can now see all customer service tools

**Verification**:
```bash
# Check via API
curl http://localhost:8000/mcp/tools/list \
  -H "X-User-Role: operator"
# Should show 15 customer tools
```

---

### Scenario 2: Grant Admin Full Access

**Goal**: Give admin user access to ALL tools for system management

**Steps**:
1. Select "admin" role
2. Click **[+ Add Permission]**
3. Select "All Access"
4. Preview shows all 250+ tools
5. Click **[Add]**
6. Permission "expose:all" appears
7. Click **[Save Changes]**

**Result**: Admin sees all tools in tools/list

**Note**: Admin authorization still applies (Layer A)

---

### Scenario 3: Revoke Specific Tool Access

**Goal**: Remove analyst's access to sensitive report tool

**Steps**:
1. Select "Analyst" role
2. Find "expose:tool:sensitive-report" in list
3. Click **[×]** next to permission
4. Confirm removal
5. Preview updates showing tool removed
6. Click **[Save Changes]**

**Result**: Analyst no longer sees sensitive-report tool

---

### Scenario 4: Grant Minimal Access (Least Privilege)

**Goal**: Create viewer role with access to only 2 specific tools

**Steps**:
1. Select "Viewer" role
2. Click **[Clear All]** to remove any permissions
3. Click **[+ Add Permission]**
4. Select "Tool Access"
5. Search and select "get-status-report"
6. Add permission
7. Click **[+ Add Permission]** again
8. Select "Tool Access"
9. Search and select "get-user-info"
10. Add permission
11. Preview shows exactly 2 tools
12. Click **[Save Changes]**

**Result**: Viewer can access only status report and user info

---

### Scenario 5: Department-Based Access

**Goal**: Set up data team with data + integration tools

**Steps**:
1. Select "DataTeam" role
2. Click **[+ Add Permission]**
3. Select "Bundle Access"
4. Choose "data-analysis" bundle
5. Add permission
6. Click **[+ Add Permission]**
7. Select "Bundle Access"
8. Choose "integration-hub" bundle
9. Add permission
10. Preview shows 22 + 18 = 40 tools
11. Click **[Save Changes]**

**Result**: Data team can access both data and integration tools

---

## Troubleshooting

### Issue 1: User Can't See Expected Tools

**Symptoms**:
- User reports missing tools in tools/list
- UI shows tools but API doesn't

**Diagnosis**:
1. Check tools/list response:
   ```bash
   curl http://localhost:8000/mcp/tools/list \
     -H "X-User-Role: operator"
   ```

2. Compare tools in response to expected tools

3. Check admin UI preview panel:
   - Select same role
   - View preview panel
   - Verify tools are listed

**Common Causes**:
- Permission not added (check permissions list)
- Permission format incorrect (check for typos)
- Cache not invalidated (clear cache if needed)
- Wrong role header sent

**Resolution**:
1. Verify permission exists in UI
2. Verify correct role sent in request header
3. Clear browser cache and retry
4. Try tools/list API directly to isolate issue

---

### Issue 2: Permission Added but Not Visible

**Symptoms**:
- Added permission shows in UI
- Tools/list still doesn't include new tools
- Changes don't appear in preview

**Diagnosis**:
1. Check if save was successful (look for success notification)
2. Refresh the page
3. Check database directly:
   ```sql
   SELECT * FROM policy_role_permissions 
   WHERE role_id = (SELECT id FROM policy_roles WHERE name = 'operator')
   ORDER BY created_at DESC;
   ```

**Common Causes**:
- Save failed silently (network error)
- Database constraint violation
- Incorrect permission format

**Resolution**:
1. Check browser console for errors
2. Verify permission format (expose:type:value)
3. Try removing and re-adding permission
4. Check server logs for database errors

---

### Issue 3: Performance Issues in Preview

**Symptoms**:
- Preview panel is slow to update
- Adding permissions takes long time
- UI feels laggy

**Diagnosis**:
1. Open browser dev tools (F12)
2. Check Network tab for API calls
3. Check Console for JavaScript errors

**Common Causes**:
- Large number of permissions (100+)
- Network latency
- Server under load
- Browser cache issues

**Resolution**:
1. Clear browser cache and cookies
2. Reduce number of permissions (use bundles instead of individual tools)
3. Check server metrics for load
4. Restart admin UI service if needed

---

### Issue 4: Can't Remove Permission

**Symptoms**:
- Remove button doesn't work
- Permission appears to remove but reappears
- Error message on removal

**Diagnosis**:
1. Check if permission is locked (special system permissions)
2. Check user authorization level
3. Review server logs for errors

**Common Causes**:
- User doesn't have remove permission
- Database connection issue
- System-level permission (can't remove)

**Resolution**:
1. Verify you are logged in as admin
2. Check database connection
3. Try removing from API directly:
   ```bash
   curl -X DELETE http://localhost:8000/admin/exposure/roles/operator/permissions \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"permission": "expose:bundle:customer-service"}'
   ```

---

## Best Practices

### 1. Use Bundles Over Individual Tools

**❌ Bad**: Grant 15 individual tool permissions
```
expose:tool:create-customer
expose:tool:update-customer
expose:tool:delete-customer
expose:tool:view-customer
... [11 more individual permissions]
```

**✅ Good**: Grant single bundle permission
```
expose:bundle:customer-service
```

**Benefits**:
- Fewer permissions to manage
- Easier to audit
- Better performance
- Automatically includes new tools added to bundle

---

### 2. Follow Least Privilege Principle

**❌ Bad**: Grant expose:all to most users
```
Operator: expose:all  (sees 250+ tools)
Analyst:  expose:all
Viewer:   expose:all
```

**✅ Good**: Grant only necessary access
```
Operator: expose:bundle:customer-service
Analyst:  expose:bundle:data-analysis + expose:bundle:customer-service
Viewer:   expose:tool:get-status + expose:tool:get-metrics
```

**Benefits**:
- Reduced attack surface
- Minimal token usage
- Clear role boundaries
- Easier to audit

---

### 3. Document Permission Changes

Always add context when making significant changes:

**✅ Good Practice**:
```
2024-01-15: Granted analyst expose:bundle:data-analysis
  Reason: Analyst needs access for quarterly report
  Approved by: Manager
  Sunset: 2024-03-31 (to be reviewed)
```

Track in external system (wiki, ticket system, etc.)

---

### 4. Review Permissions Regularly

**Monthly**:
- Review roles and their permissions
- Check for unused roles
- Verify principle of least privilege

**Quarterly**:
- Full access audit
- Remove unused permissions
- Document any changes

**Use API for audit**:
```bash
# Get all role permissions
curl http://localhost:8000/admin/exposure/roles
```

---

### 5. Plan for New Tools

When new tools are added to system:

**Bundle-Based Roles**:
- New tool automatically visible
- No admin action needed
- Preferred approach

**Tool-Specific Roles**:
- Manually add permission for each role
- Document which roles need new tool
- Update role descriptions

**Action**: After tools added, verify permissions are complete

---

### 6. Handle Role Hierarchy

Structure roles in hierarchy:

```
Admin (expose:all)
  ├─ Operator (expose:bundle:customer-service)
  ├─ Analyst (expose:bundle:data-analysis)
  └─ Viewer (expose:tool:get-status, expose:tool:get-metrics)
```

**Benefits**:
- Clear escalation path
- Easy to understand access levels
- Simpler onboarding

---

### 7. Monitor Audit Logs

Check audit logs for:
- Permission additions
- Permission removals
- Who made changes
- When changes occurred

**View logs**:
```sql
SELECT * FROM audit_logs 
WHERE resource_type = 'exposure_permission'
ORDER BY created_at DESC
LIMIT 20;
```

---

## Access Matrices

### Example 1: Typical Small Team

| Role | Permissions | Tools | Use Case |
|------|-------------|-------|----------|
| Admin | expose:all | 250+ | System admin, full control |
| Operator | expose:bundle:customer-service | 15 | Customer-facing operations |
| Analyst | expose:bundle:data-analysis, expose:bundle:customer-service | 37 | Analysis + customer context |
| Viewer | expose:tool:status, expose:tool:metrics | 2 | Read-only monitoring |

### Example 2: Enterprise Team Structure

| Role | Department | Permissions | Tools | Notes |
|------|-----------|-------------|-------|-------|
| CTO | Leadership | expose:all | 250+ | Full system access |
| Security | Security | expose:bundle:security-ops | 12 | Compliance & audit |
| DataLead | Data Team | expose:bundle:data-analysis | 22 | Full data access |
| DataAnalyst | Data Team | expose:tool:generate-report, expose:tool:export-data | 2 | Restricted analysis |
| DevOps | Operations | expose:bundle:integration-hub | 18 | System integration |
| Support | Support | expose:bundle:customer-service | 15 | Customer support |

### Example 3: Contractor Access Pattern

| Role | Contractor Type | Permissions | Duration |
|------|-----------------|-------------|----------|
| Consultant | External | expose:tool:get-system-info, expose:tool:view-logs | 90 days |
| Vendor | External | expose:bundle:integration-hub | 1 year contract |
| Auditor | External | expose:bundle:security-ops, expose:tool:audit-report | 60 days |

---

## Quick Reference

### Common Commands (API)

**Get role permissions**:
```bash
curl http://localhost:8000/admin/exposure/roles/operator
```

**Add permission**:
```bash
curl -X POST http://localhost:8000/admin/exposure/roles/operator/permissions \
  -H "Content-Type: application/json" \
  -d '{"permission": "expose:bundle:customer-service"}'
```

**Remove permission**:
```bash
curl -X DELETE http://localhost:8000/admin/exposure/roles/operator/permissions \
  -H "Content-Type: application/json" \
  -d '{"permission": "expose:bundle:customer-service"}'
```

**Get available bundles**:
```bash
curl http://localhost:8000/admin/exposure/bundles
```

**Preview role exposure**:
```bash
curl http://localhost:8000/admin/exposure/preview/operator
```

---

## Support & Contact

For issues or questions:

1. **Check Troubleshooting** section above
2. **Review logs**: 
   - Server logs: `/var/log/mcp-server/`
   - Admin UI: Browser console (F12)
3. **Contact**: security-team@company.com

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2024-01-15 | 1.0 | Initial release |
| 2024-02-02 | 1.0 | Added common scenarios & access matrices |

---

**End of Admin User Guide**

