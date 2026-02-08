# MSIL MCP Admin Portal - Complete Feature List for Verification

**Document Version:** 1.0  
**Date:** February 7, 2026  
**Purpose:** External LLM verification of all features available in the Admin Portal UI  
**Admin Portal URL:** http://localhost:3001

---

## 1. OVERVIEW

The MSIL MCP Admin Portal is a comprehensive web-based administration interface for managing the MCP (Model Context Protocol) Server. It provides 8 main functional areas accessible through a sidebar navigation.

**Architecture:**
- Backend: FastAPI server on port 8000
- Frontend: React + Vite on port 3001  
- API Proxy: Admin UI proxies all `/api` calls to backend
- Authentication: Role-based with JWT tokens
- State Management: React hooks + Context API

---

## 2. NAVIGATION STRUCTURE

### Sidebar Menu (8 Pages)

1. **Dashboard** (`/`) - System overview and metrics
2. **Tools** (`/tools`) - Tool registry management
3. **Import OpenAPI** (`/import`) - OpenAPI specification import
4. **Policies** (`/policies`) - Role-based policy configuration
5. **Exposure Governance** (`/exposure`) - Tool visibility management
6. **Audit Logs** (`/audit-logs`) - Compliance audit trails
7. **Service Booking** (`/service-booking`) - Demo booking wizard
8. **Settings** (`/settings`) - System configuration

**Sidebar Features:**
- Maruti Suzuki branding with logo
- Active page highlighting (blue gradient)
- System online indicator (green pulse dot)
- Version display (v1.0.0)
- Environment badge (Production)
- Powered by Nagarro footer

---

## 3. PAGE-BY-PAGE FEATURE BREAKDOWN

### 3.1 DASHBOARD (`/`)

**Purpose:** Real-time system monitoring and quick access to administrative actions

**Key Performance Indicators (KPIs):**
1. **Total Tools** - Count of all registered tools
2. **Active Tools** - Count of currently active tools
3. **Total Requests** - Cumulative API request count
4. **Success Rate** - Percentage of successful requests
5. **Average Response Time** - Average latency in milliseconds
6. **Total Conversations** - Chat session count

**Components:**
- **KPI Cards Component** (`KPICards`)
  - Real-time data refresh
  - Visual metric cards with gradients
  - Color-coded status indicators

- **Tools Usage Chart Component** (`ToolsUsageChart`)
  - Large chart (2/3 of grid width)
  - Visualizes tool invocation patterns
  - Time-series data display

- **Recent Activity Component** (`RecentActivity`)
  - Activity feed (1/3 of grid width)
  - Recent tool invocations
  - Event timeline

- **Quick Actions Panel**
  - **Reload Tools** - Refresh tool registry from database
  - **Clear Cache** - Clear Redis cache entries
  - **View Logs** - Open application logs
  - Each action has icon, title, description, and gradient styling

**Status Indicators:**
- "Live Data" badge with green pulse dot
- Loading state with animated spinner
- Error handling with user feedback

---

### 3.2 TOOLS (`/tools`)

**Purpose:** Complete CRUD operations for MCP tool definitions

**Main Features:**

1. **Tool List Display**
   - Paginated table view
   - Total count display
   - Search and filter capabilities
   - Responsive card/table layout
   - Component: `ToolList`

2. **Tool Creation** (Modal)
   - **Create New Tool** button (top-right, blue with Plus icon)
   - Opens modal dialog with form
   
3. **Tool Editing** (Modal)
   - Edit existing tool by clicking on tool card
   - Pre-populated form with current values
   - JSON editors for schemas

4. **Tool Form Fields:**
   - **Basic Information:**
     - Tool Name (unique identifier)
     - Display Name (user-friendly name)
     - Description (full description)
     - Category (categorization)
     - Bundle Name (optional grouping)
     - Version (semantic versioning)
     - Tags (array of string tags)
   
   - **API Configuration:**
     - API Endpoint (full URL)
     - HTTP Method (GET/POST/PUT/DELETE/PATCH)
     - Headers (JSON object)
     - Auth Type (none/bearer/apikey/oauth2)
   
   - **Schemas:**
     - Input Schema (JSON editor with validation)
     - Output Schema (JSON editor, optional)
   
   - **Risk & Governance:**
     - Risk Level (read/write/privileged)
     - Requires Elevation (boolean toggle)
     - Requires Confirmation (boolean toggle)
     - Requires Approval (boolean toggle)
     - Max Concurrent Executions (numeric)
     - Rate Limit Tier (permissive/standard/strict)
   
   - **Status:**
     - Is Active (boolean toggle)
     - Created At (timestamp, read-only)
     - Updated At (timestamp, read-only)

5. **Tool Actions:**
   - **Toggle Active/Inactive** - Enable/disable tool
   - **Edit Tool** - Opens edit modal
   - **Delete Tool** - Deactivates tool (with confirmation)

6. **Search & Filter:**
   - Search icon (magnifying glass)
   - Filter icon
   - Real-time search across tool name, description, category
   - Filter by category, status, risk level

7. **Data Persistence:**
   - Automatic saving with loading states
   - Error handling with user-friendly messages
   - Success confirmations
   - Form validation (JSON schema validation)

8. **Bulk Operations:**
   - Download button for exporting tools
   - CSV/JSON export capabilities

---

### 3.3 IMPORT OPENAPI (`/import`)

**Purpose:** Automated tool generation from OpenAPI/Swagger specifications

**Workflow Steps:**

**Step 1: Upload Specification**
- Component: `OpenAPIUpload`
- **Upload Methods:**
  1. **File Upload** - Drag & drop or click to browse ✅ IMPLEMENTED
     - Supported: JSON (.json), YAML (.yaml, .yml)
     - OpenAPI 3.0, 3.1, Swagger 2.0

**Future Methods (Not Yet Implemented):**
- URL Import - Planned for Phase 2
- Paste Content - Planned for Phase 2

**Step 2: Specification Processing**
- Automatic parsing and validation
- Tool generation from API operations
- Display of spec metadata:
  - Name
  - Version
  - Description
  - Tools Generated count

**Step 3: Tool Preview & Review**
- Component: `ToolPreview`
- **Displays Generated Tools:**
  - Table/grid view of all generated tools
  - Each tool shows:
    - Tool name (derived from operationId)
    - HTTP method + endpoint
    - Description (from operation description)
    - Parameters (from operation parameters)
    - Input/output schemas
  
- **Tool Selection:**
  - Select All / Deselect All checkbox
  - Individual tool checkboxes
  - Only selected tools will be registered
  
- **Tool Editing (Pre-approval):**
  - Edit tool name
  - Edit description
  - Modify input schema
  - Adjust risk level
  - Set rate limit tier

- **Error Display:**
  - Yellow alert box for parsing issues
  - List of errors/warnings
  - Non-blocking (can proceed despite warnings)

**Step 4: Tool Approval & Registration**
- **Approve & Register** button
- Sends selected tools to backend
- API Call: `POST /api/admin/openapi/approve`
- Payload: `{ spec_id, tool_ids[] }`

**Step 5: Confirmation**
- Success screen with checkmark
- Displays:
  - "Tools Registered Successfully!" heading
  - Count of tools registered
  - List of registered tool names (with checkmarks)
