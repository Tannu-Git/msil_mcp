"""
Tool Registry - Manages tool definitions and discovery
"""
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """Tool definition"""
    id: uuid.UUID
    name: str
    display_name: str
    description: str
    category: str
    api_endpoint: str
    http_method: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    headers: Dict[str, str] = field(default_factory=dict)
    auth_type: str = "none"
    is_active: bool = True
    version: str = "1.0.0"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Risk & Privilege Management (P0-3)
    risk_level: str = "read"  # read, write, privileged
    requires_elevation: bool = False
    requires_approval: bool = False
    max_concurrent_executions: int = 10
    rate_limit_tier: str = "standard"  # permissive, standard, strict


class ToolRegistry:
    """
    Tool Registry - Manages tool definitions
    For MVP: Uses in-memory storage with DB loading
    """
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._loaded = False
    
    async def _ensure_loaded(self):
        """Ensure tools are loaded from database"""
        if not self._loaded:
            await self._load_from_db()
            self._loaded = True
    
    async def _load_from_db(self):
        """Load tools from database"""
        try:
            from app.db.database import get_db_session
            from sqlalchemy import text
            
            async with get_db_session() as session:
                result = await session.execute(
                    text("SELECT * FROM tools WHERE is_active = true")
                )
                rows = result.fetchall()
                
                for row in rows:
                    tool = Tool(
                        id=row.id,
                        name=row.name,
                        display_name=row.display_name,
                        description=row.description,
                        category=row.category,
                        api_endpoint=row.api_endpoint,
                        http_method=row.http_method,
                        input_schema=row.input_schema,
                        output_schema=row.output_schema,
                        headers=row.headers or {},
                        auth_type=row.auth_type,
                        is_active=row.is_active,
                        version=row.version,
                        created_at=row.created_at,
                        updated_at=row.updated_at
                    )
                    self._tools[tool.name] = tool
                
                logger.info(f"Loaded {len(self._tools)} tools from database")
                
        except Exception as e:
            logger.warning(f"Could not load tools from DB: {e}. Using default tools.")
            self._load_default_tools()
    
    def _load_default_tools(self):
        """Load default tools (fallback if DB not available)"""
        default_tools = [
            Tool(
                id=uuid.uuid4(),
                name="resolve_customer",
                display_name="Resolve Customer",
                description="Resolve customer details from mobile number",
                category="service_booking",
                api_endpoint="/api/customer/resolve",
                http_method="POST",
                input_schema={
                    "type": "object",
                    "properties": {
                        "mobile": {
                            "type": "string",
                            "description": "Customer mobile number (10 digits)"
                        }
                    },
                    "required": ["mobile"]
                }
            ),
            Tool(
                id=uuid.uuid4(),
                name="resolve_vehicle",
                display_name="Resolve Vehicle",
                description="Get vehicle details from registration number",
                category="service_booking",
                api_endpoint="/api/vehicle/resolve",
                http_method="POST",
                input_schema={
                    "type": "object",
                    "properties": {
                        "registration_number": {
                            "type": "string",
                            "description": "Vehicle registration number (e.g., MH12AB1234)"
                        }
                    },
                    "required": ["registration_number"]
                }
            ),
            Tool(
                id=uuid.uuid4(),
                name="get_nearby_dealers",
                display_name="Get Nearby Dealers",
                description="Find dealers near a location",
                category="service_booking",
                api_endpoint="/api/dealers/nearby",
                http_method="POST",
                input_schema={
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"},
                        "area": {"type": "string", "description": "Area or locality"},
                        "service_type": {
                            "type": "string",
                            "enum": ["regular", "express", "body_repair"],
                            "description": "Type of service required"
                        }
                    },
                    "required": ["city"]
                }
            ),
            Tool(
                id=uuid.uuid4(),
                name="get_available_slots",
                display_name="Get Available Slots",
                description="Get available appointment slots for a dealer",
                category="service_booking",
                api_endpoint="/api/slots/available",
                http_method="POST",
                input_schema={
                    "type": "object",
                    "properties": {
                        "dealer_code": {"type": "string", "description": "Dealer code"},
                        "date": {"type": "string", "format": "date", "description": "Date (YYYY-MM-DD)"},
                        "service_type": {"type": "string", "enum": ["regular", "express", "body_repair"]}
                    },
                    "required": ["dealer_code", "date"]
                }
            ),
            Tool(
                id=uuid.uuid4(),
                name="create_service_booking",
                display_name="Create Service Booking",
                description="Create a new service booking appointment",
                category="service_booking",
                api_endpoint="/api/booking/create",
                http_method="POST",
                input_schema={
                    "type": "object",
                    "properties": {
                        "customer_mobile": {"type": "string"},
                        "vehicle_registration": {"type": "string"},
                        "dealer_code": {"type": "string"},
                        "appointment_date": {"type": "string", "format": "date"},
                        "appointment_time": {"type": "string"},
                        "service_type": {"type": "string", "enum": ["regular", "express", "body_repair"]},
                        "notes": {"type": "string"}
                    },
                    "required": ["customer_mobile", "vehicle_registration", "dealer_code", "appointment_date", "appointment_time", "service_type"]
                }
            ),
            Tool(
                id=uuid.uuid4(),
                name="get_booking_status",
                display_name="Get Booking Status",
                description="Get status of an existing booking",
                category="service_booking",
                api_endpoint="/api/booking/{booking_id}",
                http_method="GET",
                input_schema={
                    "type": "object",
                    "properties": {
                        "booking_id": {"type": "string", "description": "Booking ID"}
                    },
                    "required": ["booking_id"]
                }
            )
        ]
        
        for tool in default_tools:
            self._tools[tool.name] = tool
        
        logger.info(f"Loaded {len(default_tools)} default tools")
    
    async def list_tools(
        self,
        category: Optional[str] = None,
        active_only: bool = True
    ) -> List[Tool]:
        """List all tools with optional filtering"""
        await self._ensure_loaded()
        
        tools = list(self._tools.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        if active_only:
            tools = [t for t in tools if t.is_active]
        
        return tools
    
    async def get_tool(self, name: str) -> Optional[Tool]:
        """Get a specific tool by name"""
        await self._ensure_loaded()
        return self._tools.get(name)
    
    async def count_tools(self, active_only: bool = False) -> int:
        """Count total tools"""
        await self._ensure_loaded()
        
        if active_only:
            return len([t for t in self._tools.values() if t.is_active])
        return len(self._tools)
    
    async def register_tool(self, tool: Tool) -> None:
        """Register a new tool"""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    async def reload(self) -> None:
        """Force reload tools from database"""
        self._loaded = False
        self._tools.clear()
        await self._ensure_loaded()


# Singleton instance
tool_registry = ToolRegistry()
