# MSIL MCP Platform — User Guide

**Version**: 1.1  
**Date**: February 2, 2026  
**Audience**: Business Users, Operators, Support Teams

---

## 1) What the MCP Platform Does

The MCP Platform provides secure, controlled access to backend tools (dealer, inventory, booking, customer) through a Host/Agent application. You request actions in natural language, and the system executes approved tools on your behalf.

---

## 2) How Access Works

Your access is determined by **roles and departments** assigned in the MSIL IdP, and by **Exposure Governance** (tool visibility rules):

- **Viewer**: Read-only tools
- **Operator**: Read + approved write tools
- **Developer**: Broader tooling access (non-prod)
- **Admin**: Full access

Department scope also applies (e.g., dealer-operations vs sales).

---

## 3) Login & Authentication

1. Open the Host/Agent App or Admin UI.
2. Sign in using your MSIL IdP account.
3. Your token will include your role and department claims.

If you don’t see expected tools, contact your admin to update your IdP role assignment or Exposure Governance permissions.

---

## 4) Using Tools

### 4.1 Discover Available Tools
The system automatically lists tools you are allowed to use. Exposure Governance limits visibility to only the tools you need.

### 4.2 Execute a Tool
When you ask for an action:
1. The system checks your role and department.
2. It validates input parameters.
3. It executes the tool and returns the result.

### 4.3 Write Tools Require Confirmation
For **write/privileged tools**, you must confirm the action.

Example confirmation:
```
user_confirmed: true
```

---

## 5) Privileged Access (PIM)

Some tools require **Privileged Identity Management (PIM)**.

If you attempt a privileged tool without elevation:
- You will receive a **403 Elevation Required**.
- Request elevation via IdP, then retry.

---

## 6) Common Errors & What to Do

| Error | Meaning | Action |
|------|---------|--------|
| 401 Unauthorized | Token invalid/expired | Re-login |
| 403 Forbidden | Role/department mismatch | Ask admin for access |
| 403 Elevation Required | PIM missing | Request PIM elevation |
| 429 Rate Limited | Too many requests | Retry after a minute |
| 400 Invalid Params | Input invalid | Fix request parameters |

---

## 7) Security Rules (Must Follow)

- **Never share credentials**
- **Do not expose PII** in requests
- **Use confirmation for write actions**
- **Report access issues to admins**

---

## 8) Getting Access or Changes

If you need new tool access:
1. Contact your platform admin
2. Provide tool name + justification
3. Admin will update IdP role, OPA policy, or Exposure Governance permission

---

*Last updated: February 2, 2026*