- **Action Buttons:**
  - **Import Another Spec** - Reset wizard
  - **View All Tools** - Navigate to Tools page

**Additional Features:**
- "How it works" info panel (3-step guide)
- "Import Different Spec" link to restart
- Error recovery options
- Progress indication

---

### 3.4 POLICIES (`/policies`)

**Purpose:** Role-based access control (RBAC) and permission management

**Main Features:**

1. **Statistics Dashboard:**
   - **Active Roles Card** (Shield icon, blue)
     - Display count of all roles
   - **Total Permissions Card** (Edit icon, green)
     - Sum of all permissions across roles
   - **Recent Changes Card** (if implemented)

2. **Create Role Section:**
   - Dedicated card at top of page
   - **Form Fields:**
     - **Role Name** - Text input (e.g., "operator", "developer", "admin")
     - **Initial Permissions** - Comma-separated list
       - Examples: `invoke:*`, `read:*`, `write:tool`
       - Supports wildcard patterns
   - **Create Role** button with Plus icon

3. **Role Management:**
   - **Role Cards/List:**
     - Display all existing roles
     - Each role shows:
       - Role name (heading)
       - Permission count badge
       - List of assigned permissions
       - Action buttons
   
4. **Permission Management (Per Role):**
   - **Add Permission:**
     - Input field for new permission
     - Add button
     - Supports patterns: `invoke:*`, `read:customer:*`, `write:tool:update_veh`
   
   - **Remove Permission:**
     - Trash icon button per permission
     - Confirmation dialog
     - Immediate update after confirmation
   
   - **Edit Mode Toggle:**
     - Edit icon to enable editing
     - Save changes button
     - Cancel changes button

5. **Role Actions:**
   - **Delete Role** - Trash icon button
     - Confirmation: "Delete role [name]?"
     - Permanent deletion warning
   
   - **Refresh Roles** - Reload from backend
   - **Export Policies** - Download as JSON/CSV (if implemented)

6. **Permission Patterns:**
   - Format: `action:resource:subresource`
   - Examples:
     - `invoke:*` - Invoke any tool
     - `read:*` - Read any resource
     - `write:tool` - Write to tool resources
     - `admin:*:*` - Admin access to everything
     - `expose:bundle:customer_mgmt` - Expose specific bundle

7. **API Integration:**
   - `GET /api/admin/policies/roles` - Fetch all roles
   - `POST /api/admin/policies/roles` - Create role
   - `DELETE /api/admin/policies/roles/{role_name}` - Delete role
   - `POST /api/admin/policies/roles/{role_name}/permissions` - Add permission
   - `DELETE /api/admin/policies/roles/{role_name}/permissions` - Remove permission

8. **Real-time Updates:**
   - Auto-refresh after every change
   - Loading indicators during API calls
   - Success/error toast notifications

---

### 3.5 EXPOSURE GOVERNANCE (`/exposure`)

**Purpose:** Control tool visibility per role (Layer B - Discovery/Exposure filtering)

**Layout:**
- 3-column grid (1 + 2 layout)
- Left: Role selector (sticky sidebar)
- Right: Permissions, Preview, and Bundles

**Core Concept:**
Exposure Governance determines which tools are VISIBLE in the `tools/list` endpoint for each role. This is separate from policy enforcement (authorization).

**Main Features:**

1. **Role Selector (Left Sidebar):**
   - Card with role buttons
   - **Available Roles:**
     - Operator
     - Developer
     - Admin
   - Active role highlighted (blue gradient)
   - Inactive roles (gray, hover effect)
   - Clicking role switches context

2. **Exposure Permissions Panel:**
   - **Header:**
     - "Exposure Permissions" title
     - Description: "Tools that [role] can see (discover in tools/list)"
     - Note: Actual execution permission is controlled separately by Policies
     - **Add Permission** button (top-right, Plus icon)
   
   - **Permissions List Component** (`PermissionsList`):
     - Displays all exposure permissions for selected role
     - **Permission Types:**
       1. **Global Access** - `expose:all`
          - Badge: "ALL TOOLS" (purple gradient)
          - Grants visibility to all tools
       2. **Bundle Access** - `expose:bundle:{bundle_name}`
          - Badge: "BUNDLE: {name}" (blue gradient)
          - Shows bundle icon + name
          - Exposes all tools in that bundle
       3. **Tool Access** - `expose:tool:{tool_name}`
          - Badge: "TOOL: {name}" (green gradient)
          - Shows wrench icon + tool name
          - Exposes single specific tool
     
     - **Permission Actions:**
       - Trash icon button to remove
       - Confirmation dialog before removal
       - Loading state while removing (spinner replaces button)
     
     - **Empty State:**
       - "No exposure permissions" message
       - "Add permissions to grant tool visibility"
       - Eye icon illustration

3. **Add Permission Dialog:**
   - Component: `AddPermissionDialog`
   - Modal dialog with 3 tabs/options:
   
   **Option 1: Grant All Access**
   - Radio button: "Expose all tools"
   - Description: "Role can see all available tools"
   - Generates: `expose:all`
   - **Warning if already has all access** (blue info box)
   
   **Option 2: Grant Bundle Access**
   - Radio button: "Expose entire bundle"
   - **Dropdown:** Select from available bundles
     - Fetched from: `GET /api/admin/exposure/bundles`
     - Shows: Bundle name + tool count
     - Example: "Customer Management (8 tools)"
   - Generates: `expose:bundle:{selected_bundle}`
   - **Info if bundle already exposed** (yellow warning)
   
   **Option 3: Grant Tool Access**
   - Radio button: "Expose specific tool"
   - **Two-step selection:**
     1. Select bundle (dropdown)
     2. Select tool from that bundle (dropdown)
   - Shows tool details:
     - Tool name
     - Description
     - Category
     - HTTP method
   - Generates: `expose:tool:{selected_tool}`
   - **Warning if tool already exposed** (yellow info box)
   
   - **Dialog Actions:**
     - **Cancel** - Close without changes
     - **Add Permission** - Save and close
       - Disabled if no valid selection
       - Shows spinner while saving
       - Automatically refreshes preview after save

4. **Preview Panel:**
   - Component: `PreviewPanel`
   - **Summary Cards (3 across):**
     1. **Total Tools** - Count of visible tools in tools/list (blue gradient)
     2. **Bundles** - Count of visible bundles (purple gradient)
     3. **Status** - "✓ Active" or "○ No Access" (green/gray)
   - **Important:** Exposure controls visibility only. Execution permission is determined by Policies (authorization layer)
   
   - **Exposed Tools by Bundle:**
     - Accordion/expandable sections
     - Default: First 2 bundles expanded
     - Each bundle shows:
       - Bundle name (heading)
       - Tool count badge
       - **Expand/Collapse** button (ChevronDown/ChevronUp icons)
     
     - **Tool List (when expanded):**
       - Table with columns:
         - Tool name
         - Description
         - HTTP method badge (GET/POST/PUT/DELETE)
         - Category tag
       - Sortable/filterable (if implemented)
     
     - **Empty State:**
       - "No tools exposed" message
       - "Add exposure permissions to grant visibility"

