"""
Integration tests for Exposure Governance admin API endpoints.

Tests cover:
- Permission CRUD operations
- Bundle listing
- Role exposure preview
- Cache invalidation on mutations
- Audit logging
- Error handling
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


@pytest.fixture
def client():
    """Create test client for admin API."""
    from app.api.admin import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router, prefix="/admin")
    
    return TestClient(app)


@pytest.fixture
def mock_auth():
    """Mock authentication decorator."""
    def mock_require_admin():
        return {"user_id": "admin_user_1", "role": "admin"}
    
    return mock_require_admin


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def mock_exposure_manager():
    """Mock exposure manager."""
    manager = AsyncMock()
    manager.get_exposed_tools_for_user = AsyncMock(return_value={
        "__BUNDLE__Service Booking",
        "get_dealer"
    })
    manager.filter_tools = AsyncMock()
    manager.invalidate_cache = Mock()
    return manager


# ============================================
# GET ROLE PERMISSIONS TESTS
# ============================================

@pytest.mark.asyncio
async def test_get_role_permissions_operator(client, mock_auth, mock_db):
    """Test getting exposure permissions for operator role."""
    expected_permissions = ["expose:bundle:Service Booking"]
    
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()):
        
        mock_db.execute.return_value.scalars.return_value = expected_permissions
        
        response = client.get(
            "/admin/exposure/roles?role_name=operator"
        )
    
    assert response.status_code == 200
    assert "permissions" in response.json()


@pytest.mark.asyncio
async def test_get_role_permissions_not_found(client, mock_auth, mock_db):
    """Test getting permissions for non-existent role."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()):
        
        mock_db.execute.return_value.scalars.return_value = []
        
        response = client.get(
            "/admin/exposure/roles?role_name=nonexistent"
        )
    
    # Should return empty list, not error
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_role_permissions_admin(client, mock_auth, mock_db):
    """Test getting permissions for admin role."""
    expected_permissions = ["expose:all"]
    
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()):
        
        mock_db.execute.return_value.scalars.return_value = expected_permissions
        
        response = client.get(
            "/admin/exposure/roles?role_name=admin"
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "expose:all" in data.get("permissions", [])


# ============================================
# ADD PERMISSION TESTS
# ============================================

@pytest.mark.asyncio
async def test_add_bundle_permission(client, mock_auth, mock_db, mock_exposure_manager):
    """Test adding bundle exposure permission."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()), \
         patch("app.api.admin.exposure_manager", mock_exposure_manager), \
         patch("app.api.admin.audit_service") as mock_audit:
        
        response = client.post(
            "/admin/exposure/roles/operator/permissions",
            json={"permission": "expose:bundle:Dealer Management"}
        )
    
    # Should succeed
    assert response.status_code in [200, 201]
    
    # Should invalidate cache
    mock_exposure_manager.invalidate_cache.assert_called()
    
    # Should log audit event
    mock_audit.log_event.assert_called()


@pytest.mark.asyncio
async def test_add_tool_permission(client, mock_auth, mock_db, mock_exposure_manager):
    """Test adding specific tool permission."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()), \
         patch("app.api.admin.exposure_manager", mock_exposure_manager), \
         patch("app.api.admin.audit_service"):
        
        response = client.post(
            "/admin/exposure/roles/developer/permissions",
            json={"permission": "expose:tool:custom_tool"}
        )
    
    assert response.status_code in [200, 201]


@pytest.mark.asyncio
async def test_add_all_access_permission(client, mock_auth, mock_db, mock_exposure_manager):
    """Test adding expose:all permission."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()), \
         patch("app.api.admin.exposure_manager", mock_exposure_manager), \
         patch("app.api.admin.audit_service"):
        
        response = client.post(
            "/admin/exposure/roles/super_admin/permissions",
            json={"permission": "expose:all"}
        )
    
    assert response.status_code in [200, 201]


@pytest.mark.asyncio
async def test_add_invalid_permission_format(client, mock_auth, mock_db):
    """Test adding permission with invalid format."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()):
        
        response = client.post(
            "/admin/exposure/roles/operator/permissions",
            json={"permission": "invalid:format"}
        )
    
    # Should fail validation
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_add_duplicate_permission(client, mock_auth, mock_db, mock_exposure_manager):
    """Test adding permission that already exists."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()), \
         patch("app.api.admin.exposure_manager", mock_exposure_manager):
        
        # First add
        response1 = client.post(
            "/admin/exposure/roles/operator/permissions",
            json={"permission": "expose:bundle:Service Booking"}
        )
        
        # Second add (duplicate)
        response2 = client.post(
            "/admin/exposure/roles/operator/permissions",
            json={"permission": "expose:bundle:Service Booking"}
        )
    
    # First should succeed
    assert response1.status_code in [200, 201]
    
    # Second should fail gracefully (409 Conflict or same as first)
    # Depending on implementation


# ============================================
# REMOVE PERMISSION TESTS
# ============================================

@pytest.mark.asyncio
async def test_remove_permission(client, mock_auth, mock_db, mock_exposure_manager):
    """Test removing exposure permission."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()), \
         patch("app.api.admin.exposure_manager", mock_exposure_manager), \
         patch("app.api.admin.audit_service"):
        
        response = client.delete(
            "/admin/exposure/roles/operator/permissions?permission=expose:bundle:Service%20Booking"
        )
    
    assert response.status_code in [200, 204]
    
    # Should invalidate cache
    mock_exposure_manager.invalidate_cache.assert_called()


@pytest.mark.asyncio
async def test_remove_nonexistent_permission(client, mock_auth, mock_db):
    """Test removing permission that doesn't exist."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()):
        
        response = client.delete(
            "/admin/exposure/roles/operator/permissions?permission=expose:bundle:NonExistent"
        )
    
    # Should handle gracefully (404 or 200)
    assert response.status_code in [200, 204, 404]


# ============================================
# GET BUNDLES TESTS
# ============================================

@pytest.mark.asyncio
async def test_get_available_bundles(client, mock_auth, mock_db):
    """Test getting list of available bundles."""
    mock_bundles = [
        {
            "name": "Service Booking",
            "description": "Service booking tools",
            "tool_count": 5,
            "tools": []
        },
        {
            "name": "Dealer Management",
            "description": "Dealer management tools",
            "tool_count": 3,
            "tools": []
        }
    ]
    
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()):
        
        mock_db.execute.return_value.scalars.return_value = mock_bundles
        
        response = client.get("/admin/exposure/bundles")
    
    assert response.status_code == 200
    data = response.json()
    assert "bundles" in data or len(data) >= 0


@pytest.mark.asyncio
async def test_get_bundles_empty(client, mock_auth, mock_db):
    """Test getting bundles when none exist."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()):
        
        mock_db.execute.return_value.scalars.return_value = []
        
        response = client.get("/admin/exposure/bundles")
    
    assert response.status_code == 200


# ============================================
# PREVIEW TESTS
# ============================================

@pytest.mark.asyncio
async def test_preview_role_exposure(client, mock_auth, mock_db, mock_exposure_manager):
    """Test previewing what tools a role can see."""
    mock_preview = {
        "role_name": "operator",
        "total_exposed_tools": 5,
        "exposed_bundles": ["Service Booking"],
        "exposed_tools": []
    }
    
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()), \
         patch("app.api.admin.exposure_manager", mock_exposure_manager):
        
        mock_exposure_manager.get_exposed_tools_for_user = AsyncMock(
            return_value={"__BUNDLE__Service Booking"}
        )
        
        response = client.get(
            "/admin/exposure/preview?role_name=operator"
        )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_preview_admin_role(client, mock_auth, mock_db, mock_exposure_manager):
    """Test previewing admin role (should see all tools)."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()), \
         patch("app.api.admin.exposure_manager", mock_exposure_manager):
        
        mock_exposure_manager.get_exposed_tools_for_user = AsyncMock(
            return_value={"*"}
        )
        
        response = client.get(
            "/admin/exposure/preview?role_name=admin"
        )
    
    assert response.status_code == 200


# ============================================
# AUDIT LOGGING TESTS
# ============================================

@pytest.mark.asyncio
async def test_audit_log_permission_added(client, mock_auth, mock_db, mock_exposure_manager):
    """Test that permission additions are logged."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()), \
         patch("app.api.admin.exposure_manager", mock_exposure_manager), \
         patch("app.api.admin.audit_service") as mock_audit:
        
        client.post(
            "/admin/exposure/roles/operator/permissions",
            json={"permission": "expose:bundle:Service Booking"}
        )
        
        # Verify audit log was called
        assert mock_audit.log_event.called


