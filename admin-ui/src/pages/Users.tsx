import { useState, useEffect } from 'react';
import { Users as UsersIcon, Shield, Search, Edit2, Check } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';

interface User {
  username: string;
  email?: string;
  roles: string[];
  created_at?: string;
}

interface Role {
  name: string;
  permissions: string[];
}

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Load users and roles
      const [usersResponse, rolesResponse] = await Promise.all([
        fetch('/api/admin/users', {
          headers: {
            'x-api-key': 'msil-mcp-dev-key-2026',
            'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'mock-jwt-token')
          }
        }),
        fetch('/api/admin/policies/roles', {
          headers: {
            'x-api-key': 'msil-mcp-dev-key-2026',
            'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'mock-jwt-token')
          }
        })
      ]);

      if (usersResponse.ok) {
        const data = await usersResponse.json();
        setUsers(data.users || []);
      }

      if (rolesResponse.ok) {
        const data = await rolesResponse.json();
        setRoles(data.roles || []);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const openRoleDialog = (user: User) => {
    setSelectedUser(user);
    setSelectedRoles([...user.roles]);
    setDialogOpen(true);
  };

  const toggleRole = (roleName: string) => {
    setSelectedRoles(prev =>
      prev.includes(roleName)
        ? prev.filter(r => r !== roleName)
        : [...prev, roleName]
    );
  };

  const saveRoles = async () => {
    if (!selectedUser) return;

    try {
      const response = await fetch(`/api/admin/users/${selectedUser.username}/roles`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': 'msil-mcp-dev-key-2026',
          'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'mock-jwt-token')
        },
        body: JSON.stringify({ roles: selectedRoles })
      });

      if (response.ok) {
        await loadData();
        setDialogOpen(false);
        setSelectedUser(null);
      }
    } catch (error) {
      console.error('Failed to update roles:', error);
    }
  };

  const filteredUsers = users.filter(user =>
    user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (user.email && user.email.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const getRoleBadgeColor = (roleName: string) => {
    const colors: Record<string, string> = {
      admin: 'bg-purple-100 text-purple-700',
      developer: 'bg-blue-100 text-blue-700',
      operator: 'bg-green-100 text-green-700',
      user: 'bg-gray-100 text-gray-700'
    };
    return colors[roleName] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <UsersIcon className="w-8 h-8 text-blue-600" />
            User Management
          </h1>
          <p className="text-gray-600 mt-1">Manage users and assign roles</p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search users by name or email..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Users</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{users.length}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <UsersIcon className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Available Roles</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{roles.length}</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Search Results</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{filteredUsers.length}</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <Search className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Users List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Roles
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">
                    Loading users...
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">
                    No users found
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr key={user.username} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-blue-600 font-semibold">
                            {user.username.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{user.username}</div>
                          {user.email && (
                            <div className="text-sm text-gray-500">{user.email}</div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-2">
                        {user.roles.length === 0 ? (
                          <span className="text-sm text-gray-500">No roles</span>
                        ) : (
                          user.roles.map((role) => (
                            <span
                              key={role}
                              className={`px-2 py-1 text-xs font-semibold rounded-full ${getRoleBadgeColor(role)}`}
                            >
                              {role}
                            </span>
                          ))
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.created_at
                        ? new Date(user.created_at).toLocaleDateString()
                        : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => openRoleDialog(user)}
                        className="text-blue-600 hover:text-blue-900 inline-flex items-center gap-1"
                      >
                        <Edit2 className="w-4 h-4" />
                        Manage Roles
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Role Assignment Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[520px] max-h-[90vh] overflow-y-auto">
          <DialogHeader className="px-8 pt-6">
            <DialogTitle>Manage Roles for {selectedUser?.username}</DialogTitle>
          </DialogHeader>
          <div className="px-8 py-4 space-y-4">
            <p className="text-sm text-gray-600">
              Select roles to assign to this user. Multiple roles can be assigned.
            </p>
            <div className="space-y-2">
              {roles.map((role) => (
                <div
                  key={role.name}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                  onClick={() => toggleRole(role.name)}
                >
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 capitalize">{role.name}</div>
                    <div className="text-sm text-gray-500">
                      {role.permissions.length} permission{role.permissions.length !== 1 ? 's' : ''}
                    </div>
                  </div>
                  <div className={`w-6 h-6 rounded border-2 flex items-center justify-center ${
                    selectedRoles.includes(role.name)
                      ? 'bg-blue-600 border-blue-600'
                      : 'border-gray-300'
                  }`}>
                    {selectedRoles.includes(role.name) && (
                      <Check className="w-4 h-4 text-white" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <DialogFooter className="px-8 pb-6">
            <button
              onClick={() => setDialogOpen(false)}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={saveRoles}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Save Changes
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">About User Management</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Users are automatically created on first authentication</li>
          <li>• Multiple roles can be assigned to a single user</li>
          <li>• Role permissions are combined when a user has multiple roles</li>
          <li>• Changes to roles take effect immediately</li>
        </ul>
      </div>
    </div>
  );
}