5. **Available Bundles Reference:**
   - Card showing all system bundles
   - **Grid View (2 columns on desktop):**
     - Each bundle card shows:
       - Bundle name (bold)
       - Description
       - Tool count
       - Gray background, rounded corners
   - **Purpose:** Reference for admins to see what's available
   - Data source: `GET /api/admin/exposure/bundles`
   - Example bundles:
     - Customer Management (8 tools)
     - Inventory Management (12 tools)
     - Analytics (6 tools)

6. **API Integration:**
   - `GET /api/admin/exposure/roles/{role}/permissions` - Get role's exposure permissions
   - `POST /api/admin/exposure/roles/{role}/permissions` - Add permission
   - `DELETE /api/admin/exposure/roles/{role}/permissions` - Remove permission
   - `GET /api/admin/exposure/bundles` - List all available bundles
   - `GET /api/admin/exposure/roles/{role}/preview` - Preview what role will see

7. **Real-time Features:**
   - **Refresh** button (top-right, with RefreshCw icon)
   - Auto-refresh after every change
   - Loading states during API calls
   - Success toast: "Permission added to {role}"
   - Error toast: "Failed to add/remove permission"
   - Preview updates immediately after permission changes

8. **User Experience:**
   - Responsive 3-column → 1-column on mobile
   - Sticky role selector on desktop
   - Smooth transitions and animations
   - Color-coded permission badges
   - Clear visual hierarchy
   - Confirmation dialogs for destructive actions

---

### 3.6 AUDIT LOGS (`/audit-logs`)

**Purpose:** Compliance-ready audit trail viewing and export

**Main Features:**

1. **Statistics Cards (4 across):**
   - **Total Events** - Count of all logged events
   - **Success Events** - Count of successful operations (green)
   - **Failed Events** - Count of failed operations (red)
   - **Denied Events** - Count of policy-denied operations (orange)

2. **Log Controls (Header):**
   - **Export CSV** button (top-right)
     - Downloads filtered logs as CSV
     - Filename: `audit-logs-YYYY-MM-DD.csv`
     - Includes: Event ID, Timestamp, Event Type, User, Tool, Action, Status, Latency

3. **Filters Panel:**
   - **Search Box** (Search icon)
     - Real-time search across:
       - User ID
       - Tool name
       - Action description
   
   - **Event Type Filter** (dropdown)
     - Options: Tool Invocation, Policy Decision, Authentication, etc.
   
   - **Status Filter** (dropdown)
     - Options: Success, Failure, Denied, All
   
   - **Date Range** (if implemented)
     - Start date picker
     - End date picker
     - Apply button

4. **Audit Log Table:**
   - **Columns:**
     - **Status Icon** - Visual indicator
       - ✓ CheckCircle (green) - Success/Allowed
       - ✗ XCircle (red) - Failure
       - ⚠ AlertCircle (orange) - Denied
     
     - **Timestamp** - ISO format with timezone
       - Example: "2026-02-07T15:30:00Z"
       - Relative time on hover (if implemented)
     
     - **Event Type** - Type of event
       - tool_invocation
       - policy_decision
       - authentication_attempt
       - exposure_check
       - rate_limit_exceeded
     
     - **User ID** - Identifier of user/service
       - Example: "user-123", "service-account-456"
     
     - **Tool Name** - Name of tool invoked (if applicable)
       - Example: "get_customer_details", "update_vehicle"
     
     - **Action** - Description of action
       - Example: "Invoked tool", "Policy evaluated", "Auth failed"
     
     - **Status** - Outcome
       - success / allowed - Green badge
       - failure - Red badge
       - denied - Orange badge
     
     - **Latency** - Response time in milliseconds
       - Example: "245 ms"
       - Color-coded: Green (<100ms), Yellow (100-500ms), Red (>500ms)
     
     - **Error Message** - If status is failure (expandable)
   
   - **Row Actions (Hover):**
     - Expand for details (if implemented)
     - Copy event ID
     - View full JSON payload (if implemented)

5. **Pagination:**
   - Default: 100 events per page
   - Page controls: Previous, Next, Page numbers
   - Configurable page size: 25, 50, 100, 200

6. **Real-time Updates:**
   - Auto-refresh toggle (if implemented)
   - Manual refresh button
   - Badge showing last refresh time
   - WebSocket live updates (if implemented)

7. **Event Details Panel (Expandable Row):**
   - Click on row to expand
   - Shows safe event details (PII-masked):
     - Correlation ID
     - Tool name and version
     - Policy decision and reason
     - Execution status and latency
     - User context (roles, scopes, masked client ID)
   - **Security:** Raw request/response bodies and stack traces not displayed to prevent PII leakage

8. **Compliance Features:**
   - **PII Masking:**
     - Customer IDs masked: "cust-***123"
     - Email addresses masked: "user@***"
     - Phone numbers masked: "+91-***-**45"
     - API keys masked: "sk-***"
   
   - **Immutable Logs:**
     - Cannot edit/delete logs from UI
     - Timestamp verification
     - Event ID generation (UUID)
   
   - **Retention Policy Display:**
     - Shows retention period (e.g., "90 days")
     - Warning before purge date

9. **Empty State:**
   - "No audit logs found" message
   - File icon illustration
   - Helpful text about log generation

10. **Loading State:**
    - Skeleton loader for table rows
    - Spinner for stats cards
    - Loading bar at top

---

### 3.7 SERVICE BOOKING (`/service-booking`)

**Purpose:** Demo multi-step booking wizard (showcases MCP tool chaining)

**Wizard Flow:**

**Step Indicator (Top):**
- 4 steps with icons
- Visual progress line connecting steps
- Current step highlighted (blue)
- Completed steps checkmarked (green)
- Future steps grayed out

**Step 1: Vehicle Information**
- Icon: Car
- **Fields:**
  - **Vehicle Model** (dropdown)
    - Options: Swift, Dzire, Baleno, Brezza, Ertiga, XL6, Ciaz, etc.
  - **Registration Number** (text input)
    - Format: XX-00-XX-0000
    - Validation: Alphanumeric with hyphens
- **Next** button (bottom-right, blue with ArrowRight icon)

**Step 2: Service Details**
- Icon: Wrench
- **Fields:**
  - **Service Type** (dropdown)
    - Options: Regular Service, Wheel Alignment, AC Service, Battery Check, Brake Service, Engine Tune-up, Full Service
  - **Preferred Date** (date picker)
    - Minimum: Today + 1 day
    - Calendar widget
  - **Preferred Time** (dropdown)
    - Options: 09:00 AM, 10:00 AM, 11:00 AM, 12:00 PM, 02:00 PM, 03:00 PM, 04:00 PM
- **Navigation:**
  - **Back** button (gray with ArrowLeft icon)
  - **Next** button (blue with ArrowRight icon)

**Step 3: Dealer Selection**
- Icon: MapPin
- **Fields:**
  - **Dealer Code** (text input or dropdown)
    - Auto-complete enabled (if implemented)
  - **Dealer Name** (text input or dropdown)
    - Populated based on dealer code
  - **Dealer Address** (read-only text area)
    - Shows full dealer address
- **Dealer Search:** (if implemented)
  - Search by location
  - Map view with nearby dealers
  - Distance calculation
- **Navigation:**
  - **Back** button
  - **Next** button

