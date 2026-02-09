import { useState, useEffect } from 'react';
import { Shield, Play, CheckCircle, XCircle, AlertCircle, Users, Wrench } from 'lucide-react';
import { getApiUrl } from '@/lib/config';

interface TestResult {
  allowed: boolean;
  user: string;
  roles?: string[];
  action: string;
  resource: string;
  engine?: string;
  reason?: string;
  error?: string;
  execution_time_ms?: number;
}

export default function TestAuthorization() {
  const [user, setUser] = useState('testuser@msil.com');
  const [action, setAction] = useState('invoke');
  const [resource, setResource] = useState('');
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<TestResult | null>(null);
  const [testHistory, setTestHistory] = useState<TestResult[]>([]);

  // Available options
  const [users, setUsers] = useState<string[]>([]);
  const [tools, setTools] = useState<string[]>([]);

  const actions = ['invoke', 'read', 'write', 'delete', '*'];

  useEffect(() => {
    loadUsers();
    loadTools();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await fetch(getApiUrl('/api/admin/users'), {
        headers: {
          'x-api-key': 'msil-mcp-dev-key-2026',
          'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'mock-jwt-token')
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUsers((data.users || []).map((u: any) => u.username));
      }
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const loadTools = async () => {
    try {
      const response = await fetch(getApiUrl('/api/analytics/tools/list?limit=1000'), {
        headers: {
          'x-api-key': 'msil-mcp-dev-key-2026',
          'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'mock-jwt-token')
        }
      });

      if (response.ok) {
        const data = await response.json();
        setTools((data.tools || []).map((t: any) => t.name));
      }
    } catch (error) {
      console.error('Failed to load tools:', error);
    }
  };

  const runTest = async () => {
    if (!user || !action || !resource) {
      alert('Please fill all fields');
      return;
    }

    setTesting(true);
    setResult(null);

    const startTime = Date.now();

    try {
      const response = await fetch(getApiUrl('/api/admin/test-authz'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': 'msil-mcp-dev-key-2026',
          'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'mock-jwt-token')
        },
        body: JSON.stringify({ user, action, resource })
      });

      const execution_time_ms = Date.now() - startTime;

      if (response.ok) {
        const data = await response.json();
        const testResult = { ...data, execution_time_ms };
        setResult(testResult);
        setTestHistory(prev => [testResult, ...prev].slice(0, 10));
      } else {
        const error = await response.json();
        const testResult: TestResult = {
          allowed: false,
          user,
          action,
          resource,
          error: error.detail || 'Test failed',
          execution_time_ms
        };
        setResult(testResult);
        setTestHistory(prev => [testResult, ...prev].slice(0, 10));
      }
    } catch (error: any) {
      const execution_time_ms = Date.now() - startTime;
      const testResult: TestResult = {
        allowed: false,
        user,
        action,
        resource,
        error: error.message || 'Request failed',
        execution_time_ms
      };
      setResult(testResult);
      setTestHistory(prev => [testResult, ...prev].slice(0, 10));
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
            Test Authorization
          </h1>
          <p className="text-gray-600 mt-1">Test authorization decisions for users and resources</p>
        </div>
      </div>

      {/* Test Form */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900">Authorization Test</h3>
          <p className="text-sm text-gray-600 mt-1">
            Simulate authorization decisions to validate your RBAC and OPA policies
          </p>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* User Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Users className="w-4 h-4 inline mr-1" />
                User
              </label>
              <select
                value={user}
                onChange={(e) => setUser(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select user...</option>
                {users.map(u => (
                  <option key={u} value={u}>{u}</option>
                ))}
              </select>
              <input
                type="text"
                value={user}
                onChange={(e) => setUser(e.target.value)}
                placeholder="Or type custom user"
                className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>

            {/* Action Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Action
              </label>
              <select
                value={action}
                onChange={(e) => setAction(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {actions.map(a => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>

            {/* Resource Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Wrench className="w-4 h-4 inline mr-1" />
                Resource
              </label>
              <select
                value={resource}
                onChange={(e) => setResource(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select resource...</option>
                <option value="*">* (All)</option>
                <option value="config">config</option>
                <option value="dashboard">dashboard</option>
                <optgroup label="Tools">
                  {tools.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </optgroup>
              </select>
              <input
                type="text"
                value={resource}
                onChange={(e) => setResource(e.target.value)}
                placeholder="Or type custom resource"
                className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={runTest}
              disabled={testing || !user || !action || !resource}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              {testing ? 'Testing...' : 'Run Test'}
            </button>
            {result && (
              <span className="text-sm text-gray-500">
                Took {result.execution_time_ms}ms
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Test Result */}
      {result && (
        <div className={`bg-white rounded-lg shadow overflow-hidden border-l-4 ${
          result.allowed ? 'border-green-500' : 'border-red-500'
        }`}>
          <div className={`px-6 py-4 ${
            result.allowed ? 'bg-green-50' : 'bg-red-50'
          }`}>
            <div className="flex items-start gap-4">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 ${
                result.allowed ? 'bg-green-500' : 'bg-red-500'
              }`}>
                {result.allowed ? (
                  <CheckCircle className="w-6 h-6 text-white" />
                ) : (
                  <XCircle className="w-6 h-6 text-white" />
                )}
              </div>
              <div className="flex-1">
                <h3 className={`text-xl font-bold mb-2 ${
                  result.allowed ? 'text-green-900' : 'text-red-900'
                }`}>
                  {result.allowed ? 'Access Allowed ✓' : 'Access Denied ✗'}
                </h3>
                <div className="space-y-2">
                  <p className={`text-sm ${
                    result.allowed ? 'text-green-800' : 'text-red-800'
                  }`}>
                    User <strong>{result.user}</strong> is <strong>{result.allowed ? 'allowed' : 'not allowed'}</strong> to perform
                    action <strong>{result.action}</strong> on resource <strong>{result.resource}</strong>
                  </p>
                  {result.roles && result.roles.length > 0 && (
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-600">User Roles:</span>
                      {result.roles.map(role => (
                        <span key={role} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-semibold rounded">
                          {role}
                        </span>
                      ))}
                    </div>
                  )}
                  {result.engine && (
                    <p className="text-sm text-gray-600">
                      <strong>Policy Engine:</strong> {result.engine}
                    </p>
                  )}
                  {result.reason && (
                    <p className="text-sm text-gray-600">
                      <strong>Reason:</strong> {result.reason}
                    </p>
                  )}
                  {result.error && (
                    <div className="mt-2 p-3 bg-red-100 border border-red-200 rounded-lg">
                      <div className="flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-red-800">
                          <strong>Error:</strong> {result.error}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Test History */}
      {testHistory.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="border-b border-gray-200 px-6 py-4">
            <h3 className="text-lg font-semibold text-gray-900">Test History</h3>
            <p className="text-sm text-gray-600 mt-1">Recent authorization tests</p>
          </div>
          <div className="divide-y divide-gray-200">
            {testHistory.map((test, index) => (
              <div key={index} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      test.allowed ? 'bg-green-100' : 'bg-red-100'
                    }`}>
                      {test.allowed ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-600" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {test.user} → {test.action}:{test.resource}
                      </p>
                      {test.roles && (
                        <p className="text-xs text-gray-500">
                          Roles: {test.roles.join(', ')}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {test.engine && (
                      <span className="text-xs text-gray-500">
                        {test.engine}
                      </span>
                    )}
                    <span className={`px-2 py-1 text-xs font-semibold rounded ${
                      test.allowed
                        ? 'bg-green-100 text-green-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {test.allowed ? 'Allowed' : 'Denied'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">About Authorization Testing</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Tests run against your current RBAC and OPA policies</li>
          <li>• User roles are fetched from the user management system</li>
          <li>• Results show which policy engine was used (OPA or Simple RBAC)</li>
          <li>• Test history is kept in memory (cleared on page refresh)</li>
          <li>• Use this to validate policy changes before deploying</li>
        </ul>
      </div>
    </div>
  );
}
