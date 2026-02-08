-- MSIL MCP Server Database Schema
-- Version: 1.0
-- Date: January 30, 2026

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TOOLS TABLE
-- ============================================
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    bundle_name VARCHAR(255),
    api_endpoint VARCHAR(500) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    input_schema JSONB NOT NULL,
    output_schema JSONB,
    headers JSONB DEFAULT '{}',
    auth_type VARCHAR(50) DEFAULT 'none',
    is_active BOOLEAN DEFAULT true,
    version VARCHAR(20) DEFAULT '1.0.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for tool lookups
CREATE INDEX idx_tools_name ON tools(name);
CREATE INDEX idx_tools_category ON tools(category);
CREATE INDEX idx_tools_bundle ON tools(bundle_name);
CREATE INDEX idx_tools_active ON tools(is_active);

-- ============================================
-- SERVICE BOOKINGS TABLE
-- ============================================
CREATE TABLE service_bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id VARCHAR(50) NOT NULL UNIQUE,
    customer_mobile VARCHAR(15) NOT NULL,
    customer_name VARCHAR(255),
    vehicle_registration VARCHAR(20) NOT NULL,
    vehicle_model VARCHAR(100),
    dealer_code VARCHAR(50) NOT NULL,
    dealer_name VARCHAR(255),
    service_type VARCHAR(50) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status VARCHAR(50) DEFAULT 'CONFIRMED',
    notes TEXT,
    created_via VARCHAR(50) DEFAULT 'MCP',
    correlation_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for booking lookups
CREATE INDEX idx_bookings_booking_id ON service_bookings(booking_id);
CREATE INDEX idx_bookings_mobile ON service_bookings(customer_mobile);
CREATE INDEX idx_bookings_vehicle ON service_bookings(vehicle_registration);
CREATE INDEX idx_bookings_status ON service_bookings(status);
CREATE INDEX idx_bookings_date ON service_bookings(appointment_date);

-- ============================================
-- TOOL EXECUTIONS TABLE (Audit Log)
-- ============================================
CREATE TABLE tool_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    correlation_id UUID NOT NULL,
    tool_name VARCHAR(255) NOT NULL,
    input_params JSONB,
    output_result JSONB,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    execution_time_ms INTEGER,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for execution lookups
CREATE INDEX idx_executions_correlation ON tool_executions(correlation_id);
CREATE INDEX idx_executions_tool ON tool_executions(tool_name);
CREATE INDEX idx_executions_status ON tool_executions(status);
CREATE INDEX idx_executions_created ON tool_executions(created_at);

-- ============================================
-- OPENAPI SPECS (Persisted Imports)
-- ============================================
CREATE TABLE openapi_specs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50),
    description TEXT,
    source_url TEXT,
    file_name VARCHAR(255),
    format VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'parsed'
);

CREATE INDEX idx_openapi_specs_name ON openapi_specs(name);
CREATE INDEX idx_openapi_specs_status ON openapi_specs(status);
CREATE INDEX idx_openapi_specs_uploaded ON openapi_specs(uploaded_at);

CREATE TABLE openapi_spec_tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    spec_id UUID NOT NULL REFERENCES openapi_specs(id) ON DELETE CASCADE,
    tool_id UUID,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    bundle_name VARCHAR(255),
    api_endpoint VARCHAR(500) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    input_schema JSONB NOT NULL,
    output_schema JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_openapi_tools_spec ON openapi_spec_tools(spec_id);
CREATE INDEX idx_openapi_tools_name ON openapi_spec_tools(name);
CREATE INDEX idx_openapi_tools_bundle ON openapi_spec_tools(bundle_name);

-- ============================================
-- POLICY ROLES & PERMISSIONS
-- ============================================
CREATE TABLE policy_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE policy_role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES policy_roles(id) ON DELETE CASCADE,
    permission VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_policy_roles_name ON policy_roles(name);
CREATE INDEX idx_policy_role_permissions_role ON policy_role_permissions(role_id);

-- ============================================
-- CHAT SESSIONS TABLE
-- ============================================
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL UNIQUE,
    user_id VARCHAR(255),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    message_count INTEGER DEFAULT 0,
    tools_used JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX idx_sessions_user_id ON chat_sessions(user_id);

-- ============================================
-- CHAT MESSAGES TABLE
-- ============================================
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system', 'tool'
    content TEXT,
    tool_calls JSONB,
    tool_call_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_session ON chat_messages(session_id);
