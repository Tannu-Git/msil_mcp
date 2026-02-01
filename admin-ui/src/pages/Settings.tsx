import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, Save, RefreshCw, AlertTriangle, CheckCircle, 
  Shield, Database, Zap, Activity, Cloud, Code, Brain, Lock, Server,
  Globe, Key, FileText, Network, Container, TestTube, ChevronRight
} from 'lucide-react';
import { api } from '../lib/api';

// ============================================================================
// Type Definitions
// ============================================================================

interface SettingsData {
  authentication: Record<string, any>;
  policy: Record<string, any>;
  audit: Record<string, any>;
  resilience: Record<string, any>;
  rate_limiting: Record<string, any>;
  batch: Record<string, any>;
  cache: Record<string, any>;
  api_gateway: Record<string, any>;
  database: Record<string, any>;
  llm: Record<string, any>;
  openai: Record<string, any>;
  system: Record<string, any>;
  idempotency?: Record<string, any>;
  pim?: Record<string, any>;
  waf?: Record<string, any>;
  mtls?: Record<string, any>;
  tool_risk?: Record<string, any>;
  container_security?: Record<string, any>;
  security_testing?: Record<string, any>;
  network_policies?: Record<string, any>;
}

// ============================================================================
// Constants - LLM Providers and Models
// ============================================================================

const LLM_PROVIDERS = [
  { id: 'openai', name: 'OpenAI', description: 'GPT models from OpenAI' },
  { id: 'azure_openai', name: 'Azure OpenAI', description: 'OpenAI models via Azure' },
  { id: 'google', name: 'Google AI', description: 'Gemini models from Google' },
  { id: 'anthropic', name: 'Anthropic', description: 'Claude models from Anthropic' },
  { id: 'aws_bedrock', name: 'AWS Bedrock', description: 'Various models via AWS' },
];

