# MCP Tool Definition Artefacts

**Document Version**: 2.2  
**Last Updated**: February 2, 2026  
**Classification**: Internal

---

## 1. Overview

This document describes the MCP Tool definition format, auto-derivation from OpenAPI specs, and the standard artefacts for tool creation and management.

> **📋 MCP Protocol Note**: The Host/Agent application (not the LLM directly) communicates with the MCP Server. The LLM generates tool call intents that the Host converts to proper MCP protocol requests.

---

## 2. Tool Definition Schema

### 2.1 Complete Tool Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MCP Tool Definition",
  "type": "object",
  "required": ["name", "description", "version", "input_schema", "api_config"],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier (auto-generated)"
    },
    "name": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_]*$",
      "minLength": 3,
      "maxLength": 64,
      "description": "Tool identifier used in LLM tool calls",
      "examples": ["get_dealer_enquiries", "create_booking"]
    },
    "description": {
      "type": "string",
      "minLength": 10,
      "maxLength": 500,
      "description": "Clear description for LLM understanding"
    },
    "bundle_name": {
      "type": "string",
      "maxLength": 255,
      "description": "Logical bundle grouping for Exposure Governance",
      "examples": ["customer-service", "data-analysis"]
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Semantic version"
    },
    "input_schema": {
      "$ref": "#/definitions/json_schema",
      "description": "JSON Schema for input parameters"
    },
    "output_schema": {
      "$ref": "#/definitions/json_schema",
      "description": "JSON Schema for expected output"
    },
    "api_config": {
      "$ref": "#/definitions/api_config"
    },
    "security_config": {
      "$ref": "#/definitions/security_config"
    },
    "validation_config": {
      "$ref": "#/definitions/validation_config"
    },
    "examples": {
      "$ref": "#/definitions/examples"
    },
    "metadata": {
      "$ref": "#/definitions/metadata"
    }
  },
  "definitions": {
    "json_schema": {
      "type": "object",
      "description": "Valid JSON Schema object"
    },
    "api_config": {
      "type": "object",
      "required": ["endpoint", "method"],
      "properties": {
        "endpoint": {
          "type": "string",
          "description": "Backend API path (can include {placeholders})"
        },
        "method": {
          "type": "string",
          "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]
        },
        "path_params": {
          "type": "array",
          "items": {"type": "string"}
        },
        "query_params": {
          "type": "array",
          "items": {"type": "string"}
        },
        "body_mapping": {
          "type": "object",
          "description": "How to map input to request body"
        },
        "response_mapping": {
          "type": "object",
          "description": "How to transform API response"
        },
        "timeout_ms": {
          "type": "integer",
          "default": 30000
        }
      }
    },
    "security_config": {
      "type": "object",
      "properties": {
        "risk_level": {
          "type": "string",
          "enum": ["read", "write", "privileged"],
          "default": "read"
        },
        "requires_confirmation": {
          "type": "boolean",
          "default": false,
          "description": "If true, tool execution requires user_confirmed=true in arguments (step-up confirmation for write/privileged tools)"
        },
        "requires_elevation": {
          "type": "boolean",
          "default": false
        },
        "allowed_roles": {
          "type": "array",
          "items": {"type": "string"}
        },
        "rate_limit_tier": {
          "type": "string",
          "enum": ["permissive", "standard", "strict"],
          "default": "standard"
        },
        "audit_level": {
          "type": "string",
          "enum": ["basic", "detailed", "full"],
          "default": "basic"
        }
      }
    },
    "validation_config": {
      "type": "object",
      "properties": {
        "allowlist": {
          "type": "object",
          "description": "Field-level allowlists"
        },
        "denylist": {
          "type": "object",
          "description": "Field-level denylists"
        },
        "custom_validators": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Named custom validator functions"
        }
      }
    },
    "examples": {
      "type": "object",
      "properties": {
        "positive": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "description": {"type": "string"},
              "input": {"type": "object"},
              "output": {"type": "object"}
            }
          }
        },
        "negative": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "description": {"type": "string"},
              "input": {"type": "object"},
              "error": {"type": "string"}
            }
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "domain": {"type": "string"},
        "journey": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "source_spec": {"type": "string"},
        "owner": {"type": "string"},
        "deprecated": {"type": "boolean"},
        "deprecation_message": {"type": "string"}
      }
    }
  }
}
```

---

## 3. Example Tool Definitions

### 3.1 Read Tool (Low Risk)

```yaml
# tools/get_dealer_enquiries.yaml
name: get_dealer_enquiries
description: |
  Retrieve enquiries for a specific dealer with optional filtering.
  Returns enquiry details including customer info, vehicle preference, and status.
