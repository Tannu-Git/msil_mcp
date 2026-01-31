"""HTTP client with mTLS support."""
import httpx
from typing import Optional, Dict, Any
import logging
from .certificate_manager import CertificateManager

logger = logging.getLogger(__name__)


class MTLSClient:
    """HTTP client with Mutual TLS authentication."""
    
    def __init__(
        self,
        cert_manager: CertificateManager,
        timeout: float = 30.0,
        verify: bool = True
    ):
        """
        Initialize mTLS client.
        
        Args:
            cert_manager: Certificate manager with SSL contexts
            timeout: Request timeout in seconds
            verify: Whether to verify server certificates
        """
        self.cert_manager = cert_manager
        self.timeout = timeout
        self.verify = verify
        self._client: Optional[httpx.AsyncClient] = None
    
    async def get_client(self) -> httpx.AsyncClient:
        """
        Get or create HTTP client with mTLS.
        
        Returns:
            Configured httpx.AsyncClient
        """
        if self._client is None:
            # Create SSL context
            ssl_context = self.cert_manager.create_client_ssl_context()
            
            # Create httpx client with mTLS
            self._client = httpx.AsyncClient(
                verify=ssl_context,
                timeout=self.timeout,
                http2=True  # Enable HTTP/2 for better performance
            )
            
            logger.info("Created mTLS HTTP client")
        
        return self._client
    
    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Make GET request with mTLS.
        
        Args:
            url: Request URL
            headers: Optional headers
            params: Optional query parameters
            
        Returns:
            HTTP response
        """
        client = await self.get_client()
        logger.debug(f"mTLS GET request to {url}")
        
        try:
            response = await client.get(url, headers=headers, params=params)
            logger.debug(f"mTLS GET response: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"mTLS GET request failed: {e}")
            raise
    
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """
        Make POST request with mTLS.
        
        Args:
            url: Request URL
            data: Form data
            json: JSON data
            headers: Optional headers
            
        Returns:
            HTTP response
        """
        client = await self.get_client()
        logger.debug(f"mTLS POST request to {url}")
        
        try:
            response = await client.post(url, data=data, json=json, headers=headers)
            logger.debug(f"mTLS POST response: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"mTLS POST request failed: {e}")
            raise
    
    async def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """
        Make PUT request with mTLS.
        
        Args:
            url: Request URL
            data: Form data
            json: JSON data
            headers: Optional headers
            
        Returns:
            HTTP response
        """
        client = await self.get_client()
        logger.debug(f"mTLS PUT request to {url}")
        
        try:
            response = await client.put(url, data=data, json=json, headers=headers)
            logger.debug(f"mTLS PUT response: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"mTLS PUT request failed: {e}")
            raise
    
    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """
        Make DELETE request with mTLS.
        
        Args:
            url: Request URL
            headers: Optional headers
            
        Returns:
            HTTP response
        """
        client = await self.get_client()
        logger.debug(f"mTLS DELETE request to {url}")
        
        try:
            response = await client.delete(url, headers=headers)
            logger.debug(f"mTLS DELETE response: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"mTLS DELETE request failed: {e}")
            raise
    
    async def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make generic HTTP request with mTLS.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
        """
        client = await self.get_client()
        logger.debug(f"mTLS {method} request to {url}")
        
        try:
            response = await client.request(method, url, **kwargs)
            logger.debug(f"mTLS {method} response: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"mTLS {method} request failed: {e}")
            raise
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("mTLS HTTP client closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
