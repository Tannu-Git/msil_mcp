-- Migration: Create audit_logs table for compliance
-- Version: 003
-- Date: 2026-01-31
-- Description: Audit trail with 12-month retention requirement

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id VARCHAR(100) NOT NULL UNIQUE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    correlation_id VARCHAR(100),
    user_id VARCHAR(100),
    tool_name VARCHAR(100),
    action VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    latency_ms DECIMAL(10, 2),
    request_size INTEGER,
    response_size INTEGER,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_tool ON audit_logs(tool_name);
CREATE INDEX idx_audit_status ON audit_logs(status);
CREATE INDEX idx_audit_correlation ON audit_logs(correlation_id);

-- Composite index for common query patterns
CREATE INDEX idx_audit_type_status ON audit_logs(event_type, status);
CREATE INDEX idx_audit_tool_timestamp ON audit_logs(tool_name, timestamp DESC);

-- Comments for documentation
COMMENT ON TABLE audit_logs IS 'Audit trail for compliance with 12-month retention';
COMMENT ON COLUMN audit_logs.event_type IS 'Type: tool_call, policy_decision, auth_event, config_change';
COMMENT ON COLUMN audit_logs.status IS 'Status: success, failure, denied, allowed';
COMMENT ON COLUMN audit_logs.metadata IS 'JSON metadata with PII masked';
