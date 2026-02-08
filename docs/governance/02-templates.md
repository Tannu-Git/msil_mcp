# Governance Templates

**Document Version**: 2.1  
**Last Updated**: February 2, 2026  
**Classification**: Internal

---

## 1. Change Request Template

### 1.1 Standard Change Request (CR)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CHANGE REQUEST FORM                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ CR Number: CR-2026-XXX          Date: _______________                   │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ SECTION 1: CHANGE DETAILS                                                │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Title: _______________________________________________________________  │
│                                                                          │
│ Category:  □ Feature  □ Bug Fix  □ Security  □ Performance  □ Config   │
│                                                                          │
│ Priority:  □ Critical  □ High  □ Medium  □ Low                          │
│                                                                          │
│ Affected Components: _________________________________________________  │
│                                                                          │
│ Description:                                                             │
│ _____________________________________________________________________   │
│ _____________________________________________________________________   │
│ _____________________________________________________________________   │
│                                                                          │
│ Business Justification:                                                  │
│ _____________________________________________________________________   │
│ _____________________________________________________________________   │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ SECTION 2: IMPACT ASSESSMENT                                             │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Service Impact:     □ None  □ Minor  □ Moderate  □ Significant          │
│ User Impact:        □ None  □ Minor  □ Moderate  □ Significant          │
│ Security Impact:    □ None  □ Minor  □ Moderate  □ Significant          │
│ Exposure Impact:    □ None  □ Minor  □ Moderate  □ Significant          │
│ Downtime Required:  □ Yes (Duration: _______)  □ No                     │
│                                                                          │
│ Risk Assessment:                                                         │
│ _____________________________________________________________________   │
│                                                                          │
│ Rollback Plan:                                                           │
│ _____________________________________________________________________   │
│ _____________________________________________________________________   │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ SECTION 3: IMPLEMENTATION                                                │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Planned Date/Time: _________________ Duration: _______                  │
│                                                                          │
│ Implementation Steps:                                                    │
│ 1. ___________________________________________________________________  │
│ 2. ___________________________________________________________________  │
│ 3. ___________________________________________________________________  │
│                                                                          │
│ Testing/Validation:                                                      │
│ _____________________________________________________________________   │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ SECTION 4: APPROVALS                                                     │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Requestor: ___________________ Sign: _________ Date: _________          │
│ Tech Lead: ___________________ Sign: _________ Date: _________          │
│ Security:  ___________________ Sign: _________ Date: _________          │
│ Product Owner: _______________ Sign: _________ Date: _________          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Emergency Change Request

```yaml
# Emergency Change Request - ECR

ecr_number: ECR-2026-XXX
created_at: 2026-01-31T10:30:00Z
created_by: engineer@nagarro.com

incident_reference: INC-2026-XXX  # Related incident if applicable

change_details:
  title: "Emergency fix for [issue]"
  description: |
    Brief description of the emergency change required.
  
  justification: |
    Why this cannot wait for standard change process.
  
  components_affected:
    - mcp-server
    - database (if applicable)

implementation:
  planned_datetime: 2026-01-31T11:00:00Z
  estimated_duration: "30 minutes"
  
  steps:
    - step: 1
      action: "Apply hotfix"
      verification: "Health check passes"
    - step: 2
      action: "Monitor logs"
      verification: "No errors in 15 minutes"
  
  rollback_plan: |
    kubectl rollout undo deployment/mcp-server -n mcp-production

approvals:
  tech_lead:
    name: ""
    approved_at: ""
  post_implementation_review:
    due_by: "+24 hours"
    assignee: ""
```

---

## 2. Incident Report Template