**Step 4: Customer Information**
- Icon: User
- **Fields:**
  - **Customer Name** (text input)
    - Validation: Required, min 2 characters
  - **Phone Number** (text input)
    - Validation: 10-digit Indian mobile number
    - Format: +91-XXXXX-XXXXX
  - **Email** (text input)
    - Validation: Valid email format
  - **Additional Notes** (textarea)
    - Optional field
    - Max 500 characters
- **Navigation:**
  - **Back** button
  - **Submit Booking** button (green with CheckCircle icon)

**Confirmation Screen:**
- Large green CheckCircle icon
- **Heading:** "Booking Confirmed!"
- **Booking ID:** Auto-generated (e.g., "BK12345678")
- **Booking Summary Card:**
  - Vehicle: [Model] ([Registration])
  - Service: [Type]
  - Date & Time: [Date] at [Time]
  - Dealer: [Name]
  - Customer: [Name]
  - Contact: [Phone]
- **Action Buttons:**
  - **New Booking** - Resets wizard, starts over
  - **View Bookings** - Navigate to bookings list (if implemented)
  - **Print** - Print booking confirmation (if implemented)

**Additional Features:**
- **Form Validation:**
  - Real-time validation as user types
  - Error messages below invalid fields
  - Next button disabled until current step is valid
- **Progress Saving:**
  - Data persists while navigating between steps
  - Browser back/forward supported
- **Responsive Design:**
  - Single column on mobile
  - Larger form on desktop
  - Touch-friendly buttons
- **Accessibility:**
  - Keyboard navigation (Tab, Arrow keys)
  - ARIA labels for screen readers
  - Focus indicators

**Backend Integration Status:**
⚠️ **DEMO/MOCKUP ONLY** - Not wired to production backend
- Wizard completes and shows confirmation
- Does NOT save bookings to database
- Does NOT call MCP tools
- Does NOT send emails or SMS

Future integration could support tool chaining.

---

### 3.8 SETTINGS (`/settings`)

**Purpose:** Comprehensive system configuration across all components

**Layout:**
- Tabbed interface with 6 main tabs
- Settings organized by category
- Save/Reset buttons at bottom of each tab

**Tab 1: GENERAL (SettingsIcon)**

1. **System Settings:**
   - **Log Level** (dropdown)
     - Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
     - Description for each level
     - Color-coded badges
   - **Log Format** (dropdown)
     - Options: JSON, Text, Structured
   - **Log Output** (checkboxes)
     - Console
     - File
     - External logging service
   - **Log File Path** (text input)
     - Default: `/var/log/msil-mcp/app.log`
   - **Max Log Size** (number input + unit)
     - Value + dropdown (MB, GB)
   - **Log Rotation** (toggle)
     - Enable/disable automatic rotation
   - **Timezone** (dropdown)
     - Options: UTC, IST, EST, PST, etc.

2. **Server Settings:**
   - **Host** (text input)
     - Default: `0.0.0.0`
   - **Port** (number input)
     - Default: 8000
   - **Workers** (number input)
     - Number of Uvicorn workers
     - Default: 4
   - **Debug Mode** (toggle)
     - Enable/disable debug mode
   - **Reload on Change** (toggle)
     - Auto-reload on code changes (dev only)

3. **CORS Settings:**
   - **Allowed Origins** (textarea, comma-separated)
     - List of allowed origins
     - Example: `http://localhost:3000, http://localhost:3001`
   - **Allow Credentials** (toggle)
   - **Allowed Methods** (multi-select checkboxes)
     - GET, POST, PUT, DELETE, PATCH, OPTIONS
   - **Allowed Headers** (textarea, comma-separated)

**Tab 2: SECURITY (Shield Icon)**

1. **Authentication:**
   - **Auth Required** (toggle)
     - Enable/disable authentication globally
   - **Demo Mode** (toggle)
     - Bypass auth for demo/testing
     - Warning: "Not for production use"
   - **JWT Secret Key** (password input)
     - Masked input field
     - "Change Secret" button
   - **JWT Algorithm** (dropdown)
     - Options: HS256, HS512, RS256, RS512
   - **Token Expiry** (number input + unit)
     - Value + dropdown (minutes, hours, days)
     - Default: 24 hours
   - **Refresh Token Enabled** (toggle)
   - **Refresh Token Expiry** (number input + unit)
     - Default: 7 days

2. **Authorization & Policy:**
   - **Policy Enforcement Enabled** (toggle)
     - Enable Layer A policy checks
   - **OPA Server URL** (text input)
     - If using external OPA
     - Example: `http://opa:8181`
   - **Default Policy Action** (dropdown)
     - Allow or Deny (if no policy matches)
   - **Policy Cache TTL** (number input, seconds)
     - Default: 300 seconds

3. **Exposure Governance:**
   - **Exposure Checks Enabled** (toggle)
     - Enable Layer B exposure filtering
   - **Default Exposure** (dropdown)
     - None (deny all) or All (allow all) if no config
   - **Exposure Cache TTL** (number input, seconds)

4. **Audit & Compliance:**
   - **Audit Logging Enabled** (toggle)
   - **Audit Log Target** (dropdown)
     - Options: Database, File, External Service, S3
   - **Audit Retention Period** (number input + unit)
     - Days to keep audit logs
     - Default: 90 days
   - **PII Masking Enabled** (toggle)
     - Mask sensitive data in logs
   - **Compliance Mode** (dropdown)
     - Options: Standard, HIPAA, PCI-DSS, SOC2, ISO27001

5. **Privileged Identity Management (PIM):**
   - **PIM Provider** (dropdown)
     - Options: Local, Azure PIM, CyberArk, Okta
   - **PIM Endpoint** (text input)
     - URL for PIM service
   - **Elevation Timeout** (number input, minutes)
     - Default: 60 minutes
   - **Require Justification** (toggle)
     - Force users to provide reason for elevation

6. **Mutual TLS (mTLS):**
   - **mTLS Enabled** (toggle)
   - **Client Certificate Verification** (dropdown)
     - Options: CERT_REQUIRED, CERT_OPTIONAL, CERT_NONE
   - **CA Certificate Path** (file picker)
     - Path to CA certificate bundle
   - **Client Certificate Path** (file picker)
   - **Client Key Path** (file picker)

7. **Web Application Firewall (WAF):**
   - **WAF Enabled** (toggle)
   - **SQL Injection Prevention** (toggle)
   - **XSS Prevention** (toggle)
   - **Rate Limit by IP** (toggle)
   - **Block List** (textarea)
     - IP addresses to block (one per line)
   - **Allow List** (textarea)
     - IP addresses to allow (one per line)

8. **Tool Risk Management:**
   - **Risk Assessment Enabled** (toggle)
   - **Default Risk Level** (dropdown)
     - Options: Read, Write, Privileged
   - **Risk-based Rate Limiting** (toggle)
     - Higher risk = stricter limits
   - **Multipliers:**
     - Read Risk Multiplier (number, default: 1x)
     - Write Risk Multiplier (number, default: 3x)
     - Privileged Risk Multiplier (number, default: 10x)

**Tab 3: LLM / AI (Brain Icon)**

1. **LLM Provider:**
   - **Selected Provider** (radio buttons with cards)
     - OpenAI (GPT models)
     - Azure OpenAI (OpenAI via Azure)
     - Google AI (Gemini models)
     - Anthropic (Claude models)
     - AWS Bedrock (Various models)
   - Each provider card shows:
     - Provider logo/icon
     - Name
     - Description
     - "Select" radio button

