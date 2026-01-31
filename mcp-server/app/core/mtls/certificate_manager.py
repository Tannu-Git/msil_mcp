"""Certificate management for mTLS."""
import ssl
from pathlib import Path
from typing import Optional
import logging
from dataclasses import dataclass
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


@dataclass
class MTLSConfig:
    """Configuration for Mutual TLS."""
    
    ca_cert_path: str
    client_cert_path: str
    client_key_path: str
    server_cert_path: Optional[str] = None
    server_key_path: Optional[str] = None
    verify_mode: int = ssl.CERT_REQUIRED
    check_hostname: bool = True
    min_tls_version: int = ssl.TLSVersion.TLSv1_2
    ciphers: Optional[str] = None
    
    def __post_init__(self):
        """Validate certificate paths."""
        self._validate_path(self.ca_cert_path, "CA certificate")
        self._validate_path(self.client_cert_path, "Client certificate")
        self._validate_path(self.client_key_path, "Client private key")
        
        if self.server_cert_path:
            self._validate_path(self.server_cert_path, "Server certificate")
        if self.server_key_path:
            self._validate_path(self.server_key_path, "Server private key")
    
    def _validate_path(self, path: str, description: str):
        """Validate that certificate file exists."""
        if not Path(path).exists():
            raise FileNotFoundError(f"{description} not found at: {path}")


class CertificateManager:
    """Manager for TLS certificates and SSL contexts."""
    
    def __init__(self, config: MTLSConfig):
        """
        Initialize certificate manager.
        
        Args:
            config: mTLS configuration
        """
        self.config = config
        self._client_context: Optional[ssl.SSLContext] = None
        self._server_context: Optional[ssl.SSLContext] = None
    
    def create_client_ssl_context(self) -> ssl.SSLContext:
        """
        Create SSL context for client connections (outbound).
        
        Returns:
            Configured SSL context for client
        """
        if self._client_context:
            return self._client_context
        
        logger.info("Creating client SSL context for mTLS")
        
        # Create SSL context for client authentication
        context = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=self.config.ca_cert_path
        )
        
        # Load client certificate and private key
        context.load_cert_chain(
            certfile=self.config.client_cert_path,
            keyfile=self.config.client_key_path
        )
        
        # Configure TLS version and verification
        context.minimum_version = self.config.min_tls_version
        context.verify_mode = self.config.verify_mode
        context.check_hostname = self.config.check_hostname
        
        # Configure cipher suites (if specified)
        if self.config.ciphers:
            context.set_ciphers(self.config.ciphers)
        else:
            # Use secure default ciphers
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        # Disable weak protocols
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        
        self._client_context = context
        logger.info("Client SSL context created successfully")
        
        return context
    
    def create_server_ssl_context(self) -> ssl.SSLContext:
        """
        Create SSL context for server connections (inbound).
        
        Returns:
            Configured SSL context for server
            
        Raises:
            ValueError: If server certificate paths not configured
        """
        if self._server_context:
            return self._server_context
        
        if not self.config.server_cert_path or not self.config.server_key_path:
            raise ValueError("Server certificate and key paths required for server context")
        
        logger.info("Creating server SSL context for mTLS")
        
        # Create SSL context for server
        context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        
        # Load server certificate and private key
        context.load_cert_chain(
            certfile=self.config.server_cert_path,
            keyfile=self.config.server_key_path
        )
        
        # Load CA certificate for client verification
        context.load_verify_locations(cafile=self.config.ca_cert_path)
        
        # Require client certificates
        context.verify_mode = ssl.CERT_REQUIRED
        
        # Configure TLS version
        context.minimum_version = self.config.min_tls_version
        
        # Configure cipher suites
        if self.config.ciphers:
            context.set_ciphers(self.config.ciphers)
        else:
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        # Disable weak protocols
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        
        self._server_context = context
        logger.info("Server SSL context created successfully")
        
        return context
    
    def verify_certificate(self, cert_path: str) -> dict:
        """
        Verify and extract information from a certificate.
        
        Args:
            cert_path: Path to certificate file
            
        Returns:
            Dictionary with certificate information
        """
        try:
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            
            return {
                "subject": cert.subject.rfc4514_string(),
                "issuer": cert.issuer.rfc4514_string(),
                "serial_number": cert.serial_number,
                "not_valid_before": cert.not_valid_before_utc,
                "not_valid_after": cert.not_valid_after_utc,
                "is_expired": cert.not_valid_after_utc < datetime.now(cert.not_valid_after_utc.tzinfo),
                "version": cert.version.name,
                "signature_algorithm": cert.signature_algorithm_oid._name
            }
        except Exception as e:
            logger.error(f"Failed to verify certificate {cert_path}: {e}")
            raise
    
    def check_certificate_expiry(self, cert_path: str) -> int:
        """
        Check days until certificate expires.
        
        Args:
            cert_path: Path to certificate file
            
        Returns:
            Number of days until expiration (negative if expired)
        """
        cert_info = self.verify_certificate(cert_path)
        expiry_date = cert_info["not_valid_after"]
        now = datetime.now(expiry_date.tzinfo)
        days_remaining = (expiry_date - now).days
        
        if days_remaining < 30:
            logger.warning(f"Certificate {cert_path} expires in {days_remaining} days")
        
        return days_remaining
    
    def reload_certificates(self):
        """Reload certificates and recreate SSL contexts."""
        logger.info("Reloading certificates and SSL contexts")
        self._client_context = None
        self._server_context = None
        
        # Recreate contexts
        self.create_client_ssl_context()
        if self.config.server_cert_path and self.config.server_key_path:
            self.create_server_ssl_context()
        
        logger.info("Certificates reloaded successfully")
