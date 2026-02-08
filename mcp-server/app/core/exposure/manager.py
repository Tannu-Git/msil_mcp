"""
Tool Exposure Manager - Resolves which tools a user can see/access

Implements two-layer model:
  Layer B (Exposure): Should user see this tool in tools/list?
  Layer A (Authorization): Can user execute this tool?

This module handles Layer B - the exposure/visibility layer.
Authorization is handled by PolicyEngine in policy/engine.py
"""

import logging
import time
import os
from typing import List, Set, Optional, Dict, Any, Tuple
from app.db.database import get_db_session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class ExposureManager:
    """Manages tool visibility based on exposure policies"""
    
    def __init__(self, cache_ttl_seconds: Optional[int] = None):
        """
        Initialize exposure manager with optional TTL caching.
        
        Args:
            cache_ttl_seconds: Cache Time-To-Live in seconds. If None, uses environment 
                             variable EXPOSURE_CACHE_TTL_SECONDS or defaults to 3600 (1 hour)
        """
        self._exposure_cache: Dict[str, Tuple[Set[str], float]] = {}
        
        # Determine TTL from parameter, environment, or default
        if cache_ttl_seconds is not None:
            self.cache_ttl = cache_ttl_seconds
        else:
            self.cache_ttl = int(os.getenv("EXPOSURE_CACHE_TTL_SECONDS", "3600"))
        
        logger.info(
            f"ExposureManager initialized with cache TTL: {self.cache_ttl} seconds "
            f"({self.cache_ttl // 60} minutes)"
        )
    
    def _is_cache_valid(self, cached_time: float) -> bool:
        """
        Check if cached entry is still valid based on TTL.
        
        Args:
            cached_time: Timestamp when entry was cached
            
        Returns:
            True if cache entry is still valid, False if expired
        """
        current_time = time.time()
        age = current_time - cached_time
        is_valid = age < self.cache_ttl
        
        if not is_valid:
            logger.debug(f"Cache entry expired (age: {age:.1f}s > TTL: {self.cache_ttl}s)")
        
        return is_valid
    
    async def get_exposed_tools_for_user(
        self,
        user_id: str,
        roles: List[str],
        client_application: Optional[str] = None
    ) -> Set[str]:
        """
        Get set of tool names user can see (exposure layer).
        
        Resolves permissions in order:
        1. Client-specific overrides (if provided)
        2. User's roles exposure permissions
        3. Fallback to all tools (if no restrictions defined)
        
        Args:
            user_id: User identifier for logging
            roles: List of user roles (e.g., ["developer", "operator"])
            client_application: Optional client app ID for client-specific rules (future)
            
        Returns:
            Set of tool names user can see. Can contain special values:
            - "*" means all tools
            - "__BUNDLE__{name}" means all tools in bundle
            - Tool name means specific tool
        """
        if not roles:
            logger.warning(f"User {user_id} has no roles, returning empty set")
            return set()
        
        # Check cache first
        cache_key = f"{':'.join(sorted(roles))}"
        if cache_key in self._exposure_cache:
            cached_tools, cached_time = self._exposure_cache[cache_key]
            if self._is_cache_valid(cached_time):
                logger.debug(f"Cache hit for roles {roles}")
                return cached_tools
            else:
                # Cache expired, remove it
                del self._exposure_cache[cache_key]
                logger.debug(f"Cache expired and removed for roles {roles}")
        
        # Compute exposed tools
        exposed_tools: Set[str] = set()
        
        for role in roles:
            # Get exposure permissions for this role from database
            permissions = await self._get_role_exposure_permissions(role)
            
            # Parse permissions to tool references
            tools_for_role = self._parse_exposure_permissions(permissions)
            exposed_tools.update(tools_for_role)
        
        # If any role has expose:all, grant all tools
        if "*" in exposed_tools:
            logger.debug(f"User {user_id} has expose:all (admin)")
            self._exposure_cache[cache_key] = ({"*"}, time.time())
            return {"*"}
        
        # Cache result with current timestamp
        self._exposure_cache[cache_key] = (exposed_tools, time.time())
        
        logger.debug(
            f"User {user_id} (roles={roles}) exposed to {len(exposed_tools)} "
            f"tool references (cached with TTL: {self.cache_ttl}s)"
        )
        return exposed_tools
    
    async def _get_role_exposure_permissions(self, role_name: str) -> List[str]:
        """
        Query database for all expose:* permissions of a role.
        
        Args:
            role_name: Role name (e.g., "operator")
            
        Returns:
            List of permissions like ["expose:bundle:Service Booking", "expose:tool:get_dealer"]
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text("""
                        SELECT DISTINCT prp.permission
                        FROM policy_roles pr
                        JOIN policy_role_permissions prp ON pr.id = prp.role_id
                        WHERE pr.name = :role_name
                        AND prp.permission LIKE 'expose:%'
                    """),
                    {"role_name": role_name}
                )
                rows = result.fetchall()
                permissions = [row[0] for row in rows]
                
                if permissions:
                    logger.debug(f"Role '{role_name}' has {len(permissions)} exposure permissions")
                else:
                    logger.debug(f"Role '{role_name}' has no exposure permissions")
                
                return permissions
        except Exception as e:
            logger.warning(
                f"Could not fetch exposure permissions for role '{role_name}': {e}. "
                f"Assuming role has no exposure rules."
            )
            return []
    
    def _parse_exposure_permissions(self, permissions: List[str]) -> Set[str]:
        """
        Parse exposure permission strings and return set of tool references.
        
        Permission format:
        - expose:bundle:Service Booking  -> all tools in that bundle (__BUNDLE__Service Booking)
        - expose:tool:resolve_customer   -> specific tool (resolve_customer)
        - expose:all                     -> all tools (*)
        
        Args:
            permissions: List of permission strings from database
            
        Returns:
            Set of tool references for filtering
        """
        refs: Set[str] = set()
        
        for perm in permissions:
            if perm == "expose:all":
                # Special case: admin has access to all tools
                logger.debug("Found expose:all permission")
                return {"*"}
            
            elif perm.startswith("expose:bundle:"):
                # Extract bundle name and mark for filtering
                bundle_name = perm.replace("expose:bundle:", "")
                ref = f"__BUNDLE__{bundle_name}"
                refs.add(ref)
                logger.debug(f"Added bundle permission: {bundle_name}")
            
            elif perm.startswith("expose:tool:"):
                # Extract tool name for direct filtering
                tool_name = perm.replace("expose:tool:", "")
                refs.add(tool_name)
                logger.debug(f"Added tool permission: {tool_name}")
            
            else:
                logger.warning(f"Unknown exposure permission format: {perm}")
        
        return refs
    
    async def filter_tools(
        self,
        all_tools: List[Any],
        user_id: str,
        roles: List[str],
        client_application: Optional[str] = None
    ) -> List[Any]:
        """
        Filter tool list by exposure policy.
        
        Returns subset of tools that user is exposed to based on:
        - User's roles
        - Bundle assignments
        - Tool-level assignments
        
        Args:
            all_tools: List of all active Tool objects from registry
            user_id: User identifier
            roles: User's roles
            client_application: Optional client app ID for client-specific rules
            
        Returns:
            Filtered list of exposed Tool objects
        """
        # Get exposure rules for this user
        exposed_tool_refs = await self.get_exposed_tools_for_user(
            user_id, roles, client_application
        )
        
        # If user has expose:all, return everything
        if "*" in exposed_tool_refs:
            logger.info(f"User {user_id} has expose:all, returning all {len(all_tools)} tools")
            return all_tools
        
        # Separate bundle references from tool names
        allowed_bundles: Set[str] = set()
        allowed_tool_names: Set[str] = set()
        
        for ref in exposed_tool_refs:
            if ref.startswith("__BUNDLE__"):
                bundle_name = ref.replace("__BUNDLE__", "")
                allowed_bundles.add(bundle_name)
            else:
                allowed_tool_names.add(ref)
        
        # Filter tools based on bundle membership or direct assignment
        filtered_tools = []
        
        for tool in all_tools:
            # Check if tool is directly allowed by name
            if tool.name in allowed_tool_names:
                filtered_tools.append(tool)
                continue
            
            # Check if tool's bundle is allowed
            if tool.bundle_name and tool.bundle_name in allowed_bundles:
                filtered_tools.append(tool)
                continue
        
        logger.info(
            f"Filtered {len(all_tools)} tools down to {len(filtered_tools)} "
            f"for user {user_id} (bundles={len(allowed_bundles)}, "
            f"tools={len(allowed_tool_names)})"
        )
        
        return filtered_tools
    
    def is_tool_exposed(
        self,
        tool_name: str,
        tool_bundle: Optional[str],
        exposed_refs: Set[str]
    ) -> bool:
        """
        Quick check if a specific tool is exposed to user.
        
        Used in tools/call endpoint for defense-in-depth validation.
        
        Args:
            tool_name: Name of tool to check
            tool_bundle: Bundle name of tool (optional)
            exposed_refs: Set of exposed tool references from get_exposed_tools_for_user()
            
        Returns:
            True if tool is accessible to user, False otherwise
        """
        # Check for expose:all
        if "*" in exposed_refs:
            return True
        
        # Check for direct tool assignment
        if tool_name in exposed_refs:
            return True
        
        # Check for bundle assignment
        if tool_bundle:
            bundle_ref = f"__BUNDLE__{tool_bundle}"
            if bundle_ref in exposed_refs:
                return True
        
        return False
    
    def invalidate_cache(self, role_name: Optional[str] = None):
        """
        Clear exposure cache after admin changes exposure permissions.
        
        Call this whenever exposure permissions are modified in admin API.
        
        Args:
            role_name: If provided, only invalidate this role's cache.
                      If None, clear entire cache.
        """
        if role_name:
            # Remove cache for this specific role
            # (Note: cache key is combined roles, so this removes partial matches)
            keys_to_remove = [k for k in self._exposure_cache.keys() if role_name in k]
            for key in keys_to_remove:
                del self._exposure_cache[key]
            logger.info(f"Exposure cache invalidated for role '{role_name}' ({len(keys_to_remove)} entries)")
        else:
            # Clear entire cache
            cache_size = len(self._exposure_cache)
            self._exposure_cache.clear()
            logger.info(f"Exposure cache cleared ({cache_size} entries)")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring/debugging.
        
        Returns:
            Dictionary with cache metrics
        """
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for cache_key, (_, cached_time) in self._exposure_cache.items():
            if self._is_cache_valid(cached_time):
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            "total_entries": len(self._exposure_cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "ttl_seconds": self.cache_ttl,
            "ttl_minutes": self.cache_ttl // 60
        }


# Singleton instance - use this in other modules
exposure_manager = ExposureManager()