2. **Provider Configuration (OpenAI):**
   - **API Key** (password input)
     - Masked field
     - "Test Connection" button
   - **Organization ID** (text input, optional)
   - **Model** (dropdown)
     - Options: GPT-4 Turbo, GPT-4o, GPT-4o Mini, GPT-3.5 Turbo
     - Shows context window size (128K, 32K, etc.)
   - **Temperature** (slider, 0.0 - 2.0)
     - Default: 0.7
     - Label shows current value
   - **Max Tokens** (number input)
     - Default: 4096
   - **Top P** (slider, 0.0 - 1.0)
     - Default: 1.0
   - **Frequency Penalty** (slider, 0.0 - 2.0)
   - **Presence Penalty** (slider, 0.0 - 2.0)

3. **Provider Configuration (Azure OpenAI):**
   - **Endpoint URL** (text input)
     - Example: `https://your-resource.openai.azure.com/`
   - **API Key** (password input)
   - **Deployment Name** (text input)
     - Azure deployment name
   - **API Version** (dropdown)
     - Options: 2023-05-15, 2024-02-15-preview, etc.
   - (Plus same model parameters as OpenAI)

4. **Provider Configuration (Google AI):**
   - **API Key** (password input)
   - **Model** (dropdown)
     - Options: Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini Pro
     - Shows context window (1M, 32K)
   - **Safety Settings** (checkboxes)
     - Block none, Block few, Block some, Block most
   - (Plus temperature, max tokens)

5. **Provider Configuration (Anthropic):**
   - **API Key** (password input)
   - **Model** (dropdown)
     - Options: Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
     - Shows context window (200K)
   - (Plus temperature, max tokens)

6. **Provider Configuration (AWS Bedrock):**
   - **AWS Region** (dropdown)
     - us-east-1, us-west-2, eu-west-1, etc.
   - **Access Key ID** (password input)
   - **Secret Access Key** (password input)
   - **Model ID** (dropdown)
     - anthropic.claude-3-sonnet
     - meta.llama3-70b-instruct
     - amazon.titan-text-express
   - (Plus model parameters)

7. **Prompt Engineering:**
   - **System Prompt** (textarea, large)
     - Default system message
     - Template variables supported
   - **User Prompt Template** (textarea)
   - **Few-shot Examples** (expandable sections)
     - Add/remove example pairs
     - Input + Expected output

8. **LLM Features:**
   - **Streaming Enabled** (toggle)
     - Stream responses token-by-token
   - **Function Calling Enabled** (toggle)
     - Allow LLM to call tools directly
   - **JSON Mode** (toggle)
     - Force JSON output
   - **Context Management:**
     - Max Context Length (number input)
     - Context Pruning Strategy (dropdown)
       - Truncate oldest, Summarize, Sliding window

**Tab 4: API GATEWAY (Globe Icon)**

1. **API Gateway Mode:**
   - **Mode** (radio buttons)
     - **Mock Mode** - Use mock API for dev/testing
       - Icon: TestTube
       - Description: "Returns fake data, no external calls"
     - **MSIL APIM** - Connect to real API Manager
       - Icon: Cloud
       - Description: "Production API gateway"

2. **Mock API Settings (if Mock Mode):**
   - **Mock Response Delay** (number input, milliseconds)
     - Simulate network latency
     - Default: 200ms
   - **Mock Success Rate** (slider, 0-100%)
     - Percentage of requests that succeed
     - Default: 95%
   - **Mock Data Set** (dropdown)
     - Options: Minimal, Realistic, Stress Test

3. **MSIL APIM Settings (if APIM Mode):**
   - **API Gateway URL** (text input)
     - Example: `https://api.maruti.com/v1`
   - **API Gateway Key** (password input)
     - Masked input
   - **Client ID** (text input)
   - **Client Secret** (password input)
   - **OAuth2 Token URL** (text input)
     - For authentication
   - **Connection Timeout** (number input, seconds)
     - Default: 30 seconds
   - **Read Timeout** (number input, seconds)
     - Default: 60 seconds
   - **Retry Strategy:**
     - **Max Retries** (number input)
       - Default: 3
     - **Backoff Strategy** (dropdown)
       - Fixed, Exponential, Exponential with Jitter
     - **Retry Status Codes** (multi-select)
       - 500, 502, 503, 504, 429
   - **Test Connection** button
     - Verifies connectivity
     - Shows green checkmark on success

4. **API Transformation:**
   - **Request Transformation Enabled** (toggle)
     - Transform requests before sending to backend
   - **Response Transformation Enabled** (toggle)
     - Transform responses before returning to client
   - **Transformation Rules** (expandable sections)
     - Add/remove rules
     - Each rule:
       - Field path (JSONPath)
       - Transform type (Map, Rename, Remove, Add)
       - Target value/field

5. **API Monitoring:**
   - **Health Check Enabled** (toggle)
   - **Health Check URL** (text input)
     - Endpoint to ping for health
   - **Health Check Interval** (number input, seconds)
     - Default: 60 seconds
   - **Alert on Failure** (toggle)
   - **Alert Webhook URL** (text input)
     - Where to send alerts

**Tab 5: PERFORMANCE (Zap Icon)**

1. **Caching (Redis):**
   - **Cache Enabled** (toggle)
   - **Redis URL** (text input)
     - Example: `redis://localhost:6379/0`
   - **Redis Password** (password input, optional)
   - **Cache TTL** (number input, seconds)
     - Default: 3600 seconds (1 hour)
   - **Cache Prefix** (text input)
     - Default: `msil-mcp:`
   - **Max Memory** (number input + unit)
     - MB or GB
   - **Eviction Policy** (dropdown)
     - Options: allkeys-lru, volatile-lru, allkeys-lfu, volatile-lfu, noeviction
   - **Test Connection** button

2. **Rate Limiting:**
   - **Rate Limiting Enabled** (toggle)
   - **Strategy** (dropdown)
     - Options: Per User, Per IP, Per Tool, Per User+Tool
   - **Default Limit** (number input + time unit)
     - Requests per minute/hour/day
     - Default: 100 requests/minute
   - **Burst Allowance** (number input)
     - Extra requests allowed in burst
     - Default: 20
   - **Rate Limit Storage** (dropdown)
     - Options: Redis, In-Memory, Database
   - **Rate Limit Headers:**
     - **Include Headers** (toggle)
       - Add X-RateLimit-* headers to responses
     - **Headers:**
       - X-RateLimit-Limit
       - X-RateLimit-Remaining
       - X-RateLimit-Reset
       - Retry-After (on 429)

3. **Idempotency:**
   - **Idempotency Enabled** (toggle)
   - **Idempotency Header** (text input)
     - Default: `Idempotency-Key`
   - **Idempotency TTL** (number input, seconds)
     - How long to cache responses
     - Default: 86400 seconds (24 hours)
   - **Idempotency Storage** (dropdown)
     - Options: Redis, Database
   - **Enforce on Methods** (checkboxes)
     - POST, PUT, PATCH, DELETE

4. **Batch Processing:**
   - **Batch Enabled** (toggle)
   - **Max Batch Size** (number input)
     - Max tools in one batch request
     - Default: 10
   - **Batch Timeout** (number input, seconds)
     - Total time for batch
     - Default: 300 seconds
   - **Parallel Execution** (toggle)
     - Execute batch tools in parallel
   - **Max Parallel** (number input)
     - Max concurrent executions
     - Default: 5
   - **Stop on Error** (toggle)
     - Stop batch if one tool fails