CREATE INDEX idx_messages_created ON chat_messages(created_at);

-- ============================================
-- METRICS TABLE
-- ============================================
CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    dimensions JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_name ON metrics(metric_name);
CREATE INDEX idx_metrics_recorded ON metrics(recorded_at);

-- ============================================
-- SEED DATA - DEMO TOOLS
-- ============================================
INSERT INTO tools (name, display_name, description, category, api_endpoint, http_method, input_schema, auth_type) VALUES
(
    'resolve_customer',
    'Resolve Customer',
    'Resolve customer details from mobile number',
    'service_booking',
    '/api/customer/resolve',
    'POST',
    '{
        "type": "object",
        "properties": {
            "mobile": {
                "type": "string",
                "description": "Customer mobile number (10 digits)"
            }
        },
        "required": ["mobile"]
    }',
    'api_key'
),
(
    'resolve_vehicle',
    'Resolve Vehicle',
    'Get vehicle details from registration number',
    'service_booking',
    '/api/vehicle/resolve',
    'POST',
    '{
        "type": "object",
        "properties": {
            "registration_number": {
                "type": "string",
                "description": "Vehicle registration number (e.g., MH12AB1234)"
            }
        },
        "required": ["registration_number"]
    }',
    'api_key'
),
(
    'get_nearby_dealers',
    'Get Nearby Dealers',
    'Find dealers near a location',
    'service_booking',
    '/api/dealers/nearby',
    'POST',
    '{
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name"
            },
            "area": {
                "type": "string",
                "description": "Area or locality name"
            },
            "service_type": {
                "type": "string",
                "enum": ["regular", "express", "body_repair"],
                "description": "Type of service required"
            }
        },
        "required": ["city"]
    }',
    'api_key'
),
(
    'get_available_slots',
    'Get Available Slots',
    'Get available appointment slots for a dealer',
    'service_booking',
    '/api/slots/available',
    'POST',
    '{
        "type": "object",
        "properties": {
            "dealer_code": {
                "type": "string",
                "description": "Dealer code"
            },
            "date": {
                "type": "string",
                "format": "date",
                "description": "Date for appointment (YYYY-MM-DD)"
            },
            "service_type": {
                "type": "string",
                "enum": ["regular", "express", "body_repair"],
                "description": "Type of service"
            }
        },
        "required": ["dealer_code", "date"]
    }',
    'api_key'
),
(
    'create_service_booking',
    'Create Service Booking',
    'Create a new service booking appointment',
    'service_booking',
    '/api/booking/create',
    'POST',
    '{
        "type": "object",
        "properties": {
            "customer_mobile": {
                "type": "string",
                "description": "Customer mobile number"
            },
            "vehicle_registration": {
                "type": "string",
                "description": "Vehicle registration number"
            },
            "dealer_code": {
                "type": "string",
                "description": "Selected dealer code"
            },
            "appointment_date": {
                "type": "string",
                "format": "date",
                "description": "Appointment date (YYYY-MM-DD)"
            },
            "appointment_time": {
                "type": "string",
                "description": "Appointment time (HH:MM)"
            },
            "service_type": {
                "type": "string",
                "enum": ["regular", "express", "body_repair"],
                "description": "Type of service"
            },
            "notes": {
                "type": "string",
                "description": "Additional notes or requests"
            }
        },
        "required": ["customer_mobile", "vehicle_registration", "dealer_code", "appointment_date", "appointment_time", "service_type"]
    }',
    'api_key'
),
(
    'get_booking_status',
    'Get Booking Status',
    'Get status of an existing booking',
    'service_booking',
    '/api/booking/{booking_id}',
    'GET',
    '{
        "type": "object",
        "properties": {
            "booking_id": {
                "type": "string",
                "description": "Booking ID to check status"
            }
        },
        "required": ["booking_id"]
    }',
    'api_key'
);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_tools_updated_at
    BEFORE UPDATE ON tools
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bookings_updated_at
    BEFORE UPDATE ON service_bookings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- GRANT PERMISSIONS
-- ============================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO msil_mcp;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO msil_mcp;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'MSIL MCP Database initialized successfully!';
    RAISE NOTICE 'Tables created: tools, service_bookings, tool_executions, chat_sessions, chat_messages, metrics';
    RAISE NOTICE 'Seed data: 6 service booking tools inserted';
END $$;
