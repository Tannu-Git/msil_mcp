"""
Batch Tool Executor - Execute multiple tools in parallel
"""
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from uuid import uuid4

from app.core.tools.executor import ToolExecutor

logger = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    """Single tool execution request in a batch"""
    tool_name: str
    arguments: Dict[str, Any]
    request_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class BatchResult:
    """Result of a single tool execution in batch"""
    request_id: str
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: int = 0


class BatchExecutor:
    """
    Execute multiple tools in parallel with concurrency control
    
    Features:
    - Parallel execution with asyncio.gather
    - Configurable max concurrency
    - Individual error handling (failures don't block batch)
    - Execution time tracking per tool
    """
    
    def __init__(self, tool_executor: Optional[ToolExecutor] = None, max_concurrency: int = 10):
        self.tool_executor = tool_executor or ToolExecutor()
        self.max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)
    
    async def execute_batch(
        self,
        requests: List[BatchRequest],
        correlation_id: str
    ) -> List[BatchResult]:
        """
        Execute batch of tool requests in parallel
        
        Args:
            requests: List of tool execution requests
            correlation_id: Batch correlation ID
            
        Returns:
            List of results (same order as requests)
        """
        if not requests:
            return []
        
        logger.info(f"[{correlation_id}] Executing batch of {len(requests)} tools")
        start_time = time.time()
        
        # Execute all requests in parallel with concurrency limit
        tasks = [
            self._execute_single(request, correlation_id)
            for request in requests
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(BatchResult(
                    request_id=requests[i].request_id,
                    tool_name=requests[i].tool_name,
                    success=False,
                    error=str(result)
                ))
            else:
                final_results.append(result)
        
        total_time = int((time.time() - start_time) * 1000)
        success_count = sum(1 for r in final_results if r.success)
        
        logger.info(
            f"[{correlation_id}] Batch completed in {total_time}ms: "
            f"{success_count}/{len(requests)} successful"
        )
        
        return final_results
    
    async def _execute_single(
        self,
        request: BatchRequest,
        correlation_id: str
    ) -> BatchResult:
        """Execute single tool request with semaphore"""
        async with self._semaphore:
            start_time = time.time()
            
            try:
                logger.debug(
                    f"[{correlation_id}] Batch executing {request.tool_name} "
                    f"(id: {request.request_id})"
                )
                
                result = await self.tool_executor.execute(
                    tool_name=request.tool_name,
                    arguments=request.arguments,
                    correlation_id=f"{correlation_id}:batch:{request.request_id}"
                )
                
                execution_time = int((time.time() - start_time) * 1000)
                
                return BatchResult(
                    request_id=request.request_id,
                    tool_name=request.tool_name,
                    success=True,
                    data=result.get("data"),
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                execution_time = int((time.time() - start_time) * 1000)
                
                logger.error(
                    f"[{correlation_id}] Batch tool {request.tool_name} failed: {e}"
                )
                
                return BatchResult(
                    request_id=request.request_id,
                    tool_name=request.tool_name,
                    success=False,
                    error=str(e),
                    execution_time_ms=execution_time
                )
    
    async def execute_batch_sequential(
        self,
        requests: List[BatchRequest],
        correlation_id: str,
        stop_on_error: bool = False
    ) -> List[BatchResult]:
        """
        Execute batch sequentially (useful when order matters)
        
        Args:
            requests: List of tool execution requests
            correlation_id: Batch correlation ID
            stop_on_error: Stop execution if any tool fails
            
        Returns:
            List of results
        """
        results = []
        
        for request in requests:
            result = await self._execute_single(request, correlation_id)
            results.append(result)
            
            # Stop if error and stop_on_error is True
            if not result.success and stop_on_error:
                logger.warning(
                    f"[{correlation_id}] Stopping sequential batch due to error "
                    f"in {request.tool_name}"
                )
                break
        
        return results
    
    def get_statistics(self, results: List[BatchResult]) -> Dict[str, Any]:
        """Get batch execution statistics"""
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        
        execution_times = [r.execution_time_ms for r in results]
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
        max_time = max(execution_times) if execution_times else 0
        min_time = min(execution_times) if execution_times else 0
        
        return {
            "total_requests": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "avg_execution_time_ms": int(avg_time),
            "max_execution_time_ms": max_time,
            "min_execution_time_ms": min_time
        }


# Singleton instance
batch_executor = BatchExecutor()
