import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, RefreshCw, AlertTriangle, CheckCircle, Shield, Database, Zap, Activity, Cloud, Code } from 'lucide-react';
import { api } from '../lib/api';

interface SettingsData {
  authentication: {
    oauth2_enabled: boolean;
    jwt_algorithm: string;
    jwt_access_token_expire_minutes: number;
    jwt_refresh_token_expire_days: number;
  };
  policy: {
    opa_enabled: boolean;
    opa_url: string;
  };
  audit: {
    audit_enabled: boolean;
    audit_s3_bucket: string | null;
    audit_retention_days: number;
  };
  resilience: {
    circuit_breaker_failure_threshold: number;
    circuit_breaker_recovery_timeout: number;
    retry_max_attempts: number;
    retry_exponential_base: number;
  };
  rate_limiting: {
    rate_limit_enabled: boolean;
    rate_limit_per_user: number;
    rate_limit_per_tool: number;
  };
  batch: {
    batch_max_concurrency: number;
    batch_max_size: number;
  };
  cache: {
    redis_enabled: boolean;
    redis_url: string;
    cache_ttl: number;
  };
  api_gateway: {
    api_gateway_mode: string;
    mock_api_base_url: string;
    msil_apim_base_url: string;
  };
  database: {
    database_url: string;
    database_pool_size: number;
    database_max_overflow: number;
  };
  openai: {
    openai_model: string;
    openai_max_tokens: number;
  };
  system: {
    app_name: string;
    app_version: string;
    debug: boolean;
    log_level: string;
  };
}