version: "1.0.0"

input_schema:
  type: object
  properties:
    dealer_id:
      type: string
      description: Unique dealer identifier
      pattern: "^DL[0-9]{6}$"
    status:
      type: string
      description: Filter by enquiry status
      enum: [pending, contacted, converted, lost]
    date_from:
      type: string
      format: date
      description: Start date for filtering (YYYY-MM-DD)
    date_to:
      type: string
      format: date
      description: End date for filtering (YYYY-MM-DD)
    limit:
      type: integer
      minimum: 1
      maximum: 100
      default: 20
  required: [dealer_id]

output_schema:
  type: object
  properties:
    enquiries:
      type: array
      items:
        type: object
        properties:
          enquiry_id: {type: string}
          customer_name: {type: string}
          contact_number: {type: string}
          vehicle_model: {type: string}
          status: {type: string}
          created_at: {type: string, format: date-time}
    total_count: {type: integer}
    page_info:
      type: object
      properties:
        has_more: {type: boolean}
        next_cursor: {type: string}

api_config:
  endpoint: /v1/dealers/{dealer_id}/enquiries
  method: GET
  path_params: [dealer_id]
  query_params: [status, date_from, date_to, limit]
  timeout_ms: 10000

security_config:
  risk_level: read
  requires_elevation: false
  allowed_roles: [viewer, operator, admin]
  rate_limit_tier: standard
  audit_level: basic

validation_config:
  allowlist:
    status: [pending, contacted, converted, lost]
  custom_validators:
    - validate_date_range

examples:
  positive:
    - description: Get all enquiries for a dealer
      input:
        dealer_id: DL123456
      output:
        enquiries:
          - enquiry_id: ENQ001
            customer_name: John Doe
            vehicle_model: Swift
            status: pending
        total_count: 1
    
    - description: Filter by status
      input:
        dealer_id: DL123456
        status: pending
      output:
        enquiries: [...]
        total_count: 5
  
  negative:
    - description: Invalid dealer ID format
      input:
        dealer_id: invalid
      error: "dealer_id must match pattern ^DL[0-9]{6}$"
    
    - description: Invalid date range
      input:
        dealer_id: DL123456
        date_from: "2026-01-31"
        date_to: "2026-01-01"
      error: "date_from must be before date_to"

metadata:
  domain: dealer
  journey: enquiry-management
  tags: [dealer, enquiry, read]
  source_spec: dealer-service-v1.yaml
  owner: dealer-team@msil.com
```

### 3.2 Write Tool (Medium Risk)

```yaml
# tools/update_enquiry_status.yaml
name: update_enquiry_status
description: |
  Update the status of a dealer enquiry.
  Triggers notifications to relevant stakeholders.
version: "1.0.0"

input_schema:
  type: object
  properties:
    enquiry_id:
      type: string
      description: Unique enquiry identifier
      pattern: "^ENQ[0-9]{9}$"
    new_status:
      type: string
      description: New status to set
      enum: [contacted, converted, lost]
    notes:
      type: string
      description: Optional notes about the status change
      maxLength: 1000
    follow_up_date:
      type: string
      format: date
      description: Optional follow-up date
  required: [enquiry_id, new_status]

output_schema:
  type: object
  properties:
    success: {type: boolean}
    enquiry:
      type: object
      properties:
        enquiry_id: {type: string}
        previous_status: {type: string}
        new_status: {type: string}
        updated_at: {type: string, format: date-time}
    notifications_sent:
      type: array
      items: {type: string}

