-- ============================================
-- PHASE 1: Tool Exposure Governance
-- Version: 1.0
-- Date: February 2, 2026
-- ============================================
-- 
-- This migration adds exposure governance to the MCP Server
-- without creating new tables. Instead, it extends the existing
-- policy_role_permissions table with new permission types.
--
-- Permission Types:
-- - expose:bundle:{bundle_name}  -> Grant access to all tools in a bundle
-- - expose:tool:{tool_name}      -> Grant access to specific tool
-- - expose:all                   -> Grant access to all tools (admin)
--
-- ============================================

-- Ensure policy_roles table exists
-- (Already created in 01-init.sql, but adding check for safety)
CREATE TABLE IF NOT EXISTS policy_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ensure policy_role_permissions table exists
CREATE TABLE IF NOT EXISTS policy_role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES policy_roles(id) ON DELETE CASCADE,
    permission VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for exposure permission lookups
CREATE INDEX IF NOT EXISTS idx_policy_role_permissions_permission 
ON policy_role_permissions(permission);

-- ============================================
-- SEED INITIAL EXPOSURE PERMISSIONS
-- Default exposure rules for standard roles
-- ============================================

-- 1. OPERATOR ROLE
-- Operator can see Service Booking tools (customer-facing operations)
INSERT INTO policy_role_permissions (role_id, permission)
SELECT r.id, 'expose:bundle:Service Booking'
FROM policy_roles r
WHERE r.name = 'operator'
ON CONFLICT (role_id, permission) DO NOTHING;

-- 2. DEVELOPER ROLE
-- Developer can see all Service Booking tools
INSERT INTO policy_role_permissions (role_id, permission)
SELECT r.id, 'expose:bundle:Service Booking'
FROM policy_roles r
WHERE r.name = 'developer'
ON CONFLICT (role_id, permission) DO NOTHING;

-- 3. ADMIN ROLE
-- Admin can see ALL tools (no restrictions)
INSERT INTO policy_role_permissions (role_id, permission)
SELECT r.id, 'expose:all'
FROM policy_roles r
WHERE r.name = 'admin'
ON CONFLICT (role_id, permission) DO NOTHING;

-- ============================================
-- EXPOSURE GOVERNANCE TABLE
-- Optional: For Phase 2 (Profiles)
-- This table is NOT created in Phase 1 but structure is documented here
-- ============================================
--
-- CREATE TABLE IF NOT EXISTS exposure_profiles (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     name VARCHAR(255) NOT NULL UNIQUE,
--     description TEXT,
--     allowed_bundles JSONB DEFAULT '[]',
--     allowed_tool_ids JSONB DEFAULT '[]',
--     denied_tool_ids JSONB DEFAULT '[]',
--     environment VARCHAR(50),  -- 'dev', 'staging', 'prod'
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );
--
-- CREATE TABLE IF NOT EXISTS role_profile_map (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     role_id UUID NOT NULL REFERENCES policy_roles(id) ON DELETE CASCADE,
--     profile_id UUID NOT NULL REFERENCES exposure_profiles(id) ON DELETE CASCADE,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
--     UNIQUE(role_id, profile_id)
-- );

-- ============================================
-- VERIFICATION QUERIES
-- Run these to verify migration success
-- ============================================

-- Verify exposure permissions were created
-- SELECT r.name, prp.permission
-- FROM policy_roles r
-- JOIN policy_role_permissions prp ON r.id = prp.role_id
-- WHERE prp.permission LIKE 'expose:%'
-- ORDER BY r.name, prp.permission;

-- Count tools per bundle (for verification)
-- SELECT bundle_name, COUNT(*) as tool_count
-- FROM tools
-- WHERE is_active = true
-- GROUP BY bundle_name
-- ORDER BY tool_count DESC;

-- ============================================
-- ROLLBACK SCRIPT (if needed)
-- Uncomment to remove all exposure permissions
-- ============================================

-- DELETE FROM policy_role_permissions 
-- WHERE permission LIKE 'expose:%';
