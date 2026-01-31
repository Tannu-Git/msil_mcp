"""
OpenAI Client - Handles LLM integration
"""
import logging
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    OpenAI Client for chat completions with tool support
    """
    
    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None
    
    def _get_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client"""
        if self._client is None:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        correlation_id: str = ""
    ) -> Dict[str, Any]:
        """
        Get chat completion from OpenAI
        
        Args:
            messages: Conversation messages
            tools: Available tools in OpenAI format
            correlation_id: Request correlation ID
            
        Returns:
            Response with content and/or tool_calls
        """
        try:
            client = self._get_client()
            
            # Clean messages for OpenAI format
            clean_messages = []
            for msg in messages:
                clean_msg = {"role": msg["role"]}
                
                if msg.get("content"):
                    clean_msg["content"] = msg["content"]
                elif msg["role"] != "assistant":
                    clean_msg["content"] = ""
                
                if msg.get("tool_calls"):
                    clean_msg["tool_calls"] = msg["tool_calls"]
                
                if msg.get("tool_call_id"):
                    clean_msg["tool_call_id"] = msg["tool_call_id"]
                
                clean_messages.append(clean_msg)
            
            logger.info(f"[{correlation_id}] Calling OpenAI with {len(clean_messages)} messages")
            
            # Make API call
            kwargs = {
                "model": settings.OPENAI_MODEL,
                "messages": clean_messages,
                "max_tokens": settings.OPENAI_MAX_TOKENS,
                "temperature": 0.7
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = await client.chat.completions.create(**kwargs)
            
            # Extract response
            choice = response.choices[0]
            message = choice.message
            
            result = {
                "content": message.content,
                "tool_calls": None
            }
            
            if message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            
            logger.info(f"[{correlation_id}] OpenAI response received. Tool calls: {len(result['tool_calls'] or [])}")
            
            return result
            
        except Exception as e:
            logger.error(f"[{correlation_id}] OpenAI error: {str(e)}")
            raise


# Singleton instance
openai_client = OpenAIClient()