api_config:
  endpoint: /v1/enquiries/{enquiry_id}/status
  method: PUT
  path_params: [enquiry_id]
  body_mapping:
    status: new_status
    notes: notes
    follow_up_date: follow_up_date
  timeout_ms: 15000

security_config:
  risk_level: write
  requires_confirmation: true  # Write tools require user_confirmed=true
  requires_elevation: false
  allowed_roles: [operator, admin]
  rate_limit_tier: standard
  audit_level: detailed

validation_config:
  denylist:
    notes:
      - "DROP TABLE"
      - "<script>"
  custom_validators:
    - validate_enquiry_exists
    - validate_status_transition

examples:
  positive:
    - description: Mark enquiry as contacted
      input:
        enquiry_id: ENQ123456789
        new_status: contacted
        notes: Customer interested in Swift ZXi
      output:
        success: true
        enquiry:
          enquiry_id: ENQ123456789
          previous_status: pending
          new_status: contacted
        notifications_sent: [email, sms]
  
  negative:
    - description: Invalid status transition
      input:
        enquiry_id: ENQ123456789
        new_status: pending  # Cannot go back to pending
      error: "Invalid status transition from contacted to pending"

metadata:
  domain: dealer
  journey: enquiry-management
  tags: [dealer, enquiry, write, status]
  source_spec: dealer-service-v1.yaml
  owner: dealer-team@msil.com
```

### 3.3 Privileged Tool (High Risk)

```yaml
# tools/delete_customer_data.yaml
name: delete_customer_data
description: |
  Permanently delete customer data in compliance with DPDP Act.
  This action is IRREVERSIBLE and requires PIM elevation.
version: "1.0.0"

input_schema:
  type: object
  properties:
    customer_id:
      type: string
      description: Customer identifier for data deletion
      pattern: "^CUST[0-9]{10}$"
    deletion_reason:
      type: string
      description: Mandatory reason for deletion
      enum: [customer_request, legal_compliance, data_retention_expired]
    confirmation_code:
      type: string
      description: Two-factor confirmation code
      pattern: "^[0-9]{6}$"
  required: [customer_id, deletion_reason, confirmation_code]

output_schema:
  type: object
  properties:
    success: {type: boolean}
    deletion_reference: {type: string}
    deleted_records:
      type: object
      properties:
        personal_info: {type: integer}
        enquiries: {type: integer}
        bookings: {type: integer}
        communications: {type: integer}
    completed_at: {type: string, format: date-time}

api_config:
  endpoint: /v1/customers/{customer_id}/gdpr-delete
  method: DELETE
  path_params: [customer_id]
  body_mapping:
    reason: deletion_reason
    confirmation: confirmation_code
  timeout_ms: 60000

security_config:
  risk_level: privileged
  requires_confirmation: true  # Privileged tools require user_confirmed=true
  requires_elevation: true     # Also requires PIM elevation
  allowed_roles: [admin]
  rate_limit_tier: strict
  audit_level: full

validation_config:
  custom_validators:
    - validate_customer_exists
    - validate_no_pending_transactions
    - verify_2fa_code

examples:
  positive:
    - description: Delete customer data per DPDP request
      input:
        customer_id: CUST0123456789
        deletion_reason: customer_request
        confirmation_code: "123456"
      output:
        success: true
        deletion_reference: DEL-2026-0001234
        deleted_records:
          personal_info: 1
          enquiries: 5
          bookings: 2
          communications: 15
  
  negative:
    - description: Missing PIM elevation
      input:
        customer_id: CUST0123456789
        deletion_reason: customer_request
        confirmation_code: "123456"
      error: "PIM elevation required for privileged operations"
    
    - description: Customer has pending transaction
      input:
        customer_id: CUST0123456789
        deletion_reason: customer_request
        confirmation_code: "123456"
      error: "Cannot delete customer with pending bookings"

