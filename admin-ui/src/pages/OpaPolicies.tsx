import { useState, useEffect } from 'react';
import { Shield, Save, AlertCircle, Play, CheckCircle } from 'lucide-react';
import Editor from '@monaco-editor/react';
import { getApiUrl } from '@/lib/config';

export default function OpaPolicies() {
  const [policyContent, setPolicyContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Test input state
  const [testUser, setTestUser] = useState('testuser@msil.com');
  const [testAction, setTestAction] = useState('invoke');
  const [testResource, setTestResource] = useState('get_vehicle_booking');

  useEffect(() => {
    loadPolicy();
  }, []);

  const loadPolicy = async () => {
    try {
      const response = await fetch(getApiUrl('/api/admin/opa/policies/authz'), {
        headers: {
          'x-api-key': 'msil-mcp-dev-key-2026',
          'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'mock-jwt-token')
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPolicyContent(data.content || '');
      }
    } catch (error) {
      console.error('Failed to load policy:', error);
    } finally {
      setLoading(false);
    }
  };

  const savePolicy = async () => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      const response = await fetch(getApiUrl('/api/admin/opa/policies/authz'), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': 'msil-mcp-dev-key-2026',
          'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'mock-jwt-token')
        },
        body: JSON.stringify({ content: policyContent })
      });

      if (response.ok) {
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      } else {
        const error = await response.json();
        alert(`Failed to save policy: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to save policy:', error);
      alert('Failed to save policy');
    } finally {
      setSaving(false);
    }
  };

  const testPolicy = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const response = await fetch(getApiUrl('/api/admin/opa/policies/test'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': 'msil-mcp-dev-key-2026',
          'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'mock-jwt-token')
        },
        body: JSON.stringify({
          user: testUser,
          action: testAction,
          resource: testResource
        })
      });

      if (response.ok) {
        const data = await response.json();
        setTestResult(data);
      } else {
        const error = await response.json();
        setTestResult({
          allowed: false,
          error: error.detail || 'Test failed'
        });
      }
    } catch (error) {
      console.error('Failed to test policy:', error);
      setTestResult({
        allowed: false,
        error: 'Test request failed'
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="w-8 h-8 text-blue-600" />
            OPA Policy Editor
          </h1>
          <p className="text-gray-600 mt-1">Edit Rego authorization policies</p>
        </div>
        <div className="flex items-center gap-3">
          {saveSuccess && (
            <div className="flex items-center gap-2 text-green-600 bg-green-50 px-4 py-2 rounded-lg">
              <CheckCircle className="w-5 h-5" />
              <span className="text-sm font-medium">Saved successfully</span>
            </div>
          )}
          <button
            onClick={savePolicy}
            disabled={saving || loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Policy'}
          </button>
        </div>
      </div>

      {/* Warning */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="font-semibold text-amber-900 mb-1">Production Warning</h4>
          <p className="text-sm text-amber-800">
            Policy changes take effect immediately. Test changes carefully before saving.
            Invalid Rego syntax will cause OPA to fail and fallback to Simple RBAC mode.
          </p>
        </div>
      </div>

      {/* Editor */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900">Authorization Policy (Rego)</h3>
          <p className="text-sm text-gray-600 mt-1">
            Path: <code className="bg-gray-100 px-2 py-1 rounded">app/core/policy/rego/authz.rego</code>
          </p>
        </div>
        <div className="h-[500px]">
          {loading ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              Loading policy...
            </div>
          ) : (
            <Editor
              height="100%"
              defaultLanguage="rego"
              theme="vs-dark"
              value={policyContent}
              onChange={(value) => setPolicyContent(value || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 2
              }}
            />
          )}
        </div>
      </div>

      {/* Policy Tester */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Play className="w-5 h-5" />
            Test Policy
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Test authorization decisions against current policy
          </p>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">User</label>
              <input
                type="text"
                value={testUser}
                onChange={(e) => setTestUser(e.target.value)}
                placeholder="user@msil.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Action</label>
              <select
                value={testAction}
                onChange={(e) => setTestAction(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="invoke">invoke</option>
                <option value="read">read</option>
                <option value="write">write</option>
                <option value="delete">delete</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Resource</label>
              <input
                type="text"
                value={testResource}
                onChange={(e) => setTestResource(e.target.value)}
                placeholder="tool_name"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={testPolicy}
              disabled={testing}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              {testing ? 'Testing...' : 'Test Decision'}
            </button>
          </div>

          {/* Test Result */}
          {testResult && (
            <div className={`mt-4 p-4 rounded-lg border ${
              testResult.allowed
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}>
              <div className="flex items-start gap-3">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                  testResult.allowed ? 'bg-green-500' : 'bg-red-500'
                }`}>
                  {testResult.allowed ? (
                    <CheckCircle className="w-4 h-4 text-white" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-white" />
                  )}
                </div>
                <div className="flex-1">
                  <h4 className={`font-semibold mb-1 ${
                    testResult.allowed ? 'text-green-900' : 'text-red-900'
                  }`}>
                    {testResult.allowed ? 'Access Allowed' : 'Access Denied'}
                  </h4>
                  <p className={`text-sm ${
                    testResult.allowed ? 'text-green-800' : 'text-red-800'
                  }`}>
                    User <strong>{testUser}</strong> is{' '}
                    {testResult.allowed ? 'allowed' : 'not allowed'} to{' '}
                    <strong>{testAction}</strong> resource <strong>{testResource}</strong>
                  </p>
                  {testResult.reason && (
                    <p className="text-sm text-gray-600 mt-2">
                      Reason: {testResult.reason}
                    </p>
                  )}
                  {testResult.error && (
                    <p className="text-sm text-red-700 mt-2">
                      Error: {testResult.error}
                    </p>
                  )}
                  {testResult.engine && (
                    <p className="text-xs text-gray-500 mt-2">
                      Engine: {testResult.engine}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Syntax Reference */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">Rego Syntax Reference</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• <code>package msil.authz</code> - Package declaration (required)</li>
          <li>• <code>default allow = false</code> - Default deny policy</li>
          <li>• <code>allow &#123; ... &#125;</code> - Allow rule (multiple rules can exist)</li>
          <li>• <code>input.user.roles[_] == &quot;admin&quot;</code> - Check if user has admin role</li>
          <li>• <code>input.action == &quot;invoke&quot;</code> - Check action type</li>
          <li>• <code>startswith(input.resource, &quot;get_&quot;)</code> - String matching</li>
        </ul>
      </div>
    </div>
  );
}