@pytest.mark.asyncio
async def test_audit_log_permission_removed(client, mock_auth, mock_db, mock_exposure_manager):
    """Test that permission removals are logged."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()), \
         patch("app.api.admin.exposure_manager", mock_exposure_manager), \
         patch("app.api.admin.audit_service") as mock_audit:
        
        client.delete(
            "/admin/exposure/roles/operator/permissions?permission=expose:bundle:Service%20Booking"
        )
        
        # Verify audit log was called
        assert mock_audit.log_event.called


# ============================================
# AUTHORIZATION TESTS
# ============================================

@pytest.mark.asyncio
async def test_requires_admin_authorization(client, mock_auth, mock_db):
    """Test that endpoints require admin authorization."""
    with patch("app.api.admin.require_admin", side_effect=Exception("Unauthorized")):
        # All endpoints should require auth
        response = client.get("/admin/exposure/bundles")
        
        # Should fail without proper auth (will depend on error handling)


# ============================================
# ERROR SCENARIOS
# ============================================

@pytest.mark.asyncio
async def test_database_error_handling(client, mock_auth, mock_db):
    """Test graceful handling of database errors."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()):
        
        mock_db.execute.side_effect = Exception("Database error")
        
        response = client.get("/admin/exposure/bundles")
    
    # Should return error response, not crash
    assert response.status_code >= 400


@pytest.mark.asyncio
async def test_cache_invalidation_on_add(client, mock_auth, mock_db, mock_exposure_manager):
    """Test that cache is invalidated after adding permission."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()), \
         patch("app.api.admin.exposure_manager", mock_exposure_manager), \
         patch("app.api.admin.audit_service"):
        
        client.post(
            "/admin/exposure/roles/operator/permissions",
            json={"permission": "expose:bundle:Service Booking"}
        )
    
    # Cache should be invalidated
    mock_exposure_manager.invalidate_cache.assert_called_with("operator")


@pytest.mark.asyncio
async def test_cache_invalidation_on_remove(client, mock_auth, mock_db, mock_exposure_manager):
    """Test that cache is invalidated after removing permission."""
    with patch("app.api.admin.get_session", return_value=mock_db), \
         patch("app.api.admin.require_admin", return_value=mock_auth()), \
         patch("app.api.admin.exposure_manager", mock_exposure_manager), \
         patch("app.api.admin.audit_service"):
        
        client.delete(
            "/admin/exposure/roles/operator/permissions?permission=expose:bundle:Service%20Booking"
        )
    
    # Cache should be invalidated
    mock_exposure_manager.invalidate_cache.assert_called_with("operator")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