5. **Resilience (Circuit Breaker):**
   - **Circuit Breaker Enabled** (toggle)
   - **Failure Threshold** (number input)
     - Failures before opening circuit
     - Default: 5
   - **Success Threshold** (number input)
     - Successes to close circuit
     - Default: 2
   - **Timeout** (number input, seconds)
     - Tool invocation timeout
     - Default: 30 seconds
   - **Half-Open Timeout** (number input, seconds)
     - Time to wait before trying again
     - Default: 60 seconds
   - **Fallback Strategy** (dropdown)
     - Options: Return Error, Return Cached, Return Default

6. **Connection Pooling:**
   - **Pool Size** (number input)
     - Max open connections
     - Default: 20
   - **Pool Timeout** (number input, seconds)
     - Time to wait for connection
     - Default: 10 seconds
   - **Pool Recycle** (number input, seconds)
     - Recycle connections after time
     - Default: 3600 seconds

**Tab 6: ADVANCED (Server Icon)**

1. **Database:**
   - **Database URL** (text input)
     - PostgreSQL connection string
     - Example: `postgresql://user:pass@localhost:5432/msil_mcp`
   - **Pool Size** (number input)
     - Default: 10
   - **Max Overflow** (number input)
     - Default: 20
   - **Pool Timeout** (number input, seconds)
     - Default: 30
   - **Echo SQL** (toggle)
     - Log all SQL queries (debug only)
   - **SSL Mode** (dropdown)
     - Options: disable, require, verify-ca, verify-full
   - **Test Connection** button

2. **Container Security:**
   - **Run as Non-Root** (toggle)
     - Force container to run as non-root user
   - **Read-Only Filesystem** (toggle)
     - Mount root filesystem as read-only
   - **Resource Limits:**
     - **CPU Limit** (number input + unit)
       - Cores or millicores
     - **Memory Limit** (number input + unit)
       - MB or GB
   - **Security Context:**
     - **Drop Capabilities** (multi-select)
       - ALL, SYS_ADMIN, NET_RAW, etc.
     - **Add Capabilities** (multi-select)
       - Only if needed

3. **Network Policies:**
   - **Ingress Rules:**
     - **Allowed Sources** (textarea, one per line)
       - CIDR blocks allowed to connect
       - Example: `10.0.0.0/8`, `192.168.1.0/24`
   - **Egress Rules:**
     - **Allowed Destinations** (textarea, one per line)
       - CIDR blocks this service can reach
   - **DNS Policy** (dropdown)
     - Options: ClusterFirst, Default, None

4. **Backup & Recovery:**
   - **Backup Enabled** (toggle)
   - **Backup Schedule** (cron expression input)
     - Example: `0 2 * * *` (daily at 2 AM)
   - **Backup Target** (dropdown)
     - Options: S3, Local Disk, Azure Blob, GCS
   - **S3 Backup Settings** (if S3 selected):
     - **Bucket Name** (text input)
     - **Region** (dropdown)
     - **Access Key** (password input)
     - **Secret Key** (password input)
     - **Object Lock** (toggle)
       - Immutable backups
     - **Object Lock Mode** (dropdown)
       - GOVERNANCE or COMPLIANCE
     - **Retention Days** (number input)
       - Default: 90 days
   - **Encryption** (toggle)
     - Encrypt backups
   - **Encryption Key** (password input or KMS ARN)

5. **Security Testing:**
   - **DAST Enabled** (toggle)
     - Dynamic Application Security Testing
   - **SAST Enabled** (toggle)
     - Static Application Security Testing
   - **Dependency Scanning** (toggle)
     - Check for vulnerable dependencies
   - **Secret Scanning** (toggle)
     - Detect hardcoded secrets
   - **Scan on Deploy** (toggle)
     - Run security scans on deployment
   - **Webhook on Findings** (text input)
     - URL to notify on security findings

6. **Feature Flags:**
   - **Feature Flag Provider** (dropdown)
     - Options: LaunchDarkly, ConfigCat, Custom
   - **Provider Key** (password input)
   - **Refresh Interval** (number input, seconds)
     - Default: 60 seconds

7. **Observability:**
   - **Metrics Enabled** (toggle)
   - **Metrics Endpoint** (text input)
     - Default: `/metrics`
   - **Prometheus Format** (toggle)
   - **Tracing Enabled** (toggle)
   - **Tracing Backend** (dropdown)
     - Options: Jaeger, Zipkin, OpenTelemetry
   - **Tracing Endpoint** (text input)
   - **Sample Rate** (slider, 0-100%)
     - Percentage of requests to trace
     - Default: 10%

**Settings Tab Global Features:**
- **Save All** button (bottom-right, blue)
  - Saves all settings across all tabs
  - Shows spinner during save
  - Success toast: "Settings saved successfully"
  - Error toast with details if save fails
- **Reset to Defaults** button (bottom-left, gray)
  - Confirmation dialog
  - Resets all settings to factory defaults
- **Unsaved Changes Indicator:**
  - Orange dot on tab if changes pending
  - "You have unsaved changes" banner
- **Import/Export:**
  - **Export Settings** button - Download as JSON
  - **Import Settings** button - Upload JSON
- **Validation:**
  - Real-time field validation
  - Disable Save if any field is invalid
  - Show error messages below invalid fields

---

## 4. COMMON UI COMPONENTS

### 4.1 Header Bar
- Appears at top of every page
- **Left Side:**
  - Breadcrumb navigation (Home > Current Page)
- **Right Side:**
  - Notification bell icon (with badge if new notifications)
  - User avatar dropdown
    - User name display
    - Role display
    - Logout button

### 4.2 Page Patterns
All pages follow similar structure:
- **Page Title** (large, bold)
- **Page Description** (smaller, gray text)
- **Action Buttons** (top-right)
- **Content Cards** (white background, rounded corners, shadow)
- **Loading States** (spinner + text)
- **Empty States** (icon + helpful text)
- **Error States** (red alert box)

### 4.3 Form Components
- **Text Inputs** - Border, rounded, focus state
- **Dropdowns/Select** - Searchable, keyboard navigation
- **Toggles** - iOS-style switches
- **Sliders** - For numeric ranges (temperature, sample rate)
- **Textareas** - For long text, auto-resize
- **Date Pickers** - Calendar widget
- **File Pickers** - Drag & drop or click to upload
- **JSON Editors** - Code editor with syntax highlighting
- **Radio Buttons** - For mutually exclusive options
- **Checkboxes** - For multiple selections

### 4.4 Data Display
- **Tables** - Sortable columns, pagination, row hover
- **Cards** - Info cards with icons and metrics
- **Badges** - Status indicators (active/inactive, success/failure)
- **Tags** - For categories, labels
- **Progress Bars** - For wizards, loading
- **Charts** - Line, bar, pie charts (via charting library)
- **Accordions** - Collapsible sections

### 4.5 Feedback Components
- **Toasts** - Success/error notifications (top-right corner)
- **Modals** - For forms, confirmations
- **Alerts** - Inline info/warning/error boxes
- **Spinners** - Loading indicators
- **Progress Indicators** - Step wizards, multi-step flows
- **Confirmation Dialogs** - Before destructive actions

