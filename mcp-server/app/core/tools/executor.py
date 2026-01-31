"""
Tool Executor - Executes tools against Mock API or MSIL APIM
"""
import logging
import time
import json
from typing import Any, Dict, Optional
import httpx
from circuitbreaker import circuit
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.core.tools.registry import tool_registry
from app.core.metrics.collector import metrics_collector

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Tool Executor - Executes tools against configured API gateway
    Supports: Mock API (local) and MSIL APIM (production)
    """
    
    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    def _get_base_url(self) -> str:
        """Get base URL based on API gateway mode"""
        if settings.API_GATEWAY_MODE == "msil_apim":
            return settings.MSIL_APIM_BASE_URL
        return settings.MOCK_API_BASE_URL
    
    def _get_headers(self, tool_auth_type: str) -> Dict[str, str]:
        """Get headers based on auth type and API gateway mode"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if settings.API_GATEWAY_MODE == "msil_apim":
            if settings.MSIL_APIM_SUBSCRIPTION_KEY:
                headers["Ocp-Apim-Subscription-Key"] = settings.MSIL_APIM_SUBSCRIPTION_KEY
            # Add OAuth token if available (future enhancement)
        else:
            # Mock API - simple API key
            headers["X-API-Key"] = settings.API_KEY
        
        return headers
    
    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        correlation_id: str
    ) -> Dict[str, Any]:
        """
        Execute a tool with given arguments
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            correlation_id: Request correlation ID
            
        Returns:
            Tool execution result
        """
        # Track execution with metrics collector
        async with metrics_collector.track_execution(tool_name, arguments) as execution_id:
            start_time = time.time()
            
            try:
                # Get tool definition
                tool = await tool_registry.get_tool(tool_name)
                if not tool:
                    raise ValueError(f"Tool not found: {tool_name}")
                
                # Build URL
                base_url = self._get_base_url()
                endpoint = tool.api_endpoint
                
                # Handle path parameters
                for key, value in arguments.items():
                    placeholder = f"{{{key}}}"
                    if placeholder in endpoint:
                        endpoint = endpoint.replace(placeholder, str(value))
                
                url = f"{base_url}{endpoint}"
                
                # Get headers
                headers = self._get_headers(tool.auth_type)
                headers["X-Correlation-ID"] = correlation_id
                headers["X-Execution-ID"] = execution_id
                
                # Get HTTP client
                client = await self._get_client()
                
                logger.info(f"[{correlation_id}] Executing {tool_name}: {tool.http_method} {url}")
                
                # Execute request with retry and circuit breaker
                response = await self._execute_with_retry(
                    client=client,
                    method=tool.http_method.upper(),
                    url=url,
                    headers=headers,
                    json_data=arguments,
                    correlation_id=correlation_id
                )
                
                execution_time = int((time.time() - start_time) * 1000)
                
                # Process response
                if response.status_code >= 400:
                    logger.error(f"[{correlation_id}] Tool execution failed: {response.status_code}")
                    raise Exception(f"API returned {response.status_code}: {response.text}")
                
                try:
                    result = response.json()
                except json.JSONDecodeError:
                    result = {"raw_response": response.text}
                
                logger.info(f"[{correlation_id}] Tool {tool_name} executed successfully in {execution_time}ms")
                
                return {
                    "success": True,
                    "data": result,
                    "execution_time_ms": execution_time
                }
                
            except httpx.TimeoutException as e:
                logger.error(f"[{correlation_id}] Tool execution timeout: {tool_name}")
                raise Exception("Request timeout")
                
            except Exception as e:
                logger.error(f"[{correlation_id}] Tool execution error: {str(e)}")
                raise
    
    @circuit(failure_threshold=5, recovery_timeout=60, expected_exception=httpx.HTTPError)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, httpx.ReadTimeout)),
        reraise=True
    )
    async def _execute_with_retry(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        headers: Dict,
        json_data: Dict,
        correlation_id: str
    ) -> httpx.Response:
        """
        Execute HTTP request with retry and circuit breaker
        
        Retry: 3 attempts with exponential backoff (2s, 4s, 8s)
        Circuit Breaker: Opens after 5 failures, recovers after 60 seconds
        """
        logger.debug(f"[{correlation_id}] Executing {method} {url} with retry")
        
        if method == "GET":
            response = await client.get(url, headers=headers, params=json_data)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=json_data)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=json_data)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response
    
    async def close(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


# Singleton instance
tool_executor = ToolExecutor()
