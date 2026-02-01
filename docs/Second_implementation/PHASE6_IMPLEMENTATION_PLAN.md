# Phase 6: OpenAPI Import & E2E Demo Completion

**Date**: January 31, 2026  
**Duration**: 2-3 days  
**Goal**: Complete end-to-end demo with OpenAPI import, real metrics, and tool management

---

## Implementation Phases

### Phase 6A: OpenAPI Import & Tool Generation (Day 1)
**Priority**: CRITICAL  
**Duration**: 6-8 hours

#### Task 1: OpenAPI Parser Module
**File**: `mcp-server/app/core/openapi/parser.py`
- Parse OpenAPI 3.0/3.1 and Swagger 2.0 specs
- Extract operations and convert to tool definitions
- Generate JSON Schema for inputs from parameters
- Handle authentication schemes
- Support file upload and URL import

#### Task 2: Import API Endpoints
**File**: `mcp-server/app/api/openapi_import.py`
- `POST /api/admin/openapi/upload` - Upload OpenAPI file
- `POST /api/admin/openapi/import-url` - Import from URL
- `GET /api/admin/openapi/preview/{spec_id}` - Preview generated tools
- `POST /api/admin/openapi/approve` - Approve and register tools
- `DELETE /api/admin/openapi/spec/{spec_id}` - Delete spec

#### Task 3: Import UI Page
**File**: `admin-ui/src/pages/Import.tsx`
- File upload with drag-and-drop
- URL input for remote specs
- Preview generated tools
- Edit tool metadata before registration
- Bulk approve tools

#### Task 4: Tool Preview Component
**File**: `admin-ui/src/components/import/ToolPreview.tsx`
- Display tool name, description, schema
- Edit fields inline
- Toggle active/inactive
- Validation indicators

---

### Phase 6B: Real Metrics Collection (Day 1-2)
**Priority**: HIGH  
**Duration**: 4-6 hours

#### Task 5: Metrics Collector
**File**: `mcp-server/app/core/metrics/collector.py`
- Intercept tool execution events
- Record start time, end time, success/failure
- Store in PostgreSQL metrics table
- Async writes to avoid blocking

#### Task 6: Update Tool Executor
**File**: `mcp-server/app/core/tools/executor.py`
- Add metrics collection hooks
- Track execution metadata
- Handle errors and timeouts
- Log to metrics collector

#### Task 7: Update Analytics API
**File**: `mcp-server/app/api/analytics.py`
- Replace mock data with real queries
- Aggregate metrics from database
- Calculate success rates, avg response times
- Generate time-series data

---

### Phase 6C: Tool Management UI (Day 2)
**Priority**: MEDIUM  
**Duration**: 4-5 hours

#### Task 8: Tool Detail Page
**File**: `admin-ui/src/pages/ToolDetail.tsx`
- View full tool details
- Edit tool metadata (name, description)
- Enable/Disable toggle
- Delete tool with confirmation
- View usage statistics

#### Task 9: Tool Management API
**File**: `mcp-server/app/api/admin.py` (update)
- `PUT /api/admin/tools/{tool_id}` - Update tool
- `DELETE /api/admin/tools/{tool_id}` - Delete tool
- `POST /api/admin/tools/{tool_id}/toggle` - Enable/Disable

---

### Phase 6D: Bundle Management (Day 2-3)
**Priority**: MEDIUM  
**Duration**: 4-6 hours

#### Task 10: Bundle Data Model
**File**: `mcp-server/app/models/bundle.py`
- Bundle entity with name, description, version
- Many-to-many relationship with tools
- Status: draft, approved, published

#### Task 11: Bundle API
**File**: `mcp-server/app/api/bundles.py`
- `GET /api/admin/bundles` - List bundles
- `POST /api/admin/bundles` - Create bundle
- `PUT /api/admin/bundles/{id}` - Update bundle
- `POST /api/admin/bundles/{id}/tools` - Add tools to bundle
- `DELETE /api/admin/bundles/{id}/tools/{tool_id}` - Remove tool

#### Task 12: Bundle Management UI
**File**: `admin-ui/src/pages/Bundles.tsx`
- List all bundles
- Create new bundle
- Assign tools to bundle
- Publish/unpublish bundles

---

## File Structure

```
mcp-server/
├── app/
│   ├── core/
│   │   ├── openapi/
│   │   │   ├── __init__.py
│   │   │   ├── parser.py          # NEW
│   │   │   └── validator.py       # NEW
│   │   ├── metrics/
│   │   │   ├── __init__.py
│   │   │   └── collector.py       # NEW
│   │   └── tools/
│   │       ├── executor.py         # UPDATE
│   │       └── registry.py         # UPDATE
│   ├── api/
│   │   ├── openapi_import.py      # NEW
│   │   ├── bundles.py             # NEW
│   │   ├── analytics.py           # UPDATE
│   │   └── admin.py               # UPDATE
│   ├── models/
│   │   ├── bundle.py              # NEW
│   │   └── metric.py              # NEW
│   └── main.py                    # UPDATE (add routers)

admin-ui/
├── src/
│   ├── pages/
│   │   ├── Import.tsx             # NEW
│   │   ├── ToolDetail.tsx         # NEW
│   │   ├── Bundles.tsx            # NEW
│   │   └── Tools.tsx              # UPDATE
│   ├── components/
│   │   ├── import/
│   │   │   ├── OpenAPIUpload.tsx  # NEW
│   │   │   ├── ToolPreview.tsx    # NEW
│   │   │   └── ImportProgress.tsx # NEW
│   │   ├── tools/
│   │   │   ├── ToolEditForm.tsx   # NEW
│   │   │   └── ToolList.tsx       # UPDATE
│   │   └── bundles/
│   │       ├── BundleCard.tsx     # NEW
│   │       └── BundleForm.tsx     # NEW
│   └── lib/
│       └── api.ts                 # UPDATE
```