### 2.1 Incident Record

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INCIDENT REPORT                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ Incident ID: INC-2026-XXX         Severity: □P1 □P2 □P3 □P4             │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ INCIDENT SUMMARY                                                         │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Title: _______________________________________________________________  │
│                                                                          │
│ Status: □ Open  □ Investigating  □ Mitigated  □ Resolved  □ Closed     │
│                                                                          │
│ Start Time: ___________________  End Time: ___________________          │
│                                                                          │
│ Duration: ___________________   MTTR: ___________________               │
│                                                                          │
│ Affected Services:                                                       │
│ _____________________________________________________________________   │
│                                                                          │
│ Impact Description:                                                      │
│ _____________________________________________________________________   │
│ _____________________________________________________________________   │
│                                                                          │
│ Users Affected: _______________  Requests Failed: _______________       │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ TIMELINE                                                                 │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Time        │ Event                                                      │
│ ────────────┼──────────────────────────────────────────────────────────  │
│ HH:MM       │ Alert triggered                                            │
│ HH:MM       │ On-call acknowledged                                       │
│ HH:MM       │ Root cause identified                                      │
│ HH:MM       │ Mitigation applied                                         │
│ HH:MM       │ Service restored                                           │
│ HH:MM       │ Incident closed                                            │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ ROOT CAUSE ANALYSIS                                                      │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Root Cause:                                                              │
│ _____________________________________________________________________   │
│ _____________________________________________________________________   │
│                                                                          │
│ Contributing Factors:                                                    │
│ _____________________________________________________________________   │
│ _____________________________________________________________________   │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ RESOLUTION                                                               │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Immediate Fix:                                                           │
│ _____________________________________________________________________   │
│                                                                          │
│ Permanent Fix:                                                           │
│ _____________________________________________________________________   │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ ACTION ITEMS                                                             │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ # │ Action                          │ Owner    │ Due Date  │ Status    │
│ ──┼─────────────────────────────────┼──────────┼───────────┼────────── │
│ 1 │                                 │          │           │ □         │
│ 2 │                                 │          │           │ □         │
│ 3 │                                 │          │           │ □         │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ SIGN-OFF                                                                 │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Incident Manager: ___________________ Date: _______________             │
│ Technical Lead: _____________________ Date: _______________             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Release Notes Template

### 3.1 Release Document

```markdown
# Release Notes - v2.1.0

**Release Date**: January 31, 2026  
**Release Type**: Minor Release  
**Deployment Window**: 02:00-04:00 IST

---

## Overview

Brief description of this release and its main features.

---

## New Features

### Feature 1: [Feature Name]
- Description of the feature
- User impact
- Configuration changes (if any)

### Feature 2: [Feature Name]
- Description of the feature
- User impact

---

## Improvements

- Improvement 1: Description
- Improvement 2: Description
- Performance: 20% faster tool execution

---

## Bug Fixes

| Issue ID | Description | Severity |
|----------|-------------|----------|
| BUG-123 | Fixed timeout issue | High |
| BUG-124 | Corrected error message | Low |

---

## Security Updates

- Updated dependency XYZ to patch CVE-2026-XXXX
- Enhanced input validation for tool parameters

---

## Breaking Changes

⚠️ **None in this release**

OR

⚠️ **Breaking Changes**:
- Change 1: Description and migration steps
- Change 2: Description and migration steps

---

## Configuration Changes

```yaml
# New configuration option
new_setting: value
```

---

## Database Migrations

- Migration 1: Description
- Rollback procedure: Description

---

## Known Issues

| Issue | Workaround | Fix Expected |
|-------|------------|--------------|
| Issue description | Workaround steps | v2.2.0 |

---

## Rollback Instructions

```bash
kubectl rollout undo deployment/mcp-server -n mcp-production --to-revision=N
```

---

## Verification Steps

1. Verify health endpoint returns 200
2. Execute smoke test suite
3. Verify key metrics in dashboard

---

## Approvals

| Role | Name | Date |
|------|------|------|
| Tech Lead | | |
| QA Lead | | |
| Product Owner | | |
```

---

## 4. Security Exception Request

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SECURITY EXCEPTION REQUEST                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ Request ID: SEC-EXC-2026-XXX      Date: _______________                 │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ REQUESTOR INFORMATION                                                    │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Name: _________________________ Department: ___________________         │
│ Email: ________________________ Manager: _____________________          │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ EXCEPTION DETAILS                                                        │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Policy/Control Being Excepted:                                          │
│ _____________________________________________________________________   │
│                                                                          │
│ Justification:                                                           │
│ _____________________________________________________________________   │
│ _____________________________________________________________________   │
│ _____________________________________________________________________   │
│                                                                          │
│ Duration Requested:  □ 30 days  □ 90 days  □ 180 days  □ Permanent     │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ RISK ASSESSMENT                                                          │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Risk Level:  □ Low  □ Medium  □ High  □ Critical                        │
│                                                                          │
│ Potential Impact:                                                        │
│ _____________________________________________________________________   │
│                                                                          │
│ Compensating Controls:                                                   │
│ _____________________________________________________________________   │
│ _____________________________________________________________________   │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ APPROVALS                                                                │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Manager: _____________________ Sign: _________ Date: _________          │
│ Security Lead: _______________ Sign: _________ Date: _________          │
│ CISO (if High/Critical): _____ Sign: _________ Date: _________          │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ REVIEW SCHEDULE                                                          │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Review Date: _______________  Reviewer: _______________                 │
│                                                                          │
│ □ Exception still required     □ Exception can be removed               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Access Request Template