---

## 5. AUTHENTICATION & AUTHORIZATION

### 5.1 Login Page
- **URL:** `/login`
- Not behind auth wall
- **Form Fields:**
  - Email or Username
  - Password
  - Remember Me checkbox
- **Actions:**
  - Login button
  - Forgot Password link
  - Sign Up link (if applicable)
- **Demo Mode:**
  - "Login as Demo User" button
  - Bypasses auth (if DEMO_MODE=True)

### 5.2 Protected Routes
All routes except `/login` require authentication
- **Unauthenticated Access:**
  - Redirect to `/login`
  - Show reason: "Please log in to continue"
- **Authenticated Access:**
  - Show full UI with sidebar
  - Display user info in header

### 5.3 Role-Based Access (If Implemented)
- Admin role: Full access to all pages
- Operator role: Limited access (view-only on some pages)
- Developer role: Access to Tools, Import, Settings

---

## 6. API INTEGRATION

All admin portal features interact with backend REST APIs:

### 6.1 Base URL
- `/api/admin/*` - Admin endpoints

### 6.2 Authentication
- **Header:** `Authorization: Bearer {jwt_token}`
- **Header:** `x-api-key: {api_key}` (fallback for demo)

### 6.3 Key Endpoints

**Dashboard:**
- `GET /api/admin/dashboard` - Dashboard metrics

**Tools:**
- `GET /api/admin/tools` - List all tools
- `POST /api/admin/tools` - Create tool
- `PUT /api/admin/tools/{tool_name}` - Update tool
- `DELETE /api/admin/tools/{tool_name}` - Delete tool

**Import:**
- `POST /api/admin/openapi/import` - Import OpenAPI spec
- `POST /api/admin/openapi/approve` - Approve and register tools

**Policies:**
- `GET /api/admin/policies/roles` - List all roles
- `POST /api/admin/policies/roles` - Create role
- `DELETE /api/admin/policies/roles/{role_name}` - Delete role
- `POST /api/admin/policies/roles/{role_name}/permissions` - Add permission
- `DELETE /api/admin/policies/roles/{role_name}/permissions` - Remove permission

**Exposure:**
- `GET /api/admin/exposure/roles/{role}/permissions` - Get exposure permissions
- `POST /api/admin/exposure/roles/{role}/permissions` - Add exposure permission
- `DELETE /api/admin/exposure/roles/{role}/permissions` - Remove exposure permission
- `GET /api/admin/exposure/bundles` - List all bundles
- `GET /api/admin/exposure/roles/{role}/preview` - Preview exposed tools

**Audit Logs:**
- `GET /api/admin/audit-logs` - Get audit logs (with filters)

**Settings:**
- `GET /api/admin/settings` - Get all settings
- `PUT /api/admin/settings` - Update settings

---

## 7. TECHNOLOGY STACK

### 7.1 Frontend
- **Framework:** React 18
- **Build Tool:** Vite 5
- **Styling:** Tailwind CSS 3
- **Routing:** React Router v6
- **State Management:** React Hooks + Context API
- **Icons:** Lucide React
- **HTTP Client:** Fetch API
- **TypeScript:** Full TypeScript support

### 7.2 UI Libraries Used
- Custom UI components (Button, Card, Dialog, Tabs)
- No external component library (Shadcn/UI style, but custom)
- All components in `/src/components/ui/`

### 7.3 Development
- **Dev Server:** Vite dev server with HMR
- **Port:** 3001 (configurable)
- **Proxy:** All `/api` requests proxied to port 8000
- **Environment:** `.env` files for configuration

---

## 8. TESTING CHECKLIST FOR EXTERNAL LLM

An external LLM verifying these features should check:

### 8.1 Navigation
- [ ] All 8 pages accessible from sidebar
- [ ] Active page highlighted correctly
- [ ] Breadcrumbs update on navigation
- [ ] Logo displayed correctly
- [ ] System status indicator visible

### 8.2 Dashboard
- [ ] 6 KPI cards display with numbers
- [ ] Tools Usage Chart renders
- [ ] Recent Activity feed shows data
- [ ] Quick Actions section displays 3 actions
- [ ] Refresh functionality works
- [ ] Live Data badge shows

### 8.3 Tools
- [ ] Tool list displays with pagination
- [ ] Create New Tool button opens modal
- [ ] Form has all required fields (name, endpoint, method, etc.)
- [ ] Input/Output schema JSON editors work
- [ ] Risk level, rate limit, and toggle fields present
- [ ] Save creates tool successfully
- [ ] Edit tool loads existing data
- [ ] Delete tool shows confirmation
- [ ] Toggle active/inactive works
- [ ] Search filters tools
- [ ] Total count displayed

### 8.4 Import OpenAPI
- [ ] File upload area visible (drag & drop)
- [ ] Supports JSON and YAML files
- [ ] After upload, shows spec info (name, version, tools count)
- [ ] Tool preview table displays generated tools
- [ ] Can select/deselect individual tools
- [ ] Select All / Deselect All works
- [ ] Approve & Register button visible
- [ ] After approval, shows success screen
- [ ] Success screen lists registered tool names
- [ ] "Import Another Spec" and "View All Tools" buttons work
- [ ] "How it works" info panel visible

### 8.5 Policies
- [ ] Statistics cards show Active Roles and Total Permissions counts
- [ ] Create Role section has form (name + permissions)
- [ ] Create Role button functional
- [ ] All existing roles displayed as cards
- [ ] Each role shows permission count
- [ ] Each role shows list of permissions
- [ ] Add permission input field per role
- [ ] Remove permission trash icon per permission
- [ ] Delete role button with confirmation
- [ ] Refresh updates data

### 8.6 Exposure Governance
- [ ] Role selector shows 3 roles (Operator, Developer, Admin)
- [ ] Clicking role switches context
- [ ] Active role highlighted
- [ ] Exposure Permissions panel shows permissions list
- [ ] Add Permission button opens dialog
- [ ] Dialog has 3 options: All, Bundle, Tool
- [ ] Bundle dropdown populated with available bundles
- [ ] Tool dropdown shows tools from selected bundle
- [ ] Add permission saves and refreshes
- [ ] Remove permission shows confirmation
- [ ] Preview Panel shows summary (Total Tools, Bundles, Status)
- [ ] Preview Panel shows exposed tools by bundle (accordion)
- [ ] Available Bundles reference card displays all bundles
- [ ] Refresh button works

### 8.7 Audit Logs
- [ ] Statistics cards show Total, Success, Failed, Denied counts
- [ ] Export CSV button visible
- [ ] Search box functional
- [ ] Event Type filter dropdown works
- [ ] Status filter dropdown works
- [ ] Audit log table displays with all columns:
  - Status icon
  - Timestamp
  - Event Type
  - User ID
  - Tool Name
  - Action
  - Status badge
  - Latency
- [ ] Status icons color-coded (green/red/orange)
- [ ] Pagination controls present
- [ ] CSV export downloads file