metadata:
  domain: customer
  journey: data-privacy
  tags: [customer, gdpr, dpdp, delete, privileged]
  source_spec: customer-service-v1.yaml
  owner: privacy-team@msil.com
```

---

## 4. OpenAPI Auto-Derivation

### 4.1 Import Process

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              OPENAPI TO MCP TOOL DERIVATION                              │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 1: PARSE OPENAPI SPEC                                                      │   │
│   │                                                                                 │   │
│   │   openapi: 3.0.3                                                                │   │
│   │   paths:                                                                        │   │
│   │     /v1/dealers/{dealerId}/enquiries:                                           │   │
│   │       get:                                                                      │   │
│   │         operationId: getDealerEnquiries   ◀── Tool name source                  │   │
│   │         summary: Get dealer enquiries     ◀── Tool description                  │   │
│   │         parameters:                       ◀── Input schema source               │   │
│   │           - name: dealerId                                                      │   │
│   │             in: path                                                            │   │
│   │             required: true                                                      │   │
│   │             schema:                                                             │   │
│   │               type: string                                                      │   │
│   │         responses:                        ◀── Output schema source              │   │
│   │           '200':                                                                │   │
│   │             content:                                                            │   │
│   │               application/json:                                                 │   │
│   │                 schema:                                                         │   │
│   │                   $ref: '#/components/schemas/EnquiryList'                      │   │
│   │         security:                         ◀── Security config source            │   │
│   │           - oauth2: [dealer.read]                                               │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│                                         ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 2: EXTRACT & TRANSFORM                                                     │   │
│   │                                                                                 │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │ Name Generation                                                       │     │   │
│   │   │                                                                       │     │   │
│   │   │ operationId: getDealerEnquiries                                       │     │   │
│   │   │              │                                                        │     │   │
│   │   │              ▼                                                        │     │   │
│   │   │ tool_name: get_dealer_enquiries (snake_case conversion)               │     │   │
│   │   │                                                                       │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │                                                                                 │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │ Parameter Mapping                                                     │     │   │
│   │   │                                                                       │     │   │
│   │   │ OpenAPI Parameter     →    MCP Input Schema                           │     │   │
│   │   │ ──────────────────         ────────────────                           │     │   │
│   │   │ in: path              →    path_params                                │     │   │
│   │   │ in: query             →    query_params                               │     │   │
│   │   │ in: body              →    body_mapping                               │     │   │
│   │   │ required: true        →    required array                             │     │   │
│   │   │ schema.type           →    properties.type                            │     │   │
│   │   │ schema.pattern        →    properties.pattern                         │     │   │
│   │   │ schema.enum           →    properties.enum + allowlist                │     │   │
│   │   │                                                                       │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │                                                                                 │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │ Security Mapping                                                      │     │   │
│   │   │                                                                       │     │   │
│   │   │ OAuth Scope           →    Risk Level         →    Allowed Roles      │     │   │
│   │   │ ───────────                ──────────              ─────────────      │     │   │
│   │   │ *.read                →    read               →    [viewer+]          │     │   │
│   │   │ *.write               →    write              →    [operator+]        │     │   │
│   │   │ *.admin               →    privileged         →    [admin]            │     │   │
│   │   │ *.delete              →    privileged         →    [admin] + PIM      │     │   │
│   │   │                                                                       │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│                                         ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 3: GENERATE TOOL DEFINITION                                                │   │
│   │                                                                                 │   │
│   │   {                                                                             │   │
│   │     "name": "get_dealer_enquiries",                                             │   │
│   │     "description": "Get dealer enquiries",                                      │   │
│   │     "version": "1.0.0",                                                         │   │
│   │     "input_schema": {...},                                                      │   │
│   │     "output_schema": {...},                                                     │   │
│   │     "api_config": {                                                             │   │
│   │       "endpoint": "/v1/dealers/{dealerId}/enquiries",                           │   │
│   │       "method": "GET",                                                          │   │
│   │       "path_params": ["dealerId"],                                              │   │
│   │       "query_params": ["status", "limit"]                                       │   │
│   │     },                                                                          │   │
│   │     "security_config": {                                                        │   │
│   │       "risk_level": "read",                                                     │   │
│   │       "allowed_roles": ["viewer", "operator", "admin"]                          │   │
│   │     },                                                                          │   │
│   │     "metadata": {                                                               │   │
│   │       "source_spec": "dealer-service-v1.yaml"                                   │   │
│   │     }                                                                           │   │
│   │   }                                                                             │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│                                         ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 4: HUMAN REVIEW & ENRICHMENT                                               │   │
│   │                                                                                 │   │
│   │   ✓ Review generated tool definition                                            │   │
│   │   ✓ Add/improve description for LLM clarity                                     │   │
│   │   ✓ Add positive/negative examples                                              │   │
│   │   ✓ Configure custom validators if needed                                       │   │
│   │   ✓ Set appropriate rate limit tier                                             │   │
│   │   ✓ Add business domain metadata                                                │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Import API

```http
POST /api/admin/tools/import-openapi
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "spec_url": "https://api.msil.com/dealer-service/v1/openapi.yaml",
  "options": {
    "auto_generate_names": true,
    "default_risk_level": "read",
    "scope_to_risk_mapping": {
      "*.read": "read",
      "*.write": "write",
      "*.admin": "privileged"
    },
    "include_paths": ["/v1/dealers/**"],
    "exclude_paths": ["/v1/internal/**"],
    "dry_run": true
  }
}