export default function Settings() {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [editedValues, setEditedValues] = useState<Record<string, any>>({});

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await api.get('/admin/settings');
      setSettings(data);
      setEditedValues({});
    } catch (error) {
      console.error('Failed to load settings:', error);
      setMessage({ type: 'error', text: 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (category: string, key: string, value: any) => {
    const fullKey = `${category}.${key}`;
    setEditedValues(prev => ({ ...prev, [fullKey]: value }));
  };

  const handleSave = async (category: string, key: string) => {
    const fullKey = `${category}.${key}`;
    const value = editedValues[fullKey];

    if (value === undefined) return;

    try {
      setSaving(true);
      await api.put(`/admin/settings/${category}/${key}`, { value });
      
      // Update local state
      setSettings(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          [category]: {
            ...prev[category as keyof SettingsData],
            [key]: value
          }
        };
      });

      // Clear edited value
      setEditedValues(prev => {
        const newValues = { ...prev };
        delete newValues[fullKey];
        return newValues;
      });

      setMessage({ type: 'success', text: `Setting updated successfully` });
      setTimeout(() => setMessage(null), 3000);
    } catch (error: any) {
      console.error('Failed to save setting:', error);
      setMessage({ type: 'error', text: error.message || 'Failed to save setting' });
    } finally {
      setSaving(false);
    }
  };

  const renderInput = (category: string, key: string, value: any, type: string = 'text') => {
    const fullKey = `${category}.${key}`;
    const currentValue = editedValues[fullKey] !== undefined ? editedValues[fullKey] : value;
    const hasChanges = editedValues[fullKey] !== undefined;

    if (typeof value === 'boolean') {
      return (
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={currentValue}
              onChange={(e) => handleChange(category, key, e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">{currentValue ? 'Enabled' : 'Disabled'}</span>
          </label>
          {hasChanges && (
            <button
              onClick={() => handleSave(category, key)}
              disabled={saving}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
            >
              <Save className="w-3 h-3" />
              Save
            </button>
          )}
        </div>
      );
    }

    if (typeof value === 'number') {
      return (
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={currentValue}
            onChange={(e) => handleChange(category, key, parseInt(e.target.value) || 0)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {hasChanges && (
            <button
              onClick={() => handleSave(category, key)}
              disabled={saving}
              className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
            >
              <Save className="w-4 h-4" />
              Save
            </button>
          )}
        </div>
      );
    }

    return (
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={currentValue || ''}
          onChange={(e) => handleChange(category, key, e.target.value)}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        {hasChanges && (
          <button
            onClick={() => handleSave(category, key)}
            disabled={saving}
            className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
          >
            <Save className="w-4 h-4" />
            Save
          </button>
        )}
      </div>
    );
  };

  const renderSettingRow = (category: string, key: string, value: any, label: string, description?: string, readonly: boolean = false) => {
    return (
      <div className="py-4 border-b border-gray-200 last:border-0">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-900 mb-1">
              {label}
            </label>
            {description && (
              <p className="text-xs text-gray-500 mb-2">{description}</p>
            )}
          </div>
          <div className="w-96">
            {readonly ? (
              <input
                type="text"
                value={value || 'N/A'}
                disabled
                className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-lg text-gray-600"
              />
            ) : (
              renderInput(category, key, value)
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderCategory = (title: string, icon: React.ReactNode, category: keyof SettingsData, description: string) => {
    if (!settings) return null;

    const categorySettings = settings[category];
    
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center gap-3 mb-4 pb-4 border-b border-gray-200">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            {icon}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <p className="text-sm text-gray-600">{description}</p>
          </div>
        </div>

        <div className="space-y-0">
          {Object.entries(categorySettings).map(([key, value]) => {
            const labels: Record<string, { label: string; description?: string; readonly?: boolean }> = {
              // Authentication
              oauth2_enabled: { label: 'OAuth2 Enabled', description: 'Enable OAuth2/JWT authentication' },
              jwt_algorithm: { label: 'JWT Algorithm', description: 'Algorithm for JWT signing (HS256)', readonly: true },
              jwt_access_token_expire_minutes: { label: 'Access Token Expiry (minutes)', description: 'Access token validity duration' },
              jwt_refresh_token_expire_days: { label: 'Refresh Token Expiry (days)', description: 'Refresh token validity duration' },
              
              // Policy
              opa_enabled: { label: 'OPA Enabled', description: 'Enable Open Policy Agent for RBAC' },
              opa_url: { label: 'OPA URL', description: 'Open Policy Agent server URL' },
              
              // Audit
              audit_enabled: { label: 'Audit Enabled', description: 'Enable audit logging for compliance' },
              audit_s3_bucket: { label: 'S3 Bucket', description: 'S3 bucket for audit log storage' },
              audit_retention_days: { label: 'Retention Days', description: 'How long to keep audit logs (365 days = 12 months)' },
              
              // Resilience
              circuit_breaker_failure_threshold: { label: 'Circuit Breaker Threshold', description: 'Failures before circuit opens' },
              circuit_breaker_recovery_timeout: { label: 'Recovery Timeout (seconds)', description: 'Time before circuit attempts to close' },
              retry_max_attempts: { label: 'Max Retry Attempts', description: 'Maximum retry attempts for failed requests' },
              retry_exponential_base: { label: 'Retry Base (seconds)', description: 'Base for exponential backoff (2s, 4s, 8s)' },
              
              // Rate Limiting
              rate_limit_enabled: { label: 'Rate Limiting Enabled', description: 'Enable API rate limiting' },
              rate_limit_per_user: { label: 'User Limit (req/min)', description: 'Requests per minute per user' },
              rate_limit_per_tool: { label: 'Tool Limit (req/min)', description: 'Requests per minute per tool' },
              
              // Batch
              batch_max_concurrency: { label: 'Max Concurrency', description: 'Max parallel tool executions in batch' },
              batch_max_size: { label: 'Max Batch Size', description: 'Maximum tools per batch request' },
              
              // Cache
              redis_enabled: { label: 'Redis Enabled', description: 'Enable Redis caching' },
              redis_url: { label: 'Redis URL', description: 'Redis connection string' },
              cache_ttl: { label: 'Cache TTL (seconds)', description: 'Default cache time-to-live' },
              
              // API Gateway
              api_gateway_mode: { label: 'Gateway Mode', description: 'API gateway mode (mock or msil_apim)' },
              mock_api_base_url: { label: 'Mock API URL', description: 'Mock API base URL for testing' },
              msil_apim_base_url: { label: 'MSIL APIM URL', description: 'Production APIM base URL' },
              
              // Database
              database_url: { label: 'Database URL', description: 'PostgreSQL connection string', readonly: true },
              database_pool_size: { label: 'Pool Size', description: 'Database connection pool size' },
              database_max_overflow: { label: 'Max Overflow', description: 'Max overflow connections' },
              
              // OpenAI
              openai_model: { label: 'Model', description: 'OpenAI model to use' },
              openai_max_tokens: { label: 'Max Tokens', description: 'Maximum tokens per request' },
              
              // System
              app_name: { label: 'App Name', description: 'Application name', readonly: true },
              app_version: { label: 'Version', description: 'Application version', readonly: true },
              debug: { label: 'Debug Mode', description: 'Enable debug logging and features' },
              log_level: { label: 'Log Level', description: 'Logging level (DEBUG, INFO, WARNING, ERROR)' },
            };

            const config = labels[key] || { label: key, readonly: false };
            return renderSettingRow(
              category,
              key,
              value,
              config.label,
              config.description,
              config.readonly
            );
          })}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <SettingsIcon className="w-8 h-8 text-blue-600" />
            System Settings
          </h1>
          <p className="text-gray-600 mt-1">Configure all aspects of the MCP server</p>
        </div>
        <button
          onClick={loadSettings}
          disabled={loading}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Reload
        </button>
      </div>

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'
        }`}>
          {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
          {message.text}
        </div>
      )}

      {/* Warning */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-yellow-900 mb-1">Runtime Configuration</h4>
            <p className="text-sm text-yellow-800">
              Changes made here update runtime values only. For persistent changes, update the <code className="bg-yellow-100 px-1 py-0.5 rounded">.env</code> file 
              or environment variables and restart the server.
            </p>
          </div>
        </div>
      </div>

      {/* Settings Categories */}
      {renderCategory('Authentication & Security', <Shield className="w-6 h-6 text-blue-600" />, 'authentication', 'OAuth2, JWT, and authentication settings')}
      {renderCategory('Policy Engine', <Shield className="w-6 h-6 text-purple-600" />, 'policy', 'Open Policy Agent and RBAC configuration')}
      {renderCategory('Audit & Compliance', <Activity className="w-6 h-6 text-green-600" />, 'audit', 'Audit logging and compliance settings')}
      {renderCategory('Resilience', <Zap className="w-6 h-6 text-orange-600" />, 'resilience', 'Circuit breaker and retry configuration')}
      {renderCategory('Rate Limiting', <Activity className="w-6 h-6 text-red-600" />, 'rate_limiting', 'API rate limiting configuration')}
      {renderCategory('Batch Execution', <Code className="w-6 h-6 text-indigo-600" />, 'batch', 'Batch tool execution settings')}
      {renderCategory('Cache & Redis', <Database className="w-6 h-6 text-teal-600" />, 'cache', 'Redis caching configuration')}
      {renderCategory('API Gateway', <Cloud className="w-6 h-6 text-blue-600" />, 'api_gateway', 'API gateway and backend configuration')}
      {renderCategory('Database', <Database className="w-6 h-6 text-gray-600" />, 'database', 'PostgreSQL database settings')}
      {renderCategory('OpenAI', <Code className="w-6 h-6 text-green-600" />, 'openai', 'OpenAI API configuration')}
      {renderCategory('System', <SettingsIcon className="w-6 h-6 text-gray-600" />, 'system', 'System-level configuration')}
    </div>
  );
}
