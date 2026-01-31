"""
Server-Sent Events (SSE) Streaming Support
"""
import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
from fastapi import Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


class SSEMessage:
    """Server-Sent Event message"""
    
    def __init__(
        self,
        data: Any,
        event: Optional[str] = None,
        id: Optional[str] = None,
        retry: Optional[int] = None
    ):
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry
    
    def encode(self) -> str:
        """Encode message as SSE format"""
        message = []
        
        if self.event:
            message.append(f"event: {self.event}")
        
        if self.id:
            message.append(f"id: {self.id}")
        
        if self.retry:
            message.append(f"retry: {self.retry}")
        
        # Data can be multi-line
        data_str = json.dumps(self.data) if not isinstance(self.data, str) else self.data
        for line in data_str.split('\n'):
            message.append(f"data: {line}")
        
        # End with double newline
        return '\n'.join(message) + '\n\n'


class SSEStream:
    """SSE stream manager"""
    
    def __init__(self):
        self.active_streams: Dict[str, asyncio.Queue] = {}
    
    def create_stream(self, stream_id: str) -> asyncio.Queue:
        """Create a new SSE stream"""
        queue = asyncio.Queue(maxsize=100)
        self.active_streams[stream_id] = queue
        logger.info(f"Created SSE stream: {stream_id}")
        return queue
    
    async def send_message(self, stream_id: str, message: SSEMessage):
        """Send message to stream"""
        if stream_id in self.active_streams:
            try:
                await self.active_streams[stream_id].put(message)
            except asyncio.QueueFull:
                logger.warning(f"SSE stream {stream_id} queue full, dropping message")
    
    def close_stream(self, stream_id: str):
        """Close and remove stream"""
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
            logger.info(f"Closed SSE stream: {stream_id}")
    
    async def stream_generator(
        self,
        stream_id: str,
        request: Request
    ) -> AsyncGenerator[str, None]:
        """
        Generate SSE events from queue
        
        Args:
            stream_id: Stream identifier
            request: FastAPI request object (for disconnect detection)
            
        Yields:
            SSE formatted messages
        """
        queue = self.create_stream(stream_id)
        
        try:
            # Send initial connection message
            yield SSEMessage(
                data={"status": "connected", "stream_id": stream_id},
                event="connected",
                id="0"
            ).encode()
            
            # Keep-alive counter
            keep_alive_counter = 0
            
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from stream {stream_id}")
                    break
                
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield message.encode()
                    
                except asyncio.TimeoutError:
                    # Send keep-alive comment
                    keep_alive_counter += 1
                    yield f": keep-alive {keep_alive_counter}\n\n"
                
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield SSEMessage(
                data={"error": str(e)},
                event="error"
            ).encode()
        
        finally:
            self.close_stream(stream_id)


# Singleton instance
sse_stream = SSEStream()


async def create_sse_response(
    stream_id: str,
    request: Request
) -> StreamingResponse:
    """
    Create SSE streaming response
    
    Args:
        stream_id: Unique stream identifier
        request: FastAPI request object
        
    Returns:
        StreamingResponse with SSE headers
    """
    return StreamingResponse(
        sse_stream.stream_generator(stream_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


async def send_tool_progress(
    stream_id: str,
    tool_name: str,
    progress: float,
    message: str,
    **kwargs
):
    """
    Send tool execution progress update
    
    Args:
        stream_id: Stream ID
        tool_name: Tool name
        progress: Progress percentage (0-100)
        message: Progress message
        **kwargs: Additional data
    """
    await sse_stream.send_message(
        stream_id,
        SSEMessage(
            data={
                "tool_name": tool_name,
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            },
            event="tool_progress"
        )
    )


async def send_tool_result(
    stream_id: str,
    tool_name: str,
    result: Any,
    success: bool = True,
    error: Optional[str] = None
):
    """
    Send tool execution result
    
    Args:
        stream_id: Stream ID
        tool_name: Tool name
        result: Tool result data
        success: Whether execution succeeded
        error: Error message if failed
    """
    await sse_stream.send_message(
        stream_id,
        SSEMessage(
            data={
                "tool_name": tool_name,
                "result": result,
                "success": success,
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            },
            event="tool_result" if success else "tool_error"
        )
    )


async def send_batch_update(
    stream_id: str,
    completed: int,
    total: int,
    results: list
):
    """
    Send batch execution update
    
    Args:
        stream_id: Stream ID
        completed: Number of completed tools
        total: Total number of tools
        results: List of completed results
    """
    await sse_stream.send_message(
        stream_id,
        SSEMessage(
            data={
                "completed": completed,
                "total": total,
                "progress": round((completed / total) * 100, 1) if total > 0 else 0,
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            },
            event="batch_update"
        )
    )
