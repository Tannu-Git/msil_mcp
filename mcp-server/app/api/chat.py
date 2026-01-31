"""
Chat API Endpoints
Handles chat sessions and LLM integration
"""
import logging
import uuid
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.llm.openai_client import openai_client
from app.core.tools.registry import tool_registry
from app.core.tools.executor import tool_executor
from app.db.database import get_db
# from app.services.session_service import SessionService  # TODO: Implement DB models first

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# Request/Response Models
# ============================================

class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # user, assistant, system, tool
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    session_id: Optional[str] = None
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    """Chat response model"""
    message: str
    session_id: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None


# ============================================
# Chat Endpoints
# ============================================

@router.post("/send")
async def send_message(
    request: ChatRequest,
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
) -> ChatResponse:
    """
    Send a chat message and get AI response
    Handles tool discovery and execution automatically
    """
    correlation_id = x_correlation_id or str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())
    
    logger.info(f"[{correlation_id}] Chat request: {request.message[:100]}...")
    
    try:
        # Get available tools for the LLM
        tools = await tool_registry.list_tools()
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            }
            for tool in tools
        ]
        
        # Build conversation history
        messages = [
            {
                "role": "system",
                "content": get_system_prompt()
            }
        ]
        
        # Add history
        for msg in request.history or []:
            messages.append({
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
                "tool_call_id": msg.tool_call_id
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Get LLM response
        response = await openai_client.chat_completion(
            messages=messages,
            tools=openai_tools,
            correlation_id=correlation_id
        )
        
        tool_results = []
        final_response = response.get("content", "")
        tool_calls_made = response.get("tool_calls", [])
        
        # If LLM wants to call tools, execute them
        if tool_calls_made:
            logger.info(f"[{correlation_id}] LLM requested {len(tool_calls_made)} tool calls")
            
            for tool_call in tool_calls_made:
                tool_name = tool_call.get("function", {}).get("name")
                arguments_str = tool_call.get("function", {}).get("arguments", "{}")
                
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError:
                    arguments = {}
                
                logger.info(f"[{correlation_id}] Executing tool: {tool_name}")
                
                # Execute the tool
                result = await tool_executor.execute(
                    tool_name=tool_name,
                    arguments=arguments,
                    correlation_id=correlation_id
                )
                
                tool_results.append({
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "result": result
                })
            
            # Add tool results to conversation and get final response
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls_made
            })
            
            for i, (tool_call, result) in enumerate(zip(tool_calls_made, tool_results)):
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id"),
                    "content": json.dumps(result["result"])
                })
            
            # Get final response after tool execution
            final_response_data = await openai_client.chat_completion(
                messages=messages,
                tools=openai_tools,
                correlation_id=correlation_id
            )
            final_response = final_response_data.get("content", "")
        
        return ChatResponse(
            message=final_response,
            session_id=session_id,
            tool_calls=[
                {
                    "name": tc["tool_name"],
                    "arguments": tc["arguments"]
                }
                for tc in tool_results
            ] if tool_results else None,
            tool_results=tool_results if tool_results else None
        )
        
    except Exception as e:
        logger.error(f"[{correlation_id}] Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get chat session details"""
    # For MVP, return basic session info
    return {
        "session_id": session_id,
        "started_at": "2026-01-30T10:00:00Z",
        "message_count": 5,
        "tools_used": ["resolve_vehicle", "get_nearby_dealers", "create_service_booking"]
    }


def get_system_prompt() -> str:
    """Get the system prompt for the AI assistant"""
    return """You are MSIL Service Assistant, an AI-powered assistant for Maruti Suzuki India Limited.
Your role is to help customers with:
1. Booking car service appointments
2. Finding nearby dealers
3. Checking booking status
4. Answering questions about vehicle service

You have access to various tools to help customers. When a customer wants to book a service:
1. First resolve their vehicle details using the registration number
2. Find nearby dealers based on their location
3. Check available slots at the selected dealer
4. Create the booking with their preferences

Always be helpful, professional, and courteous. Confirm important details before making bookings.
Format your responses clearly and provide booking confirmation details when a booking is made.

Important guidelines:
- Always verify vehicle registration format (e.g., MH12AB1234)
- Confirm appointment date and time before booking
- Provide booking ID in the confirmation
- If any step fails, explain the issue and suggest alternatives"""