---

## Database Schema Updates

```sql
-- OpenAPI Specs Table
CREATE TABLE openapi_specs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    version VARCHAR(50),
    file_content TEXT NOT NULL,
    source_url VARCHAR(500),
    uploaded_by VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    tools_generated INTEGER DEFAULT 0
);

-- Tool Bundles Table
CREATE TABLE tool_bundles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    version VARCHAR(50) DEFAULT '1.0.0',
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bundle-Tool Mapping
CREATE TABLE bundle_tools (
    bundle_id UUID REFERENCES tool_bundles(id),
    tool_id UUID REFERENCES tools(id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bundle_id, tool_id)
);

-- Tool Executions (for metrics)
CREATE TABLE tool_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tool_id UUID REFERENCES tools(id),
    tool_name VARCHAR(200) NOT NULL,
    execution_id UUID NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    status VARCHAR(50),
    error_message TEXT,
    input_data JSONB,
    output_data JSONB
);

CREATE INDEX idx_executions_tool ON tool_executions(tool_id);
CREATE INDEX idx_executions_started ON tool_executions(started_at);
```

---

## E2E Demo Flow

### Scenario: "Onboard New API Product"

**Step 1: Upload OpenAPI Spec**
1. Navigate to Import page
2. Upload `customer-api.yaml`
3. System parses and shows preview of 5 tools
4. Edit tool names/descriptions
5. Click "Import Tools"

**Step 2: Organize into Bundle**
1. Navigate to Bundles page
2. Create "Customer Management" bundle
3. Assign imported tools to bundle
4. Set bundle status to "Published"

**Step 3: Test Tool Execution**
1. Open Chat UI
2. Ask: "Find customer details"
3. LLM discovers new tools automatically
4. Execute tool and show results

**Step 4: View Metrics**
1. Navigate to Dashboard
2. See real-time metrics update
3. View tool usage chart with actual data
4. Check recent activity showing real executions

**Step 5: Manage Tools**
1. Navigate to Tools page
2. Click on imported tool
3. Disable tool temporarily
4. Verify it's no longer available to LLM
5. Re-enable tool

---

## Success Criteria

✅ **OpenAPI Import**
- Can upload OpenAPI 3.0 spec
- Generates correct tool definitions
- Shows preview before registration
- Tools available via MCP immediately

✅ **Real Metrics**
- Dashboard shows actual execution counts
- Success rate calculated from real data
- Response times measured accurately
- Charts show time-series data

✅ **Tool Management**
- Can enable/disable tools via UI
- Can edit tool metadata
- Can delete tools with confirmation
- Changes reflect immediately in MCP

✅ **Bundle Management**
- Can create tool bundles
- Can assign tools to bundles
- Can view bundle details
- Bundles organize tools logically

✅ **E2E Demo**
- Complete flow: Upload → Import → Execute → Monitor
- No manual coding required
- Professional UI throughout
- Real data, no mocks

---

## Testing Plan

### Unit Tests
- OpenAPI parser with various spec formats
- Metrics collector accuracy
- Tool registry CRUD operations
- Bundle assignment logic

### Integration Tests
- Upload OpenAPI → Generate tools → Execute
- Tool execution → Metrics collection → Dashboard display
- Enable/Disable tool → Verify MCP availability

### E2E Tests
1. Import OpenAPI spec with 5 operations
2. Verify 5 tools registered
3. Execute each tool via Chat UI
4. Verify metrics recorded
5. Disable 1 tool
6. Verify tool unavailable
7. Re-enable tool
8. Create bundle with tools
9. Publish bundle

---

## Dependencies

### Python Packages (add to requirements.txt)
```
pydantic-openapi-schema>=1.0.0
jsonschema>=4.17.0
openapi-spec-validator>=0.5.0
PyYAML>=6.0
```

### TypeScript Packages (add to admin-ui)
```bash
npm install react-dropzone @types/react-dropzone
npm install react-json-view @types/react-json-view
npm install react-hook-form @hookform/resolvers zod
```

---

## Risk Mitigation

### Risk 1: OpenAPI Parser Complexity
**Mitigation**: Use existing libraries, support limited subset first

### Risk 2: Database Performance
**Mitigation**: Add indexes, use async queries, implement caching

### Risk 3: UI Complexity
**Mitigation**: Reuse existing components, keep UI simple

### Risk 4: Time Constraints
**Mitigation**: Prioritize OpenAPI import, defer bundle management if needed

---

## Rollback Plan

If implementation fails:
1. Keep Phase 5 features working
2. Demo with current tools + design docs
3. Show mockups of missing features
4. Commit to delivery timeline

---

## Delivery Timeline

**Day 1 (8 hours)**
- Task 1-4: OpenAPI Import (6h)
- Task 5: Metrics Collector (2h)

**Day 2 (8 hours)**
- Task 6-7: Real Metrics Integration (4h)
- Task 8-9: Tool Management UI (4h)

**Day 3 (6 hours)**
- Task 10-12: Bundle Management (4h)
- Testing & Bug Fixes (2h)

**Total**: 22 hours over 3 days

---

## Post-Implementation

### Documentation
- Update MCP_PROTOCOL_GUIDE.md
- Create OPENAPI_IMPORT_GUIDE.md
- Update PHASE6_SUMMARY.md
- Create demo script

### Demo Preparation
- Prepare sample OpenAPI files
- Create demo scenario walkthrough
- Record demo video (optional)
- Prepare FAQ for client questions

---

**Status**: Ready to implement  
**Owner**: Development Team  
**Start Date**: January 31, 2026  
**Target Completion**: February 2, 2026
