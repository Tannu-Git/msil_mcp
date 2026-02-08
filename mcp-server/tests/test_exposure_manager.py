"""
Unit tests for ExposureManager service.

Tests cover:
- Permission retrieval and caching
- Tool filtering logic
- Exposure validation
- Cache invalidation
- Permission parsing
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.core.exposure.manager import ExposureManager
from app.core.exceptions import ToolNotExposedError


class MockDatabase:
    """Mock database session for testing."""
    
    async def execute(self, query):
        """Mock database query execution."""
        # Return mock permissions based on query
        if "operator" in str(query):
            return Mock(scalars=Mock(return_value=["expose:bundle:Service Booking"]))
        elif "developer" in str(query):
            return Mock(scalars=Mock(return_value=[
                "expose:bundle:Service Booking",
                "expose:tool:get_dealer"
            ]))
        elif "admin" in str(query):
            return Mock(scalars=Mock(return_value=["expose:all"]))
        return Mock(scalars=Mock(return_value=[]))


class MockTool:
    """Mock tool object for testing."""
    
    def __init__(self, name: str, bundle: str = "Service Booking"):
        self.name = name
        self.bundle_name = bundle
        self.display_name = f"Display {name}"
        self.description = f"Tool: {name}"


@pytest.fixture
async def manager():
    """Create ExposureManager instance for testing."""
    manager = ExposureManager()
    manager.db = AsyncMock()
    return manager


@pytest.fixture
def tools():
    """Create mock tools for testing."""
    return [
        MockTool("book_appointment", "Service Booking"),
        MockTool("list_appointments", "Service Booking"),
        MockTool("get_dealer", "Dealer Management"),
        MockTool("update_dealer", "Dealer Management"),
        MockTool("get_customer", "Customer Management"),
    ]


# ============================================
# PERMISSION PARSING TESTS
# ============================================

@pytest.mark.asyncio
async def test_parse_expose_all_permission():
    """Test parsing expose:all permission."""
    manager = ExposureManager()
    
    permissions = ["expose:all"]
    parsed = manager._parse_exposure_permissions(permissions)
    
    assert "*" in parsed
    assert len(parsed) == 1


@pytest.mark.asyncio
async def test_parse_bundle_permission():
    """Test parsing expose:bundle:* permission."""
    manager = ExposureManager()
    
    permissions = ["expose:bundle:Service Booking"]
    parsed = manager._parse_exposure_permissions(permissions)
    
    assert "__BUNDLE__Service Booking" in parsed


@pytest.mark.asyncio
async def test_parse_tool_permission():
    """Test parsing expose:tool:* permission."""
    manager = ExposureManager()
    
    permissions = ["expose:tool:get_dealer"]
    parsed = manager._parse_exposure_permissions(permissions)
    
    assert "get_dealer" in parsed


@pytest.mark.asyncio
async def test_parse_multiple_permissions():
    """Test parsing multiple permissions."""
    manager = ExposureManager()
    
    permissions = [
        "expose:bundle:Service Booking",
        "expose:tool:get_dealer",
        "expose:tool:update_dealer",
    ]
    parsed = manager._parse_exposure_permissions(permissions)
    
    assert len(parsed) == 3
    assert "__BUNDLE__Service Booking" in parsed
    assert "get_dealer" in parsed
    assert "update_dealer" in parsed


@pytest.mark.asyncio
async def test_parse_malformed_permission():
    """Test parsing malformed permission (should be ignored)."""
    manager = ExposureManager()
    
    permissions = [
        "expose:bundle:Service Booking",
        "invalid:permission:format",
        "expose:tool:get_dealer",
    ]
    parsed = manager._parse_exposure_permissions(permissions)
    
    # Should only parse valid permissions
    assert len(parsed) == 2
    assert "invalid:permission:format" not in parsed


# ============================================
# TOOL EXPOSURE VALIDATION TESTS
# ============================================

@pytest.mark.asyncio
async def test_is_tool_exposed_with_all_access():
    """Test tool exposure check with expose:all permission."""
    manager = ExposureManager()
    
    exposed_refs = {"*"}
    is_exposed = manager.is_tool_exposed(
        "any_tool",
        "Any Bundle",
        exposed_refs
    )
    
    assert is_exposed is True


@pytest.mark.asyncio
async def test_is_tool_exposed_with_bundle_permission():
    """Test tool exposure check with bundle permission."""
    manager = ExposureManager()
    
    exposed_refs = {"__BUNDLE__Service Booking"}
    is_exposed = manager.is_tool_exposed(
        "book_appointment",
        "Service Booking",
        exposed_refs
    )
    
    assert is_exposed is True


@pytest.mark.asyncio
async def test_is_tool_exposed_with_tool_permission():
    """Test tool exposure check with specific tool permission."""
    manager = ExposureManager()
    
    exposed_refs = {"get_dealer", "update_dealer"}
    is_exposed = manager.is_tool_exposed(
        "get_dealer",
        "Dealer Management",
        exposed_refs
    )
    
    assert is_exposed is True


@pytest.mark.asyncio
async def test_is_tool_not_exposed():
    """Test tool exposure check when tool is not exposed."""
    manager = ExposureManager()
    
    exposed_refs = {"__BUNDLE__Service Booking"}
    is_exposed = manager.is_tool_exposed(
        "get_dealer",
        "Dealer Management",
        exposed_refs
    )
    
    assert is_exposed is False


@pytest.mark.asyncio
async def test_is_tool_exposed_empty_refs():
    """Test tool exposure check with empty exposed refs."""
    manager = ExposureManager()
    
    exposed_refs = set()
    is_exposed = manager.is_tool_exposed(
        "any_tool",
        "Any Bundle",
        exposed_refs
    )
    
    assert is_exposed is False


# ============================================
# TOOL FILTERING TESTS
# ============================================

@pytest.mark.asyncio
async def test_filter_tools_with_all_access(manager, tools):
    """Test filtering tools with expose:all permission."""
    # Mock database to return expose:all
    manager.db.execute = AsyncMock()
    manager.db.execute.return_value.scalars.return_value = ["expose:all"]
    
    # Patch actual DB query
    with patch.object(manager, '_get_role_exposure_permissions', return_value=["expose:all"]):
        filtered = await manager.filter_tools(
            tools,
            "user123",
            ["admin"],
            "web"
        )
    
    # Should return all tools
    assert len(filtered) == 5


@pytest.mark.asyncio
async def test_filter_tools_with_bundle_permission(manager, tools):
    """Test filtering tools with bundle permission."""
    with patch.object(manager, '_get_role_exposure_permissions', return_value=["expose:bundle:Service Booking"]):
        filtered = await manager.filter_tools(
            tools,
            "user123",
            ["operator"],
            "web"
        )
    
    # Should return only Service Booking tools
    assert len(filtered) == 2
    assert all(t.bundle_name == "Service Booking" for t in filtered)


@pytest.mark.asyncio
async def test_filter_tools_with_tool_permission(manager, tools):
    """Test filtering tools with specific tool permissions."""
    with patch.object(manager, '_get_role_exposure_permissions', return_value=[
        "expose:tool:get_dealer",
        "expose:tool:update_dealer"
    ]):
        filtered = await manager.filter_tools(
            tools,
            "user123",
            ["developer"],
            "web"
        )
    
    # Should return only specified tools
    assert len(filtered) == 2
    assert all(t.name in ["get_dealer", "update_dealer"] for t in filtered)


@pytest.mark.asyncio
async def test_filter_tools_with_mixed_permissions(manager, tools):
    """Test filtering tools with mixed permission types."""
    with patch.object(manager, '_get_role_exposure_permissions', return_value=[
        "expose:bundle:Service Booking",
        "expose:tool:get_dealer"
    ]):
        filtered = await manager.filter_tools(
            tools,
            "user123",
            ["custom_role"],
            "web"
        )
    
    # Should return Service Booking tools + get_dealer (which is in Dealer Management)
    assert len(filtered) == 3
    tool_names = {t.name for t in filtered}
    assert "book_appointment" in tool_names
    assert "list_appointments" in tool_names
    assert "get_dealer" in tool_names


@pytest.mark.asyncio
async def test_filter_tools_no_permissions(manager, tools):
    """Test filtering tools with no permissions."""
    with patch.object(manager, '_get_role_exposure_permissions', return_value=[]):
        filtered = await manager.filter_tools(
            tools,
            "user123",
            ["restricted_role"],
            "web"
        )
    
    # Should return no tools
    assert len(filtered) == 0


@pytest.mark.asyncio
async def test_filter_tools_empty_list(manager):
    """Test filtering empty tool list."""
    with patch.object(manager, '_get_role_exposure_permissions', return_value=["expose:all"]):
        filtered = await manager.filter_tools(
            [],
            "user123",
            ["admin"],
            "web"
        )
    
    assert len(filtered) == 0


# ============================================
# CACHING TESTS
# ============================================

@pytest.mark.asyncio
async def test_cache_hit_on_repeated_request(manager):
    """Test that repeated requests hit cache."""
    call_count = 0
    
    async def mock_get_permissions(role):
        nonlocal call_count
        call_count += 1
        return ["expose:bundle:Service Booking"]
    
    with patch.object(manager, '_get_role_exposure_permissions', side_effect=mock_get_permissions):
        # First call - cache miss
        result1 = await manager.get_exposed_tools_for_user("user1", ["operator"], "web")
        
        # Second call - cache hit
        result2 = await manager.get_exposed_tools_for_user("user1", ["operator"], "web")
        
        # Should only call once due to caching
        assert call_count == 1
        assert result1 == result2


@pytest.mark.asyncio
async def test_cache_different_for_different_roles(manager):
    """Test that different roles have separate cache entries."""
    call_count = 0
    permissions_map = {
        "operator": ["expose:bundle:Service Booking"],
        "admin": ["expose:all"],
    }
    
    async def mock_get_permissions(role):
        nonlocal call_count
        call_count += 1
        return permissions_map.get(role, [])
    
    with patch.object(manager, '_get_role_exposure_permissions', side_effect=mock_get_permissions):
        # Call with different roles
        result1 = await manager.get_exposed_tools_for_user("user1", ["operator"], "web")
        result2 = await manager.get_exposed_tools_for_user("user1", ["admin"], "web")
        
        # Should call twice for different roles
        assert call_count == 2
        assert result1 != result2


@pytest.mark.asyncio
async def test_cache_invalidation(manager):
    """Test cache invalidation on permission update."""
    call_count = 0
    
    async def mock_get_permissions(role):
        nonlocal call_count
        call_count += 1
        return ["expose:bundle:Service Booking"]
    
    with patch.object(manager, '_get_role_exposure_permissions', side_effect=mock_get_permissions):
        # First call - cache miss
        await manager.get_exposed_tools_for_user("user1", ["operator"], "web")
        
        # Invalidate cache
        manager.invalidate_cache("operator")
        
        # Second call - cache miss (due to invalidation)
        await manager.get_exposed_tools_for_user("user1", ["operator"], "web")
        
        # Should call twice (once before, once after invalidation)
        assert call_count == 2


@pytest.mark.asyncio
async def test_cache_invalidate_all_roles(manager):
    """Test invalidating cache for all roles."""
    call_count = 0
    
    async def mock_get_permissions(role):
        nonlocal call_count
        call_count += 1
        return ["expose:all"]
    
    with patch.object(manager, '_get_role_exposure_permissions', side_effect=mock_get_permissions):
        # Make requests with multiple roles
        await manager.get_exposed_tools_for_user("user1", ["operator"], "web")
        await manager.get_exposed_tools_for_user("user1", ["admin"], "web")
        
        # Should be 2 calls
        assert call_count == 2
        
        # Invalidate all
        manager.invalidate_cache()
        
        # Make same requests again
        await manager.get_exposed_tools_for_user("user1", ["operator"], "web")
        await manager.get_exposed_tools_for_user("user1", ["admin"], "web")
        
        # Should be 4 calls total (cache was cleared)
        assert call_count == 4


# ============================================
# ERROR HANDLING TESTS
# ============================================

@pytest.mark.asyncio
async def test_get_exposed_tools_with_multiple_roles(manager):
    """Test getting exposed tools with multiple roles."""
    permissions_map = {
        "operator": ["expose:bundle:Service Booking"],
        "developer": ["expose:tool:get_dealer"],
    }
    
    async def mock_get_permissions(role):
        return permissions_map.get(role, [])
    
    with patch.object(manager, '_get_role_exposure_permissions', side_effect=mock_get_permissions):
        result = await manager.get_exposed_tools_for_user(
            "user1",
            ["operator", "developer"],
            "web"
        )
    
    # Should combine permissions from both roles
    assert "__BUNDLE__Service Booking" in result
    assert "get_dealer" in result


@pytest.mark.asyncio
async def test_get_exposed_tools_empty_roles(manager):
    """Test getting exposed tools with no roles."""
    result = await manager.get_exposed_tools_for_user(
        "user1",
        [],
        "web"
    )
    
    # Should return empty set
    assert result == set()


@pytest.mark.asyncio
async def test_filter_tools_preserves_metadata(manager, tools):
    """Test that filtering preserves tool metadata."""
    with patch.object(manager, '_get_role_exposure_permissions', return_value=["expose:all"]):
        filtered = await manager.filter_tools(
            tools,
            "user1",
            ["admin"],
            "web"
        )
    
    # Verify metadata is preserved
    for original, filtered_tool in zip(tools, filtered):
        assert filtered_tool.name == original.name
        assert filtered_tool.bundle_name == original.bundle_name
        assert filtered_tool.display_name == original.display_name


# ============================================
# EDGE CASES
# ============================================

@pytest.mark.asyncio
async def test_bundle_name_with_special_characters(manager):
    """Test bundle names with special characters."""
    manager = ExposureManager()
    
    permissions = ["expose:bundle:Service Booking & Cancellation"]
    parsed = manager._parse_exposure_permissions(permissions)
    
    assert "__BUNDLE__Service Booking & Cancellation" in parsed


@pytest.mark.asyncio
async def test_tool_name_with_special_characters(manager):
    """Test tool names with special characters."""
    manager = ExposureManager()
    
    permissions = ["expose:tool:get_dealer/info"]
    parsed = manager._parse_exposure_permissions(permissions)
    
    assert "get_dealer/info" in parsed


@pytest.mark.asyncio
async def test_very_large_permission_list(manager):
    """Test handling very large permission lists."""
    # Create 1000 permissions
    permissions = [f"expose:tool:tool_{i}" for i in range(1000)]
    
    parsed = manager._parse_exposure_permissions(permissions)
    
    # Should parse all
    assert len(parsed) == 1000


@pytest.mark.asyncio
async def test_duplicate_permissions(manager):
    """Test handling duplicate permissions."""
    manager = ExposureManager()
    
    permissions = [
        "expose:bundle:Service Booking",
        "expose:bundle:Service Booking",
        "expose:tool:get_dealer",
        "expose:tool:get_dealer",
    ]
    parsed = manager._parse_exposure_permissions(permissions)
    
    # Should be parsed as set (no duplicates)
    # When converted to set, should have 2 unique items
    unique_parsed = set(parsed)
    assert "__BUNDLE__Service Booking" in unique_parsed
    assert "get_dealer" in unique_parsed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