```yaml
# Access Request Form

request_id: ACC-2026-XXX
request_date: 2026-01-31
requestor: user@msil.com

access_details:
  type: 
    - [ ] New Access
    - [ ] Modification
    - [ ] Removal
  
  environment:
    - [ ] Development
    - [ ] Staging
    - [ ] Production
  
  role_requested: "operator"  # viewer/operator/admin
  
  justification: |
    Describe why this access is needed.
  
  duration:
    type: "permanent"  # or "temporary"
    end_date: null     # if temporary

approvals:
  manager:
    name: ""
    approved: false
    date: null
  
  security:
    name: ""
    approved: false
    date: null
  
  system_owner:
    name: ""
    approved: false
    date: null

provisioning:
  completed_by: ""
  completed_date: null
  verification: ""
```

---

## 6. Post-Implementation Review (PIR)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   POST-IMPLEMENTATION REVIEW                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ PIR ID: PIR-2026-XXX              Date: _______________                 │
│ Related CR: CR-2026-XXX           Release: v2.1.0                       │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ IMPLEMENTATION SUMMARY                                                   │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Planned Date/Time: _______________ Actual: _______________              │
│ Planned Duration: ________________ Actual: _______________              │
│                                                                          │
│ Status:  □ Successful  □ Successful with issues  □ Rolled back         │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ SUCCESS CRITERIA                                                         │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ □ All services healthy post-deployment                                  │
│ □ No increase in error rates                                            │
│ □ Performance within acceptable limits                                  │
│ □ All smoke tests passed                                                │
│ □ No security vulnerabilities introduced                                │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ ISSUES ENCOUNTERED                                                       │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Issue 1: ______________________________________________________________  │
│ Resolution: ___________________________________________________________  │
│                                                                          │
│ Issue 2: ______________________________________________________________  │
│ Resolution: ___________________________________________________________  │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ LESSONS LEARNED                                                          │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ What went well:                                                          │
│ _____________________________________________________________________   │
│                                                                          │
│ What could be improved:                                                  │
│ _____________________________________________________________________   │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ FOLLOW-UP ACTIONS                                                        │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ # │ Action                          │ Owner    │ Due Date               │
│ ──┼─────────────────────────────────┼──────────┼─────────────────────── │
│ 1 │                                 │          │                        │
│ 2 │                                 │          │                        │
│                                                                          │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│ SIGN-OFF                                                                 │
│ ───────────────────────────────────────────────────────────────────────  │
│                                                                          │
│ Implementation Lead: _______________ Date: _______________              │
│ Change Manager: ____________________ Date: _______________              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Tool Registration Request

```yaml
# Tool Registration Request

request_id: TOOL-2026-XXX
request_date: 2026-01-31
requestor: developer@nagarro.com

tool_details:
  name: "new_tool_name"
  description: "Human-readable description for LLM"
  version: "1.0.0"
  domain: "dealer"  # Business domain
  
  backend_api:
    endpoint: "/v1/service/operation"
    method: "GET"
    openapi_spec_url: "https://api.msil.com/service/openapi.yaml"

security_classification:
  risk_level: "read"  # read/write/privileged
  
  data_classification:
    - [ ] Public
    - [ ] Internal
    - [ ] Confidential
    - [ ] Restricted
  
  pii_involved: false
  financial_data: false
  requires_elevation: false

access_control:
  allowed_roles:
    - viewer
    - operator
    - admin
  
  rate_limit: "standard"  # permissive/standard/strict

testing_evidence:
  unit_tests: "link_to_tests"
  integration_tests: "link_to_tests"
  security_review: "link_to_review"

approvals:
  tech_lead:
    name: ""
    approved: false
  
  security_lead:
    name: ""
    approved: false
  
  product_owner:
    name: ""
    approved: false
```

---

*Document Classification: Internal | Last Review: January 31, 2026*
