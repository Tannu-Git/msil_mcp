import { useState, useEffect } from 'react';
import { Shield, Plus, Trash2, Edit2, X, Users } from 'lucide-react';
import { addPolicyRolePermission, createPolicyRole, deletePolicyRole, fetchPolicyRoles, removePolicyRolePermission } from '../lib/api';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';

interface Role {
  name: string;
  permissions: string[];
}

interface RoleUser {
  username: string;
  email?: string;
  roles: string[];
  created_at?: string;
}

export default function Policies() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [editingRole, setEditingRole] = useState<string | null>(null);
  const [newPermission, setNewPermission] = useState('');
  const [stats, setStats] = useState({ total_policies: 0, active_roles: 0 });
  const [loading, setLoading] = useState(true);
  const [newRoleName, setNewRoleName] = useState('');
  const [newRolePermissions, setNewRolePermissions] = useState('');
  const [viewingRoleUsers, setViewingRoleUsers] = useState<string | null>(null);
  const [roleUsers, setRoleUsers] = useState<RoleUser[]>([]);
  const [usersDialogOpen, setUsersDialogOpen] = useState(false);
  const [toolNames, setToolNames] = useState<string[]>([]);
  const [showPermissionBuilder, setShowPermissionBuilder] = useState(false);
  const [permissionAction, setPermissionAction] = useState('invoke');
  const [permissionResource, setPermissionResource] = useState('');

  const permissionActions = ['invoke', 'read', 'write', 'delete', '*'];
  const permissionResourceTypes = ['tool', 'config', 'dashboard', '*'];

  useEffect(() => {
    loadPolicies();
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      const response = await fetch('/api/analytics/tools/list?limit=1000', {
        headers: {
          'x-api-key': 'msil-mcp-dev-key-2026',
          'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'mock-jwt-token')
        }
      });

      if (response.ok) {
        const data = await response.json();
        const names = (data.tools || []).map((t: any) => t.name);
        setToolNames(names);
      }
    } catch (error) {
      console.error('Failed to fetch tools:', error);
    }
  };

  const loadPolicies = async () => {
    try {
      const result = await fetchPolicyRoles();
      setRoles(result.roles || []);
      setStats({
        total_policies: (result.roles || []).reduce((sum: number, r: Role) => sum + r.permissions.length, 0),
        active_roles: (result.roles || []).length
      });
    } catch (error) {
      console.error('Failed to load policies:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshRoles = async () => {
    const result = await fetchPolicyRoles();
    setRoles(result.roles || []);
    setStats({
      total_policies: (result.roles || []).reduce((sum: number, r: Role) => sum + r.permissions.length, 0),
      active_roles: (result.roles || []).length
    });
  };

  const addPermission = async (roleName: string) => {
    if (!newPermission.trim()) return;

    await addPolicyRolePermission(roleName, newPermission.trim());
    setNewPermission('');
    setShowPermissionBuilder(false);
    setPermissionAction('invoke');
    setPermissionResource('');
    await refreshRoles();
  };

  const buildPermission = () => {
    const permission = `${permissionAction}:${permissionResource}`;
    setNewPermission(permission);
    setShowPermissionBuilder(false);
  };

  const removePermission = async (roleName: string, permission: string) => {
    await removePolicyRolePermission(roleName, permission);
    await refreshRoles();
  };

  const handleCreateRole = async () => {
    if (!newRoleName.trim()) return;
    const permissions = newRolePermissions
      .split(',')
      .map(p => p.trim())
      .filter(Boolean);

    await createPolicyRole({ name: newRoleName.trim(), permissions });
    setNewRoleName('');
    setNewRolePermissions('');
    await refreshRoles();
  };

  const handleDeleteRole = async (roleName: string) => {
    if (!confirm(`Delete role "${roleName}"?`)) return;
    await deletePolicyRole(roleName);
    await refreshRoles();
  };

  const viewRoleUsers = async (roleName: string) => {
    try {
      const response = await fetch(`/api/admin/roles/${roleName}/users`, {
        headers: {
          'x-api-key': 'msil-mcp-dev-key-2026',
          'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'mock-jwt-token')
        }
      });

      if (response.ok) {
        const data = await response.json();
        setRoleUsers(data.users || []);
        setViewingRoleUsers(roleName);
        setUsersDialogOpen(true);
      }
    } catch (error) {
      console.error('Failed to fetch role users:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="w-8 h-8 text-blue-600" />
            Policy Configuration
          </h1>
          <p className="text-gray-600 mt-1">Manage role-based access control and permissions</p>
        </div>
      </div>

      {/* Create Role */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Create Role</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Role Name</label>
            <input
              type="text"
              value={newRoleName}
              onChange={(e) => setNewRoleName(e.target.value)}
              placeholder="e.g., operator"
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700">Initial Permissions (comma-separated)</label>
            <input
              type="text"
              value={newRolePermissions}
              onChange={(e) => setNewRolePermissions(e.target.value)}
              placeholder="invoke:*, read:*, write:tool"
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
        </div>
        <div className="mt-4">
          <button
            onClick={handleCreateRole}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create Role
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Roles</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{stats.active_roles}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Permissions</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{stats.total_policies}</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Edit2 className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Policy Engine</p>
              <p className="text-lg font-semibold text-green-600 mt-1">Simple RBAC</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Role Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {loading && (
          <div className="col-span-full text-sm text-gray-500">Loading roles...</div>
        )}
        {roles.map((role) => (
          <div key={role.name} className="bg-white rounded-lg shadow">
            {/* Role Header */}
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 capitalize">{role.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {role.permissions.length} permission{role.permissions.length !== 1 ? 's' : ''}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => viewRoleUsers(role.name)}
                    className="p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                    title="View users with this role"
                  >
                    <Users className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => setEditingRole(editingRole === role.name ? null : role.name)}
                    className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  >
                    {editingRole === role.name ? <X className="w-5 h-5" /> : <Edit2 className="w-5 h-5" />}
                  </button>
                  <button
                    onClick={() => handleDeleteRole(role.name)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Permissions List */}
            <div className="p-6 space-y-2">
              {role.permissions.map((permission, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg group hover:bg-gray-100 transition-colors"
                >
                  <code className="text-sm font-mono text-gray-700">{permission}</code>
                  {editingRole === role.name && permission !== '*' && (
                    <button
                      onClick={() => removePermission(role.name, permission)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-red-600 hover:bg-red-50 rounded transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}

              {/* Add Permission */}
              {editingRole === role.name && (
                <div className="space-y-3 mt-4">
                  {/* Manual Permission Input */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newPermission}
                      onChange={(e) => setNewPermission(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && addPermission(role.name)}
                      placeholder="action:resource (e.g., invoke:tool_name)"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      onClick={() => setShowPermissionBuilder(!showPermissionBuilder)}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                      title="Permission Builder"
                    >
                      Builder
                    </button>
                    <button
                      onClick={() => addPermission(role.name)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Add
                    </button>
                  </div>

                  {/* Permission Builder */}
                  {showPermissionBuilder && (
                    <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg space-y-3">
                      <h4 className="font-medium text-gray-900">Permission Builder</h4>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Action</label>
                          <select
                            value={permissionAction}
                            onChange={(e) => setPermissionAction(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          >
                            {permissionActions.map(action => (
                              <option key={action} value={action}>{action}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Resource</label>
                          <select
                            value={permissionResource}
                            onChange={(e) => setPermissionResource(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          >
                            <option value="">Select resource...</option>
                            <option value="*">* (All)</option>
                            {permissionResourceTypes.map(type => (
                              <option key={type} value={type}>{type}</option>
                            ))}
                            <optgroup label="Tools">
                              {toolNames.slice(0, 20).map(name => (
                                <option key={name} value={name}>{name}</option>
                              ))}
                            </optgroup>
                          </select>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="text-sm text-gray-600">
                          Preview: <code className="bg-white px-2 py-1 rounded border">
                            {permissionAction}:{permissionResource || '...'
                          }</code>
                        </div>
                        <button
                          onClick={buildPermission}
                          disabled={!permissionResource}
                          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Use This Permission
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Permission Format Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">Permission Format</h4>
        <p className="text-sm text-blue-800 mb-2">
          Permissions follow the format: <code className="bg-blue-100 px-2 py-1 rounded">action:resource</code>
        </p>
        <ul className="text-sm text-blue-800 space-y-1 ml-4">
          <li><code>*</code> - Full access to everything</li>
          <li><code>invoke:*</code> - Invoke all tools</li>
          <li><code>invoke:tool_name</code> - Invoke specific tool</li>
          <li><code>read:*</code> - Read all resources</li>
          <li><code>write:tool</code> - Write/modify tools</li>
          <li><code>write:config</code> - Modify configuration</li>
        </ul>
      </div>

      {/* Role Users Dialog */}
      <Dialog open={usersDialogOpen} onOpenChange={setUsersDialogOpen}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader className="px-8 pt-6">
            <DialogTitle>Users with &quot;{viewingRoleUsers}&quot; role</DialogTitle>
          </DialogHeader>
          <div className="px-8 py-4">
            {roleUsers.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No users have this role yet
              </div>
            ) : (
              <div className="space-y-3">
                {roleUsers.map((user) => (
                  <div
                    key={user.username}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 font-semibold">
                          {user.username.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">{user.username}</div>
                        {user.email && user.email !== user.username && (
                          <div className="text-sm text-gray-500">{user.email}</div>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {user.roles.map((role) => (
                        <span
                          key={role}
                          className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            role === viewingRoleUsers
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {role}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <DialogFooter className="px-8 pb-6">
            <button
              onClick={() => setUsersDialogOpen(false)}
              className="px-4 py-2 bg-gray-100 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Close
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
