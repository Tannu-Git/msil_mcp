# MSIL MCP Server - Complete E2E Demo Ready 🚀

AI-powered service platform for Maruti Suzuki India Limited, implementing the Model Context Protocol (MCP) for intelligent tool discovery and execution.

## 🎯 What's New in Phase 6

✅ **Zero-Code Tool Generation** - Import OpenAPI specs → Instant MCP tools  
✅ **Real-Time Metrics** - Track every tool execution with detailed analytics  
✅ **OpenAPI Import UI** - Drag-drop upload, tool preview, selective registration  
✅ **Sample APIs Included** - Customer Service API with 11 endpoints ready to test  
✅ **Complete E2E Demo** - From API import to execution to monitoring  
✅ **Comprehensive Documentation** - Step-by-step demo guide and troubleshooting

**📋 For complete demo walkthrough, see: [E2E_DEMO_GUIDE.md](E2E_DEMO_GUIDE.md)**  
**📊 For implementation status, see: [PHASE6_STATUS.md](PHASE6_STATUS.md)**

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

- **Python 3.9+** (with pip)
- **Node.js 18+** (with npm)
- **Windows** (or adapt scripts for Linux/Mac)

### Option 1: Automated Startup (Recommended)

```powershell
# Run the startup script
.\start-demo.ps1
```

This will:
1. Check if ports are available
2. Start MCP Server (port 8000)
3. Start Admin UI (port 5174)
4. Start Chat UI (port 5173)
5. Wait for all services to be ready

### Option 2: Manual Startup

### Option 2: Manual Startup

**Terminal 1: MCP Server**
```powershell
cd mcp-server
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2: Admin UI**
```powershell
cd admin-ui
npm install
npm run dev
```

**Terminal 3: Chat UI**
```powershell
cd chat-ui
npm install
npm run dev
```

### Verify Installation

- **MCP Server**: http://localhost:8000/docs (Swagger UI)
- **Admin Portal**: http://localhost:5174
- **Chat Interface**: http://localhost:5173

---

## 📋 Quick Demo (25 Minutes)

**Follow the complete guide: [E2E_DEMO_GUIDE.md](E2E_DEMO_GUIDE.md)**

1. **Import OpenAPI Spec** (5 min)
   - Open Admin UI → Click "Import OpenAPI"
   - Upload `sample-apis/customer-service-api.yaml`
   - Review 11 generated tools → Click "Register Selected"

2. **View Registered Tools** (3 min)
   - Navigate to "Tools" page
   - See all tools with metadata

3. **Execute Tools via AI** (7 min)
   - Open Chat UI
   - Ask: "Create a customer named Rajesh Kumar"
   - AI calls tools automatically

4. **Monitor Metrics** (5 min)
   - Return to Admin UI Dashboard
   - See real-time metrics and usage stats

---

## 📚 Key Documentation

- **[E2E_DEMO_GUIDE.md](E2E_DEMO_GUIDE.md)** - Complete demo walkthrough
- **[PHASE6_STATUS.md](PHASE6_STATUS.md)** - Implementation status & features
- **[MCP_PROTOCOL_GUIDE.md](MCP_PROTOCOL_GUIDE.md)** - Protocol specification
- **[ADMIN_PORTAL_DEMO_READINESS.md](ADMIN_PORTAL_DEMO_READINESS.md)** - Gap analysis

---

## 🏗️ Project Structure

```
msil_mcp/
├── mcp-server/              # FastAPI backend
│   ├── app/
│   │   ├── api/            # REST endpoints
│   │   │   ├── mcp.py      # MCP protocol (JSON-RPC 2.0)
│   │   │   ├── openapi_import.py  # OpenAPI import API ✨ NEW
│   │   │   └── analytics.py       # Real metrics ✨ UPDATED
│   │   ├── core/
│   │   │   ├── openapi/    # OpenAPI parser ✨ NEW
│   │   │   ├── metrics/    # Metrics collector ✨ NEW
│   │   │   └── tools/      # Tool registry & executor
│   │   └── main.py
│   └── requirements.txt
│
├── admin-ui/                # React admin portal
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Import.tsx  # OpenAPI import workflow ✨ NEW
│   │   │   ├── Dashboard.tsx  # Real metrics dashboard ✨ UPDATED
│   │   │   └── Tools.tsx
│   │   └── components/
│   │       └── import/     # Upload & preview ✨ NEW
│   └── package.json
│
├── chat-ui/                 # React chat interface
│   └── src/
│
├── sample-apis/             # Sample OpenAPI specs ✨ NEW
│   └── customer-service-api.yaml
│
├── E2E_DEMO_GUIDE.md       # Step-by-step demo script ✨ NEW
├── PHASE6_STATUS.md        # Implementation status ✨ NEW
├── start-demo.ps1          # Automated startup script ✨ NEW
└── README.md               # This file
```

---

## ✨ Phase 6 Features

### 1. OpenAPI Import Pipeline
- **Parser**: Supports OpenAPI 3.x and Swagger 2.0 (YAML/JSON)
- **Generator**: Converts API operations → MCP tool definitions
- **Schema Builder**: Parameters + request body → JSON Schema
- **Import UI**: Drag-drop upload, URL import, tool preview

### 2. Real Metrics Tracking
- **Collector**: Async context manager tracks every execution
- **Aggregation**: Per-tool and global metrics
- **Dashboard**: Real-time visualization (not mock data)
- **Metrics**: Calls, success rate, avg duration, last used

### 3. Sample APIs
- **Customer Service API**: 11 endpoints across 3 domains
- **Ready to Use**: Upload and start testing immediately

---

## 🎯 Use Cases

1. **API Product Onboarding** - Upload OpenAPI spec → Tools ready in 30 seconds
2. **AI Agent Tool Library** - Automatic JSON Schema generation from OpenAPI
3. **API Usage Analytics** - Real-time metrics for every tool execution
4. **Multi-Domain API Management** - Category and bundle grouping
5. **Rapid Prototyping** - Import → Test via Chat UI instantly

---

## 🛠️ Technology Stack

**Backend**: FastAPI, Python 3.9+, httpx, PyYAML  
**Frontend**: React 18, TypeScript, Vite, Tailwind CSS  
**Protocol**: JSON-RPC 2.0 over HTTP, JSON Schema Draft 7  
**Database**: PostgreSQL (optional, in-memory for MVP)

---

## 🚧 Known Limitations

- **In-Memory Storage**: Tools and metrics lost on restart (PostgreSQL schema ready)
- **Basic Auth**: API key only (OAuth2 planned)
- **No Tool Versioning**: Use bundle names for versioning

---

## 🐛 Troubleshooting

**Import fails**: Validate spec at https://editor.swagger.io  
**Tools not in Chat**: Check Admin UI → Tools page, ensure "Active"  
**Metrics showing 0**: Ensure `metrics_collector` imported in `executor.py`  
**Port in use**: Change port or kill process

---

## 📞 Support & Next Steps

### Getting Started
1. Run `.\start-demo.ps1` or start services manually
2. Read [E2E_DEMO_GUIDE.md](E2E_DEMO_GUIDE.md)
3. Import `sample-apis/customer-service-api.yaml`
4. Practice demo flow 2-3 times

### For Developers
- **OpenAPI Parser**: `mcp-server/app/core/openapi/parser.py`
- **Metrics Collector**: `mcp-server/app/core/metrics/collector.py`
- **Import Workflow**: `admin-ui/src/pages/Import.tsx`

---

## 🎉 Status

**Phase 6**: ✅ COMPLETE - Ready for Client Demo  
**Code Added**: 5,700+ lines  
**Files Created**: 15 new files  
**Documentation**: 4 comprehensive guides  

**You're ready to demo! 🚀**

---

## 📄 Legacy Sections

<details>
<summary>Original Setup Instructions (Docker, PostgreSQL, Redis)</summary>

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8080
```