Response (dry_run=true):
{
  "preview": {
    "tools_to_create": [
      {
        "name": "get_dealer_enquiries",
        "source_operation": "getDealerEnquiries",
        "risk_level": "read"
      },
      {
        "name": "update_enquiry_status",
        "source_operation": "updateEnquiryStatus",
        "risk_level": "write"
      }
    ],
    "tools_to_update": [],
    "warnings": [
      "Operation 'bulkDeleteEnquiries' mapped to privileged risk level"
    ]
  }
}
```

---

## 5. Tool Catalog Structure

```
tools/
├── dealer/
│   ├── get_dealer_enquiries.yaml
│   ├── update_enquiry_status.yaml
│   ├── get_dealer_profile.yaml
│   └── list_dealers.yaml
├── inventory/
│   ├── get_vehicle_inventory.yaml
│   ├── search_vehicles.yaml
│   └── get_vehicle_details.yaml
├── booking/
│   ├── create_booking.yaml
│   ├── get_booking_status.yaml
│   ├── cancel_booking.yaml
│   └── list_bookings.yaml
├── customer/
│   ├── get_customer_profile.yaml
│   ├── update_customer_preferences.yaml
│   └── delete_customer_data.yaml        # Privileged
└── _schemas/
    ├── common.yaml                       # Shared schemas
    ├── pagination.yaml
    └── errors.yaml
```

---

## 6. Tool Versioning

### 6.1 Version Policy

| Change Type | Version Bump | Backward Compatible |
|-------------|--------------|---------------------|
| Add optional parameter | PATCH (1.0.x) | ✅ Yes |
| Add new output field | PATCH (1.0.x) | ✅ Yes |
| Change parameter type | MAJOR (x.0.0) | ❌ No |
| Remove parameter | MAJOR (x.0.0) | ❌ No |
| Change endpoint path | MAJOR (x.0.0) | ❌ No |
| Update description | PATCH (1.0.x) | ✅ Yes |
| Change risk level | MINOR (1.x.0) | ⚠️ Depends |

### 6.2 Deprecation Process

```yaml
# Deprecated tool definition
name: get_dealer_info_v1
version: "1.2.0"
metadata:
  deprecated: true
  deprecation_message: |
    This tool is deprecated and will be removed on 2026-06-01.
    Please use 'get_dealer_profile' instead.
  deprecated_at: "2026-01-01"
  removal_date: "2026-06-01"
  replacement_tool: get_dealer_profile
```

---

*Document Classification: Internal | Last Review: January 31, 2026*
