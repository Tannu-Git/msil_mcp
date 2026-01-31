"""
Session Management Service
Handles conversation history and session persistence
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatSession, ChatMessage, ToolExecution


class SessionService:
    """Service for managing chat sessions and conversation history"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get session by ID"""
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_or_create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> ChatSession:
        """Get existing session or create new one"""
        session = await self.get_session(session_id)
        if not session:
            session = await self.create_session(session_id, user_id)
        return session
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Add a message to session history"""
        # Ensure session exists
        session = await self.get_or_create_session(session_id)
        
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=tool_calls or [],
            metadata=metadata or {},
            timestamp=datetime.utcnow()
        )
        self.db.add(message)
        
        # Update session timestamp
        session.updated_at = datetime.utcnow()
        session.message_count = (session.message_count or 0) + 1
        
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[ChatMessage]:
        """Get conversation history for a session"""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_context_messages(
        self,
        session_id: str,
        max_messages: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent messages formatted for LLM context"""
        messages = await self.get_conversation_history(session_id, limit=max_messages)
        
        # Format for OpenAI API
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
            
            # Add tool call results if present
            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    formatted.append({
                        "role": "function",
                        "name": tool_call.get("name", "unknown"),
                        "content": str(tool_call.get("result", ""))
                    })
        
        return formatted
    
    async def record_tool_execution(
        self,
        session_id: str,
        message_id: int,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        execution_time_ms: int,
        success: bool = True,
        error: Optional[str] = None
    ) -> ToolExecution:
        """Record a tool execution"""
        execution = ToolExecution(
            session_id=session_id,
            message_id=message_id,
            tool_name=tool_name,
            arguments=arguments,
            result=result if success else None,
            error=error,
            execution_time_ms=execution_time_ms,
            success=success,
            timestamp=datetime.utcnow()
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        return execution
    
    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        session = await self.get_session(session_id)
        if not session:
            return {}
        
        messages = await self.get_conversation_history(session_id)
        
        # Count tool executions
        result = await self.db.execute(
            select(ToolExecution)
            .where(ToolExecution.session_id == session_id)
        )
        tool_executions = list(result.scalars().all())
        
        return {
            "session_id": session_id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "message_count": len(messages),
            "tool_execution_count": len(tool_executions),
            "successful_tools": sum(1 for t in tool_executions if t.success),
            "failed_tools": sum(1 for t in tool_executions if not t.success),
            "avg_tool_time_ms": (
                sum(t.execution_time_ms for t in tool_executions) / len(tool_executions)
                if tool_executions else 0
            )
        }
    
    async def clear_session(self, session_id: str) -> bool:
        """Clear all messages and tool executions for a session"""
        # Delete tool executions
        await self.db.execute(
            ToolExecution.__table__.delete().where(
                ToolExecution.session_id == session_id
            )
        )
        
        # Delete messages
        await self.db.execute(
            ChatMessage.__table__.delete().where(
                ChatMessage.session_id == session_id
            )
        )
        
        # Update session
        session = await self.get_session(session_id)
        if session:
            session.message_count = 0
            session.updated_at = datetime.utcnow()
        
        await self.db.commit()
        return True