Mock API runs on: http://localhost:8080

### Step 4: Start Chat UI

```powershell
cd chat-ui
npm install
npm run dev
```

Chat UI runs on: http://localhost:3000

### Step 5: Start Admin UI

```powershell
cd admin-ui
npm install
npm run dev
```

Admin UI runs on: http://localhost:3001

## 📁 Project Structure

```
msil_mcp/
├── mcp-server/          # MCP Server (FastAPI)
├── mock-api/            # Mock API Server (FastAPI)
├── chat-ui/             # Chat Interface (React + Vite)
├── admin-ui/            # Admin Console (React + Vite)
├── infrastructure/      # Docker & Terraform configs
│   ├── local/           # Local development
│   └── terraform/       # AWS infrastructure
└── docs/                # Documentation
```

## 🔧 API Endpoints

### MCP Server (port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/mcp` | POST | MCP protocol handler |
| `/mcp/tools` | GET | List all tools (REST) |
| `/api/chat/send` | POST | Chat endpoint |
| `/api/admin/dashboard` | GET | Admin dashboard data |
| `/api/admin/tools` | GET | List tools for admin |

### Mock API (port 8080)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/customer/resolve` | POST | Resolve customer by mobile |
| `/api/vehicle/resolve` | POST | Get vehicle details |
| `/api/dealers/nearby` | POST | Find nearby dealers |
| `/api/slots/available` | POST | Get available slots |
| `/api/booking/create` | POST | Create service booking |
| `/api/booking/{id}` | GET | Get booking status |

## 🎯 Demo Flow

1. **Open Chat UI**: http://localhost:3000
2. **Send a message**: "I want to book a car service for my vehicle MH12AB1234 tomorrow at 10 AM near Hinjewadi Pune"
3. **Watch the magic**: The AI will:
   - Resolve vehicle details
   - Find nearby dealers
   - Check available slots
   - Create the booking
4. **Verify in Admin UI**: http://localhost:3001 - see the tools list and metrics

## 🔑 Configuration

### Environment Variables (mcp-server/.env)

```env
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional (defaults work for local dev)
API_GATEWAY_MODE=mock
DATABASE_URL=postgresql+asyncpg://msil_mcp:msil_mcp_dev_2026@localhost:5432/msil_mcp_db
REDIS_URL=redis://localhost:6379/0
```

## 📊 Architecture

```
┌─────────────┐     ┌─────────────┐
│  Chat UI    │     │  Admin UI   │
│  (React)    │     │  (React)    │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └─────────┬─────────┘
                 │
         ┌───────▼───────┐
         │  MCP Server   │
         │  (FastAPI)    │
         └───────┬───────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼───┐  ┌─────▼─────┐  ┌───▼───┐
│OpenAI │  │  Mock API │  │  DB   │
│ (LLM) │  │ or MSIL   │  │ Redis │
└───────┘  │   APIM    │  └───────┘
           └───────────┘
```

## 🛠 Troubleshooting

### Database connection issues
```powershell
# Check if PostgreSQL is running
docker ps | Select-String postgres

# View logs
docker logs msil-mcp-postgres
```

### Redis connection issues
```powershell
# Check if Redis is running
docker ps | Select-String redis

# Test connection
docker exec msil-mcp-redis redis-cli ping
```

### OpenAI API issues
- Ensure `OPENAI_API_KEY` is set in `.env`
- Check API key validity at https://platform.openai.com

## 📄 License

Proprietary - Maruti Suzuki India Limited / Nagarro