const LLM_MODELS: Record<string, { id: string; name: string; context: string }[]> = {
  openai: [
    { id: 'gpt-4-turbo-preview', name: 'GPT-4 Turbo', context: '128K' },
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo (Stable)', context: '128K' },
    { id: 'gpt-4', name: 'GPT-4', context: '8K' },
    { id: 'gpt-4-32k', name: 'GPT-4 32K', context: '32K' },
    { id: 'gpt-4o', name: 'GPT-4o', context: '128K' },
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', context: '128K' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', context: '16K' },
  ],
  azure_openai: [
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', context: '128K' },
    { id: 'gpt-4', name: 'GPT-4', context: '8K' },
    { id: 'gpt-4o', name: 'GPT-4o', context: '128K' },
    { id: 'gpt-35-turbo', name: 'GPT-3.5 Turbo', context: '16K' },
  ],
  google: [
    { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', context: '1M' },
    { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash', context: '1M' },
    { id: 'gemini-1.0-pro', name: 'Gemini 1.0 Pro', context: '32K' },
    { id: 'gemini-pro', name: 'Gemini Pro', context: '32K' },
  ],
  anthropic: [
    { id: 'claude-3-opus', name: 'Claude 3 Opus', context: '200K' },
    { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet', context: '200K' },
    { id: 'claude-3-haiku', name: 'Claude 3 Haiku', context: '200K' },
    { id: 'claude-2.1', name: 'Claude 2.1', context: '100K' },
  ],
  aws_bedrock: [
    { id: 'anthropic.claude-3-sonnet', name: 'Claude 3 Sonnet', context: '200K' },
    { id: 'anthropic.claude-3-haiku', name: 'Claude 3 Haiku', context: '200K' },
    { id: 'amazon.titan-text-express', name: 'Titan Text Express', context: '8K' },
    { id: 'meta.llama3-70b-instruct', name: 'Llama 3 70B', context: '8K' },
  ],
};

const LOG_LEVELS = [
  { id: 'DEBUG', name: 'Debug', description: 'Detailed debugging information', color: 'text-gray-600' },
  { id: 'INFO', name: 'Info', description: 'General operational information', color: 'text-blue-600' },
  { id: 'WARNING', name: 'Warning', description: 'Warning messages for potential issues', color: 'text-yellow-600' },
  { id: 'ERROR', name: 'Error', description: 'Error messages for failures', color: 'text-red-600' },
  { id: 'CRITICAL', name: 'Critical', description: 'Critical failures requiring immediate attention', color: 'text-red-800' },
];

const API_GATEWAY_MODES = [
  { id: 'mock', name: 'Mock Mode', description: 'Use mock API for development/testing' },
  { id: 'msil_apim', name: 'MSIL APIM', description: 'Connect to Maruti Suzuki API Manager' },
];

const TOOL_RISK_LEVELS = [
  { id: 'read', name: 'Read', description: 'Read-only operations' },
  { id: 'write', name: 'Write', description: 'Write/modify operations' },
  { id: 'privileged', name: 'Privileged', description: 'Administrative operations' },
];

const PIM_PROVIDERS = [
  { id: 'local', name: 'Local', description: 'Local elevation management' },
  { id: 'azure_pim', name: 'Azure PIM', description: 'Azure Privileged Identity Management' },
  { id: 'cyberark', name: 'CyberArk', description: 'CyberArk PAM' },
  { id: 'okta', name: 'Okta', description: 'Okta Advanced Server Access' },
];

const MTLS_VERIFY_MODES = [
  { id: 'CERT_REQUIRED', name: 'Certificate Required', description: 'Client must present a valid certificate' },
  { id: 'CERT_OPTIONAL', name: 'Certificate Optional', description: 'Client certificate is optional' },
  { id: 'CERT_NONE', name: 'No Verification', description: 'No client certificate verification' },
];

const S3_OBJECT_LOCK_MODES = [
  { id: 'GOVERNANCE', name: 'Governance', description: 'Admins can delete with special permissions' },
  { id: 'COMPLIANCE', name: 'Compliance', description: 'No one can delete until retention expires' },
];

// ============================================================================
// Tab Configuration
// ============================================================================

type TabId = 'general' | 'security' | 'llm' | 'api' | 'performance' | 'advanced';

const TABS: { id: TabId; label: string; icon: React.ReactNode; description: string }[] = [
  { id: 'general', label: 'General', icon: <SettingsIcon className="w-5 h-5" />, description: 'System and logging settings' },
  { id: 'security', label: 'Security', icon: <Shield className="w-5 h-5" />, description: 'Authentication, authorization, and compliance' },
  { id: 'llm', label: 'LLM / AI', icon: <Brain className="w-5 h-5" />, description: 'Language model configuration' },
  { id: 'api', label: 'API Gateway', icon: <Globe className="w-5 h-5" />, description: 'API gateway and backend integration' },
  { id: 'performance', label: 'Performance', icon: <Zap className="w-5 h-5" />, description: 'Caching, rate limiting, and resilience' },
  { id: 'advanced', label: 'Advanced', icon: <Server className="w-5 h-5" />, description: 'Database, container, and network settings' },
];

// ============================================================================
// Main Component
// ============================================================================

export default function Settings() {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [editedValues, setEditedValues] = useState<Record<string, any>>({});
  const [activeTab, setActiveTab] = useState<TabId>('general');
  const [selectedLLMProvider, setSelectedLLMProvider] = useState<string>('openai');

  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    // Infer LLM provider from model name
    const model = settings?.openai?.openai_model || settings?.llm?.openai_model;
    if (model) {
      if (model.startsWith('gemini')) setSelectedLLMProvider('google');
      else if (model.startsWith('claude')) setSelectedLLMProvider('anthropic');
      else if (model.startsWith('anthropic.') || model.startsWith('amazon.') || model.startsWith('meta.')) setSelectedLLMProvider('aws_bedrock');
      else setSelectedLLMProvider('openai');
    }
  }, [settings?.openai?.openai_model, settings?.llm?.openai_model]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await api.get('/admin/settings');
      // Map openai to llm for better UX
      if (data.openai) {
        data.llm = data.openai;
      }
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

    // Map llm back to openai for API
    const apiCategory = category === 'llm' ? 'openai' : category;

    try {
      setSaving(true);
      await api.put(`/admin/settings/${apiCategory}/${key}`, { value });
      
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

  const getValue = (category: string, key: string, defaultValue: any = '') => {
    const fullKey = `${category}.${key}`;
    if (editedValues[fullKey] !== undefined) return editedValues[fullKey];
    const catData = settings?.[category as keyof SettingsData];
    return catData?.[key] ?? defaultValue;
  };

  const hasChanges = (category: string, key: string) => {
    return editedValues[`${category}.${key}`] !== undefined;
  };

  // ============================================================================
  // Render Helpers
  // ============================================================================

  const renderSaveButton = (category: string, key: string) => {
    if (!hasChanges(category, key)) return null;
    return (
      <button
        onClick={() => handleSave(category, key)}
        disabled={saving}
        className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5 transition-colors"
      >
        <Save className="w-3.5 h-3.5" />
        Save
      </button>
    );
  };

  const renderToggle = (category: string, key: string, label: string, description?: string) => (
    <div className="flex items-center justify-between py-4 border-b border-gray-100 last:border-0">
      <div className="flex-1">
        <label className="text-sm font-medium text-gray-900">{label}</label>
        {description && <p className="text-xs text-gray-500 mt-0.5">{description}</p>}
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={() => handleChange(category, key, !getValue(category, key, false))}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            getValue(category, key, false) ? 'bg-blue-600' : 'bg-gray-300'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm ${
              getValue(category, key, false) ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
        {renderSaveButton(category, key)}
      </div>
    </div>
  );

  const renderNumberInput = (category: string, key: string, label: string, description?: string, suffix?: string) => (
    <div className="flex items-center justify-between py-4 border-b border-gray-100 last:border-0">
      <div className="flex-1">
        <label className="text-sm font-medium text-gray-900">{label}</label>
        {description && <p className="text-xs text-gray-500 mt-0.5">{description}</p>}
      </div>
      <div className="flex items-center gap-3">
        <div className="relative">
          <input
            type="number"
            value={getValue(category, key, 0)}
            onChange={(e) => handleChange(category, key, parseInt(e.target.value) || 0)}
            className="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
          {suffix && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">{suffix}</span>
          )}
        </div>
        {renderSaveButton(category, key)}
      </div>
    </div>
  );

  const renderTextInput = (category: string, key: string, label: string, description?: string, readonly?: boolean, type: string = 'text') => (
    <div className="flex items-center justify-between py-4 border-b border-gray-100 last:border-0">
      <div className="flex-1 mr-4">
        <label className="text-sm font-medium text-gray-900">{label}</label>
        {description && <p className="text-xs text-gray-500 mt-0.5">{description}</p>}
      </div>
      <div className="flex items-center gap-3">
        <input
          type={type}
          value={getValue(category, key, '')}
          onChange={(e) => handleChange(category, key, e.target.value)}
          disabled={readonly}
          className={`w-80 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm ${
            readonly ? 'bg-gray-100 text-gray-500' : ''
          }`}
        />
        {!readonly && renderSaveButton(category, key)}
      </div>
    </div>
  );

  const renderDropdown = (
    category: string, 
    key: string, 
    label: string, 
    options: { id: string; name: string; description?: string }[],
    description?: string
  ) => (
    <div className="flex items-center justify-between py-4 border-b border-gray-100 last:border-0">
      <div className="flex-1">
        <label className="text-sm font-medium text-gray-900">{label}</label>
        {description && <p className="text-xs text-gray-500 mt-0.5">{description}</p>}
      </div>
      <div className="flex items-center gap-3">
        <select
          value={getValue(category, key, '')}
          onChange={(e) => handleChange(category, key, e.target.value)}
          className="w-64 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white"
        >
          {options.map(opt => (
            <option key={opt.id} value={opt.id}>{opt.name}</option>
          ))}
        </select>
        {renderSaveButton(category, key)}
      </div>
    </div>
  );

  const renderSection = (title: string, icon: React.ReactNode, children: React.ReactNode) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mb-6">
      <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-white border-b border-gray-200 flex items-center gap-3">
        <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
          {icon}
        </div>
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="px-6 py-2">
        {children}
      </div>
    </div>
  );

  // ============================================================================
  // Tab Content Renderers
  // ============================================================================

  const renderGeneralTab = () => (
    <>
      {renderSection('System Information', <Server className="w-5 h-5" />, (
        <>
          {renderTextInput('system', 'app_name', 'Application Name', 'Name of this MCP server instance', true)}
          {renderTextInput('system', 'app_version', 'Version', 'Current application version', true)}
          {renderToggle('system', 'debug', 'Debug Mode', 'Enable detailed debugging and development features')}
          {renderDropdown('system', 'log_level', 'Log Level', LOG_LEVELS, 'Minimum severity level for log messages')}
        </>
      ))}
    </>
  );

  const renderSecurityTab = () => (
    <>
      {renderSection('Authentication', <Key className="w-5 h-5" />, (
        <>
          {renderToggle('authentication', 'oauth2_enabled', 'OAuth2 Authentication', 'Enable OAuth2/JWT based authentication')}
          {renderTextInput('authentication', 'jwt_algorithm', 'JWT Algorithm', 'Algorithm used for signing tokens', true)}
          {renderNumberInput('authentication', 'jwt_access_token_expire_minutes', 'Access Token Expiry', 'How long access tokens are valid', 'min')}
          {renderNumberInput('authentication', 'jwt_refresh_token_expire_days', 'Refresh Token Expiry', 'How long refresh tokens are valid', 'days')}
        </>
      ))}

      {renderSection('OpenID Connect (OIDC)', <Globe className="w-5 h-5" />, (
        <>
          {renderToggle('authentication', 'oidc_enabled', 'OIDC Enabled', 'Enable OpenID Connect for enterprise SSO')}
          {renderTextInput('authentication', 'oidc_issuer', 'Issuer URL', 'Identity Provider issuer URL')}
          {renderTextInput('authentication', 'oidc_audience', 'Audience', 'Expected audience (client ID)')}
          {renderTextInput('authentication', 'oidc_jwks_url', 'JWKS URL', 'JSON Web Key Set endpoint URL')}
          {renderTextInput('authentication', 'oidc_required_scopes', 'Required Scopes', 'Comma-separated list of required scopes')}
        </>
      ))}

      {renderSection('Policy Engine (OPA)', <Shield className="w-5 h-5" />, (
        <>
          {renderToggle('policy', 'opa_enabled', 'OPA Enabled', 'Enable Open Policy Agent for RBAC decisions')}
          {renderTextInput('policy', 'opa_url', 'OPA Server URL', 'URL of the OPA server')}
        </>
      ))}

      {renderSection('Audit & Compliance', <FileText className="w-5 h-5" />, (
        <>
          {renderToggle('audit', 'audit_enabled', 'Audit Logging', 'Enable audit logging for all operations')}
          {renderNumberInput('audit', 'audit_retention_days', 'Retention Period', 'How long to retain audit logs', 'days')}
          {renderToggle('audit', 'audit_s3_enabled', 'S3 WORM Storage', 'Store immutable audit logs in S3')}
          {renderTextInput('audit', 'audit_s3_bucket', 'S3 Bucket', 'S3 bucket name for audit logs')}
          {renderDropdown('audit', 'audit_s3_object_lock_mode', 'Object Lock Mode', S3_OBJECT_LOCK_MODES, 'S3 Object Lock retention mode')}
          {renderToggle('audit', 'audit_dual_write', 'Dual Write', 'Write logs to both database and S3')}
        </>
      ))}

      {settings?.pim && renderSection('Privileged Access Management', <Lock className="w-5 h-5" />, (
        <>
          {renderToggle('pim', 'pim_enabled', 'PIM/PAM Enabled', 'Enable Just-in-Time privileged access')}
          {renderDropdown('pim', 'pim_provider', 'PIM Provider', PIM_PROVIDERS, 'Privileged identity management system')}
          {renderTextInput('pim', 'pam_endpoint', 'PAM Endpoint', 'External PAM system API endpoint')}
          {renderNumberInput('pim', 'elevation_duration_seconds', 'Elevation Duration', 'How long elevated access lasts', 'sec')}
          {renderToggle('pim', 'elevation_require_approval', 'Require Approval', 'Require manager approval for elevation')}
        </>
      ))}

      {settings?.waf && renderSection('Web Application Firewall', <Shield className="w-5 h-5" />, (
        <>
          {renderToggle('waf', 'waf_enabled', 'WAF Enabled', 'Enable AWS WAF protection')}
          {renderNumberInput('waf', 'waf_rate_limit', 'Rate Limit', 'Max requests per 5 minutes per IP', 'req')}
          {renderToggle('waf', 'waf_ip_allowlist_enabled', 'IP Allowlist', 'Enable IP allowlist filtering')}
          {renderTextInput('waf', 'waf_allowed_ips', 'Allowed IPs', 'Comma-separated CIDR blocks')}
        </>
      ))}

      {settings?.mtls && renderSection('Mutual TLS (mTLS)', <Lock className="w-5 h-5" />, (
        <>
          {renderToggle('mtls', 'mtls_enabled', 'mTLS Enabled', 'Enable mutual TLS for service communication')}
          {renderDropdown('mtls', 'mtls_verify_mode', 'Verify Mode', MTLS_VERIFY_MODES, 'Client certificate verification mode')}
          {renderTextInput('mtls', 'mtls_ca_cert_path', 'CA Certificate Path', 'Path to CA certificate file')}
          {renderTextInput('mtls', 'mtls_client_cert_path', 'Client Certificate Path', 'Path to client certificate file')}
          {renderTextInput('mtls', 'mtls_client_key_path', 'Client Key Path', 'Path to client private key file')}
        </>
      ))}

      {settings?.tool_risk && renderSection('Tool Risk Management', <Shield className="w-5 h-5" />, (
        <>
          {renderToggle('tool_risk', 'tool_risk_enforcement_enabled', 'Risk Enforcement', 'Enforce risk-based access control')}
          {renderDropdown('tool_risk', 'tool_risk_default_level', 'Default Risk Level', TOOL_RISK_LEVELS, 'Default risk level for new tools')}
        </>
      ))}
    </>
  );

  const renderLLMTab = () => (
    <>
      {renderSection('LLM Provider Configuration', <Brain className="w-5 h-5" />, (
        <>
          <div className="py-4 border-b border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <div>
                <label className="text-sm font-medium text-gray-900">LLM Provider</label>
                <p className="text-xs text-gray-500 mt-0.5">Select your Language Model provider</p>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {LLM_PROVIDERS.map(provider => (
                <button
                  key={provider.id}
                  onClick={() => setSelectedLLMProvider(provider.id)}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    selectedLLMProvider === provider.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="font-medium text-gray-900">{provider.name}</div>
                  <div className="text-xs text-gray-500 mt-1">{provider.description}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="py-4 border-b border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <div>
                <label className="text-sm font-medium text-gray-900">Model</label>
                <p className="text-xs text-gray-500 mt-0.5">Select the specific model to use</p>
              </div>
              {renderSaveButton('llm', 'openai_model')}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {LLM_MODELS[selectedLLMProvider]?.map(model => (
                <button
                  key={model.id}
                  onClick={() => handleChange('llm', 'openai_model', model.id)}
                  className={`p-3 rounded-lg border text-left transition-all flex items-center justify-between ${
                    getValue('llm', 'openai_model', '') === model.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div>
                    <div className="font-medium text-gray-900 text-sm">{model.name}</div>
                    <div className="text-xs text-gray-500">{model.id}</div>
                  </div>
                  <span className="px-2 py-0.5 bg-gray-100 rounded text-xs font-medium text-gray-600">
                    {model.context}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {renderNumberInput('llm', 'openai_max_tokens', 'Max Tokens', 'Maximum tokens per request/response', 'tokens')}
          {renderTextInput('llm', 'openai_api_key', 'API Key', 'API key for the selected provider (stored securely)', false, 'password')}
        </>
      ))}
    </>
  );

  const renderAPITab = () => (
    <>
      {renderSection('API Gateway Mode', <Cloud className="w-5 h-5" />, (
        <>
          <div className="py-4 border-b border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <div>
                <label className="text-sm font-medium text-gray-900">Gateway Mode</label>
                <p className="text-xs text-gray-500 mt-0.5">Select how the MCP server connects to backend APIs</p>
              </div>
              {renderSaveButton('api_gateway', 'api_gateway_mode')}
            </div>
            <div className="grid grid-cols-2 gap-3">
              {API_GATEWAY_MODES.map(mode => (
                <button
                  key={mode.id}
                  onClick={() => handleChange('api_gateway', 'api_gateway_mode', mode.id)}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    getValue('api_gateway', 'api_gateway_mode', 'mock') === mode.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="font-medium text-gray-900">{mode.name}</div>
                  <div className="text-xs text-gray-500 mt-1">{mode.description}</div>
                </button>
              ))}
            </div>
          </div>
          {renderTextInput('api_gateway', 'mock_api_base_url', 'Mock API URL', 'Base URL for mock API (development)')}
          {renderTextInput('api_gateway', 'msil_apim_base_url', 'MSIL APIM URL', 'Base URL for production APIM')}
        </>
      ))}

      {renderSection('APIM MCP Subscription', <Key className="w-5 h-5" />, (
        <>
          {renderTextInput('api_gateway', 'apim_mcp_subscription_name', 'Subscription Name', 'Name of the MCP subscription in APIM')}
          {renderTextInput('api_gateway', 'apim_mcp_subscription_key', 'Subscription Key', 'Dedicated API key for MCP channel', false, 'password')}
          {renderToggle('api_gateway', 'apim_propagate_user_context', 'Propagate User Context', 'Send user identity to APIM for tracking')}
        </>
      ))}

      {settings?.idempotency && renderSection('Idempotency Protection', <Shield className="w-5 h-5" />, (
        <>
          {renderToggle('idempotency', 'idempotency_enabled', 'Idempotency Enabled', 'Enable idempotency key protection')}
          {renderToggle('idempotency', 'idempotency_required', 'Require Explicit Keys', 'Require clients to provide Idempotency-Key header')}
          {renderNumberInput('idempotency', 'idempotency_ttl_seconds', 'Cache TTL', 'How long to cache idempotent responses', 'sec')}
        </>
      ))}
    </>
  );

  const renderPerformanceTab = () => (
    <>
      {renderSection('Redis Cache', <Database className="w-5 h-5" />, (
        <>
          {renderToggle('cache', 'redis_enabled', 'Redis Caching', 'Enable Redis for caching and session storage')}
          {renderTextInput('cache', 'redis_url', 'Redis URL', 'Redis connection string')}
          {renderNumberInput('cache', 'cache_ttl', 'Default TTL', 'Default cache time-to-live', 'sec')}
        </>
      ))}

      {renderSection('Rate Limiting', <Activity className="w-5 h-5" />, (
        <>
          {renderToggle('rate_limiting', 'rate_limit_enabled', 'Rate Limiting', 'Enable API request rate limiting')}
          {renderNumberInput('rate_limiting', 'rate_limit_per_user', 'Per User Limit', 'Maximum requests per user per minute', 'req/min')}
          {renderNumberInput('rate_limiting', 'rate_limit_per_tool', 'Per Tool Limit', 'Maximum requests per tool per minute', 'req/min')}
        </>
      ))}

      {renderSection('Resilience', <Zap className="w-5 h-5" />, (
        <>
          {renderNumberInput('resilience', 'circuit_breaker_failure_threshold', 'Circuit Breaker Threshold', 'Failures before circuit opens', 'failures')}
          {renderNumberInput('resilience', 'circuit_breaker_recovery_timeout', 'Recovery Timeout', 'Time before circuit attempts to close', 'sec')}
          {renderNumberInput('resilience', 'retry_max_attempts', 'Max Retry Attempts', 'Maximum retry attempts for failed requests', 'attempts')}
          {renderNumberInput('resilience', 'retry_exponential_base', 'Retry Base', 'Exponential backoff base (2 → 2s, 4s, 8s)', 'sec')}
        </>
      ))}

      {renderSection('Batch Execution', <Code className="w-5 h-5" />, (
        <>
          {renderNumberInput('batch', 'batch_max_concurrency', 'Max Concurrency', 'Maximum parallel tool executions', 'parallel')}
          {renderNumberInput('batch', 'batch_max_size', 'Max Batch Size', 'Maximum tools per batch request', 'tools')}
        </>
      ))}
    </>
  );

  const renderAdvancedTab = () => (
    <>
      {renderSection('Database', <Database className="w-5 h-5" />, (
        <>
          {renderTextInput('database', 'database_url', 'Database URL', 'PostgreSQL connection string', true)}
          {renderNumberInput('database', 'database_pool_size', 'Pool Size', 'Database connection pool size', 'connections')}
          {renderNumberInput('database', 'database_max_overflow', 'Max Overflow', 'Additional connections when pool is exhausted', 'connections')}
        </>
      ))}

      {settings?.container_security && renderSection('Container Security', <Container className="w-5 h-5" />, (
        <>
          {renderToggle('container_security', 'container_hardening_enabled', 'Container Hardening', 'Enable container security hardening')}
          {renderToggle('container_security', 'container_readonly_root', 'Read-Only Root FS', 'Use read-only root filesystem')}
          {renderToggle('container_security', 'container_drop_all_caps', 'Drop All Capabilities', 'Drop all Linux capabilities')}
          {renderToggle('container_security', 'container_no_new_privileges', 'No New Privileges', 'Prevent privilege escalation')}
        </>
      ))}

      {settings?.security_testing && renderSection('Security Testing', <TestTube className="w-5 h-5" />, (
        <>
          {renderToggle('security_testing', 'security_tests_enabled', 'Security Tests', 'Enable automated security testing')}
          {renderToggle('security_testing', 'security_scan_on_startup', 'Scan on Startup', 'Run security scan when application starts')}
          {renderTextInput('security_testing', 'security_scan_schedule', 'Scan Schedule', 'Cron schedule for security scans')}
        </>
      ))}

      {settings?.network_policies && renderSection('Network Policies', <Network className="w-5 h-5" />, (
        <>
          {renderToggle('network_policies', 'network_policies_enabled', 'Network Policies', 'Enable Kubernetes network policies')}
          {renderToggle('network_policies', 'network_deny_by_default', 'Deny by Default', 'Block all traffic by default')}
          {renderTextInput('network_policies', 'network_allowed_namespaces', 'Allowed Namespaces', 'Comma-separated allowed K8s namespaces')}
        </>
      ))}
    </>
  );

  // ============================================================================
  // Main Render
  // ============================================================================

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-xl">
              <SettingsIcon className="w-7 h-7 text-blue-600" />
            </div>
            System Settings
          </h1>
          <p className="text-gray-600 mt-1 ml-14">Configure all aspects of the MCP server</p>
        </div>
        <button
          onClick={loadSettings}
          disabled={loading}
          className="px-4 py-2.5 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors flex items-center gap-2 font-medium"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Reload
        </button>
      </div>

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-xl flex items-center gap-3 ${
          message.type === 'success' 
            ? 'bg-green-50 text-green-800 border border-green-200' 
            : 'bg-red-50 text-red-800 border border-red-200'
        }`}>
          {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
          <span className="font-medium">{message.text}</span>
        </div>
      )}

      {/* Warning Banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-amber-900">Runtime Configuration</h4>
            <p className="text-sm text-amber-800 mt-0.5">
              Changes update runtime values only. For persistent changes, update <code className="bg-amber-100 px-1.5 py-0.5 rounded font-mono text-xs">.env</code> and restart.
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="border-b border-gray-200 bg-gray-50">
          <div className="flex overflow-x-auto">
            {TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 bg-white'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6">
          {/* Tab description */}
          <div className="mb-6 flex items-center gap-2 text-gray-600">
            <ChevronRight className="w-4 h-4" />
            <span className="text-sm">{TABS.find(t => t.id === activeTab)?.description}</span>
          </div>

          {/* Tab content */}
          {activeTab === 'general' && renderGeneralTab()}
          {activeTab === 'security' && renderSecurityTab()}
          {activeTab === 'llm' && renderLLMTab()}
          {activeTab === 'api' && renderAPITab()}
          {activeTab === 'performance' && renderPerformanceTab()}
          {activeTab === 'advanced' && renderAdvancedTab()}
        </div>
      </div>
    </div>
  );
}
