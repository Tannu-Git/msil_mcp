import React, { useState, useEffect } from 'react';
import { Shield, Plus, Trash2, Edit2, Save, X } from 'lucide-react';
import { api } from '../lib/api';

interface Role {
  name: string;
  permissions: string[];
}

export default function Policies() {
  const [roles, setRoles] = useState<Role[]>([
    { name: 'admin', permissions: ['*'] },
    { name: 'developer', permissions: ['invoke:*', 'read:*', 'write:tool', 'write:config'] },
    { name: 'operator', permissions: ['invoke:*', 'read:*'] },
    { name: 'user', permissions: ['invoke:allowed_tools', 'read:tool'] }
  ]);
  const [editingRole, setEditingRole] = useState<string | null>(null);
  const [newPermission, setNewPermission] = useState('');
  const [stats, setStats] = useState({ total_policies: 0, active_roles: 0 });

  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    try {
      // In future, load from API
      setStats({
        total_policies: roles.reduce((sum, r) => sum + r.permissions.length, 0),
        active_roles: roles.length
      });
    } catch (error) {
      console.error('Failed to load policies:', error);
    }
  };

  const addPermission = (roleName: string) => {
    if (!newPermission.trim()) return;

    setRoles(roles.map(role => {
      if (role.name === roleName) {
        return {
          ...role,
          permissions: [...role.permissions, newPermission.trim()]
        };
      }
      return role;
    }));
    setNewPermission('');
  };

  const removePermission = (roleName: string, permission: string) => {
    setRoles(roles.map(role => {
      if (role.name === roleName) {
        return {
          ...role,
          permissions: role.permissions.filter(p => p !== permission)
        };
      }
      return role;
    }));
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
                <button
                  onClick={() => setEditingRole(editingRole === role.name ? null : role.name)}
                  className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  {editingRole === role.name ? <X className="w-5 h-5" /> : <Edit2 className="w-5 h-5" />}
                </button>
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
                <div className="flex gap-2 mt-4">
                  <input
                    type="text"
                    value={newPermission}
                    onChange={(e) => setNewPermission(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addPermission(role.name)}
                    placeholder="action:resource (e.g., invoke:tool_name)"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    onClick={() => addPermission(role.name)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Add
                  </button>
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
    </div>
  );
}
