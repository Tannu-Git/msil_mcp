"""
Custom exceptions for MCP Server

Exposure layer exceptions (Layer B - visibility)
Authorization exceptions (Layer A - capability)
"""


# ============================================
# Exposure Exceptions (Layer B)
# ============================================

class ExposureError(Exception):
    """Base class for exposure-related errors"""
    pass


class ToolNotExposedError(ExposureError):
    """
    Tool is not in user's exposure set.
    
    User's role doesn't have access to this tool's bundle or the tool itself.
    This happens when exposure filtering prevents tool visibility.
    """
    pass


# ============================================
# Authorization Exceptions (Layer A)
# ============================================

class AuthorizationError(Exception):
    """
    User lacks required authorization to execute action.
    
    Different from ToolNotExposedError:
    - Tool may be visible (in exposure set)
    - But user lacks role/permission to execute it
    """
    pass


# ============================================
# Tool Registry Exceptions
# ============================================

class ToolNotFoundError(Exception):
    """Tool not found in registry"""
    pass


class ToolRegistrationError(Exception):
    """Error registering tool in registry"""
    pass


# ============================================
# Policy Exceptions
# ============================================

class PolicyError(Exception):
    """Policy evaluation or enforcement error"""
    pass


class RateLimitError(Exception):
    """Rate limit exceeded"""
    pass
