# MSIL MCP Server - Authorization Policies
# Package: msil.authz

package msil.authz

# Default deny all requests
default allow = false

# Admin role has full access
allow {
    input.roles[_] == "admin"
}

# Developer role permissions
allow {
    input.action in ["invoke", "read", "write"]
    input.roles[_] == "developer"
    startswith(input.resource, "tool_")
}

allow {
    input.action in ["read", "write"]
    input.roles[_] == "developer"
    input.resource == "config"
}

# Operator role permissions
allow {
    input.action in ["invoke", "read"]
    input.roles[_] == "operator"
}

# User role permissions (limited)
allow {
    input.action == "invoke"
    input.roles[_] == "user"
    tool_allowed_for_user[input.resource]
}

allow {
    input.action == "read"
    input.roles[_] == "user"
    input.resource in ["tool", "dashboard"]
}

# Define allowed tools for regular users
tool_allowed_for_user[tool] {
    tool := "get_nearby_dealers"
}

tool_allowed_for_user[tool] {
    tool := "resolve_vehicle"
}

tool_allowed_for_user[tool] {
    tool := "get_service_price"
}

# Rate limiting check
allow {
    input.action == "invoke"
    not rate_limited
}

# Simple rate limiting logic (would use Redis in production)
rate_limited {
    # This is a placeholder - in production, query Redis for rate limit
    # For now, always allow
    false
}

# Reason for denial (for audit logging)
reason = msg {
    not allow
    msg := sprintf("Access denied: User with roles %v cannot perform action '%s' on resource '%s'", [input.roles, input.action, input.resource])
}

reason = "Access granted" {
    allow
}
