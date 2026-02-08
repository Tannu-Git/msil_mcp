"""Request context and auth dependency for runtime decisions."""
import uuid
from dataclasses import dataclass
from typing import List, Optional

from fastapi import Header, HTTPException, Request, status

from app.config import settings
from app.core.auth.jwt_handler import JWTHandler
from app.core.auth.jwks_client import JWKSClient
from app.core.auth.oidc_validator import OIDCTokenValidator


@dataclass
class RequestContext:
    """Normalized request context for authz and governance."""

    user_id: Optional[str]
    roles: List[str]
    scopes: List[str]
    client_id: Optional[str]
    correlation_id: str
    ip: Optional[str]
    env: str
    is_elevated: bool = False  # Whether user has elevation privileges


def _parse_list_claim(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v]
    if isinstance(value, str):
        parts = [v.strip() for v in value.replace(" ", ",").split(",")]
        return [p for p in parts if p]
    return []


def _get_oidc_validator() -> Optional[OIDCTokenValidator]:
    if not settings.OIDC_ENABLED:
        return None
    if not (settings.OIDC_JWKS_URL and settings.OIDC_ISSUER and settings.OIDC_AUDIENCE):
        return None
    jwks_client = JWKSClient(settings.OIDC_JWKS_URL, cache_ttl=settings.OIDC_JWKS_CACHE_TTL)
    return OIDCTokenValidator(
        jwks_client=jwks_client,
        issuer=settings.OIDC_ISSUER,
        audience=settings.OIDC_AUDIENCE,
        required_scopes=_parse_list_claim(settings.OIDC_REQUIRED_SCOPES)
    )


async def get_request_context(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_roles: Optional[str] = Header(None, alias="X-User-Roles"),
    x_client_id: Optional[str] = Header(None, alias="X-Client-ID"),
    x_scopes: Optional[str] = Header(None, alias="X-Scopes"),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
) -> RequestContext:
    """Resolve and validate request context from headers and JWT/OIDC."""
    correlation_id = x_correlation_id or f"req-{uuid.uuid4()}"
    token = None

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    payload = None
    if token:
        if settings.OIDC_ENABLED:
            validator = _get_oidc_validator()
            if validator is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="OIDC validator not configured"
                )
            payload = await validator.validate_token(token)
        else:
            jwt_handler = JWTHandler(
                secret_key=settings.JWT_SECRET,
                algorithm=settings.JWT_ALGORITHM,
                access_token_expire_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
                refresh_token_expire_days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
            try:
                payload = jwt_handler.verify_token(token)
            except ValueError:
                payload = None

    if payload is None and settings.AUTH_REQUIRED and not (settings.DEMO_MODE and settings.DEMO_MODE_AUTH_BYPASS):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    if payload:
        user_id = payload.get(settings.USER_ID_CLAIM, payload.get("sub"))
        roles = _parse_list_claim(payload.get(settings.ROLES_CLAIM, payload.get("roles")))
        scopes = _parse_list_claim(payload.get(settings.SCOPES_CLAIM, payload.get("scope")))
        client_id = payload.get(settings.CLIENT_ID_CLAIM, payload.get("azp"))
        
        # Check for elevation in token claims
        elevation_claim = payload.get("elevation", {})
        if isinstance(elevation_claim, dict):
            is_elevated = elevation_claim.get("elevated", False)
        elif isinstance(elevation_claim, bool):
            is_elevated = elevation_claim
        else:
            is_elevated = False
    else:
        user_id = x_user_id or "demo"
        roles = _parse_list_claim(x_user_roles) or [settings.DEMO_MODE_DEFAULT_ROLE]
        scopes = _parse_list_claim(x_scopes)
        client_id = x_client_id
        is_elevated = False

    return RequestContext(
        user_id=user_id,
        roles=roles,
        scopes=scopes,
        client_id=client_id,
        correlation_id=correlation_id,
        ip=request.client.host if request.client else None,
        env=settings.ENVIRONMENT,
        is_elevated=is_elevated
    )