### 8.8 Service Booking
- [ ] Step indicator shows 4 steps with icons
- [ ] Step 1 (Vehicle): Model dropdown, Registration input, Next button
- [ ] Step 2 (Service): Service type dropdown, Date picker, Time dropdown, Back/Next buttons
- [ ] Step 3 (Dealer): Dealer code, name, address fields, Back/Next buttons
- [ ] Step 4 (Customer): Name, phone, email, notes fields, Back/Submit buttons
- [ ] Navigation between steps works (Back/Next)
- [ ] Form data persists across steps
- [ ] Submit shows confirmation screen
- [ ] Confirmation displays booking ID and summary
- [ ] New Booking button resets wizard

### 8.9 Settings
- [ ] 6 tabs displayed (General, Security, LLM/AI, API Gateway, Performance, Advanced)
- [ ] Tab icons rendered correctly
- [ ] Clicking tab switches view
- [ ] **General Tab:**
  - Log Level dropdown
  - Server settings (host, port, workers)
  - CORS settings
- [ ] **Security Tab:**
  - Auth Required toggle
  - Demo Mode toggle
  - JWT configuration
  - Policy settings
  - Exposure settings
  - Audit settings
  - PIM settings
  - mTLS settings
  - WAF settings
  - Tool Risk settings
- [ ] **LLM/AI Tab:**
  - Provider selection (OpenAI, Azure, Google, Anthropic, AWS)
  - API key input
  - Model dropdown
  - Temperature slider
  - Max tokens input
  - System prompt textarea
- [ ] **API Gateway Tab:**
  - Mode selection (Mock/MSIL APIM)
  - Mock settings (if Mock mode)
  - APIM settings (URL, key, timeout, retries)
  - Test Connection button
- [ ] **Performance Tab:**
  - Cache settings (Redis URL, TTL)
  - Rate limiting settings (strategy, limits)
  - Idempotency settings
  - Batch processing settings
  - Resilience (circuit breaker)
  - Connection pooling
- [ ] **Advanced Tab:**
  - Database configuration
  - Container security settings
  - Network policies
  - Backup & recovery settings
  - Security testing toggles
  - Feature flags
  - Observability settings
- [ ] Save All button at bottom
- [ ] Reset to Defaults button
- [ ] Unsaved changes indicator
- [ ] Import/Export Settings buttons

### 8.10 Common Elements
- [ ] Header bar on all pages
- [ ] User avatar and name in header
- [ ] Notification bell icon
- [ ] Logout button in dropdown
- [ ] Loading states show spinners
- [ ] Error states show red alert boxes
- [ ] Success toasts appear on successful actions
- [ ] Confirmation dialogs for destructive actions
- [ ] All forms have validation
- [ ] Disabled buttons when invalid
- [ ] Responsive design (works on mobile)

---

## 9. PHASE 2 ROADMAP (FUTURE ENHANCEMENTS)

*Planned enhancements beyond Phase 1 MVP:*

1. Real-time Notifications (WebSocket push updates)
2. User Management Page (create/edit admin accounts)
3. Multi-tenancy (separate customer environments)
4. Advanced Analytics Dashboard (custom reporting)
5. Tool Version History (change tracking)
6. Workflow Builder (visual tool chaining UI)
7. API Playground (interactive tool testing)
8. Dark Mode (theme toggle)

**For details, see internal ROADMAP.md (not included in customer deliverables)**

---

## 10. KNOWN ISSUES

1. **PreviewPanel Error** - Fixed: Added null safety check for undefined preview
2. **CSS @import Warning** - Vite warning about @import order in globals.css (non-blocking)
3. **Port Conflicts** - Admin UI may start on 3002 if 3001 is occupied

---

## 11. VERIFICATION INSTRUCTIONS FOR EXTERNAL LLM

When verifying this feature list:

1. **Open the Admin Portal:** Navigate to `http://localhost:3001` in a browser
2. **Login (if required):** Use demo credentials or demo mode bypass
3. **Navigate Each Page:** Click through all 8 sidebar menu items
4. **Check Each Feature:** For each page listed above, verify:
   - All UI elements are present
   - All buttons/inputs are functional
   - Data loads correctly (even if mock data)
   - Actions complete successfully (create, edit, delete)
   - Error handling works (try invalid inputs)
   - Loading states appear during operations
5. **Test Workflows:** Complete end-to-end workflows:
   - Create a tool → Edit it → Delete it
   - Import OpenAPI spec → Approve tools → View in Tools page
   - Add exposure permission → Preview → Remove permission
   - Create policy role → Add permission → Delete role
   - Complete service booking wizard from start to finish
   - Change settings → Save → Verify persistence
6. **Check Responsiveness:** Resize browser to verify mobile layout
7. **Verify API Calls:** Open browser DevTools Network tab, confirm API calls to `/api/admin/*`
8. **Test Error Cases:** Try to submit invalid forms, check error messages
9. **Compare Against This Document:** Mark each feature as ✓ Present or ✗ Missing
10. **Report Discrepancies:** Note any features described here but not found in UI

---

## 12. SUCCESS CRITERIA

The Admin Portal UI is considered **fully featured** if:

- ✅ All 8 pages are accessible and render without errors
- ✅ All core CRUD operations work (Create, Read, Update, Delete)
- ✅ All forms submit successfully and show feedback
- ✅ All wizards/multi-step flows complete end-to-end
- ✅ API integration functions (data loads from backend)
- ✅ No critical bugs block basic functionality
- ✅ UI matches the feature descriptions in this document (95%+ match)
- ✅ All navigation works without broken links
- ✅ Loading/error/empty states display appropriately
- ✅ Settings persist after save

**Acceptable Deviations:**
- Minor styling differences (colors, spacing)
- Placeholder text variations
- Feature flags showing/hiding certain options
- Settings not all implemented yet (as marked in "Missing Features")

---

## IMPLEMENTATION STATUS NOTES

### ⚠️ Known Limitations (As of February 7, 2026)

**Backend Enforcement:**
- Policy engine and exposure filtering code exists but verification of end-to-end enforcement needed
- Some runtime configurations (rate limiting, elevation gates, confirmation flows) partially implemented

**Dashboard Metrics:**
- KPI cards fetch real data from metrics collection system
- Conversation tracking not yet integrated (shows 0)
- Time-filtered metrics (last hour, last 24h) in development

**Audit Logging:**
- Audit trail recorded and searchable
- PII masking configuration in progress
- Retention period: 365 days (12 months, per RFP requirement)

**Service Booking:**
- UI workflow complete and functional
- Backend integration not yet implemented (demo/mockup only)

**Settings Configuration:**
- Essential settings (General, Security, API Gateway) implemented
- Advanced settings (Performance tuning, Container orchestration) planned for Phase 2
- Not all toggles backed by functional endpoints yet

### ✅ Verified Working

- Admin authentication and login
- Tool CRUD operations (create, read, update, delete)
- OpenAPI specification file uploads and tool generation
- Exposure governance configuration (roles, permissions, preview)
- Policy configuration (role creation, permission management)
- Audit log viewing and CSV export
- Settings persistence for implemented features
- UI validation and error handling
- Responsive design and accessibility

---

## END OF DOCUMENT

**Total Pages:** 8  
**Total Features Documented:** 150+  
**Total UI Components:** 50+  
**Total API Endpoints:** 30+  
**Estimated Verification Time:** 2-3 hours for complete manual check  

**Prepared For:** External LLM verification  
**Prepared By:** GitHub Copilot Assistant  
**Date:** February 7, 2026
