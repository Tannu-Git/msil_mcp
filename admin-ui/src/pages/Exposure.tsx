import { useState, useEffect } from 'react'
import { Eye, Plus, Trash2, AlertCircle, Loader, RefreshCw, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  getRoleExposurePermissions,
  addExposurePermission,
  removeExposurePermission,
  getAvailableBundles,
  previewRoleExposure,
  formatPermission,
  buildPermission,
  ExposureBundle,
  ExposurePreview,
  ExposedTool,
} from '@/lib/api/exposureApi'
import { AddPermissionDialog } from '@/components/exposure/AddPermissionDialog'
import { PreviewPanel } from '@/components/exposure/PreviewPanel'
import { PermissionsList } from '@/components/exposure/PermissionsList'

const ROLES = ['operator', 'developer', 'admin']

export default function Exposure() {
  const [selectedRole, setSelectedRole] = useState<string>('operator')
  const [permissions, setPermissions] = useState<string[]>([])
  const [bundles, setBundles] = useState<ExposureBundle[]>([])
  const [preview, setPreview] = useState<ExposurePreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)

  // Load permissions and bundles on role change
  useEffect(() => {
    loadRoleData()
  }, [selectedRole])

  async function loadRoleData() {
    try {
      setLoading(true)
      setError(null)
      const [perms, bundles_, preview_] = await Promise.all([
        getRoleExposurePermissions(selectedRole),
        getAvailableBundles(),
        previewRoleExposure(selectedRole),
      ])
      setPermissions(perms)
      setBundles(bundles_)
      setPreview(preview_)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load exposure data')
    } finally {
      setLoading(false)
    }
  }

  async function handleAddPermission(permission: string) {
    try {
      setSaving('add')
      await addExposurePermission(selectedRole, permission)
      setSuccess(`Permission added to ${selectedRole}`)
      setShowAddDialog(false)
      await loadRoleData()
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add permission')
    } finally {
      setSaving(null)
    }
  }

  async function handleRemovePermission(permission: string) {
    if (!confirm(`Remove permission: ${formatPermission(permission).type}?`)) return

    try {
      setSaving(permission)
      await removeExposurePermission(selectedRole, permission)
      setSuccess('Permission removed')
      await loadRoleData()
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove permission')
    } finally {
      setSaving(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
            <Eye className="w-8 h-8 text-blue-600" />
            Tool Exposure Governance
          </h1>
          <p className="text-slate-600 mt-1">
            Manage which tools are visible to different roles
          </p>
        </div>
        <Button
          onClick={loadRoleData}
          variant="outline"
          size="sm"
          className="gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-red-900">Error</h3>
            <p className="text-red-800 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Success Alert */}
      {success && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-emerald-600 mt-0.5 flex-shrink-0" />
          <p className="text-emerald-800 text-sm">{success}</p>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sidebar - Role Selector */}
        <Card className="lg:col-span-1 h-fit sticky top-6">
          <CardHeader>
            <CardTitle className="text-lg">Roles</CardTitle>
            <CardDescription>Select a role to manage exposure</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {ROLES.map((role) => (
              <button
                key={role}
                onClick={() => setSelectedRole(role)}
                className={`w-full px-4 py-3 rounded-lg text-left font-medium transition-colors ${
                  selectedRole === role
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-100 text-slate-900 hover:bg-slate-200'
                }`}
              >
                {role.charAt(0).toUpperCase() + role.slice(1)}
              </button>
            ))}
          </CardContent>
        </Card>

        {/* Main Content Area */}
        <div className="lg:col-span-2 space-y-6">
          {loading ? (
            <Card>
              <CardContent className="py-12">
                <div className="flex flex-col items-center gap-3">
                  <Loader className="w-8 h-8 text-blue-600 animate-spin" />
                  <p className="text-slate-600">Loading exposure data...</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Permissions Tab */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-3">
                  <div>
                    <CardTitle>Exposure Permissions</CardTitle>
                    <CardDescription>
                      Tools that {selectedRole} role can see and access
                    </CardDescription>
                  </div>
                  <Button
                    onClick={() => setShowAddDialog(true)}
                    size="sm"
                    className="gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Add Permission
                  </Button>
                </CardHeader>
                <CardContent>
                  <PermissionsList
                    permissions={permissions}
                    onRemove={handleRemovePermission}
                    saving={saving}
                  />
                </CardContent>
              </Card>

              {/* Preview Tab */}
              {preview && (
                <Card>
                  <CardHeader>
                    <CardTitle>Preview Tools</CardTitle>
                    <CardDescription>
                      This is what {selectedRole} role will see in tools/list
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <PreviewPanel
                      preview={preview}
                      bundles={bundles}
                    />
                  </CardContent>
                </Card>
              )}

              {/* Bundles Reference */}
              <Card>
                <CardHeader>
                  <CardTitle>Available Bundles</CardTitle>
                  <CardDescription>
                    All tool bundles that can be exposed
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {bundles.map((bundle) => (
                      <div
                        key={bundle.name}
                        className="p-4 rounded-lg border border-slate-200 bg-slate-50"
                      >
                        <h4 className="font-semibold text-slate-900">{bundle.name}</h4>
                        <p className="text-sm text-slate-600 mt-1">
                          {bundle.description}
                        </p>
                        <p className="text-xs text-slate-500 mt-2">
                          {bundle.tool_count} tools
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>

      {/* Add Permission Dialog */}
      <AddPermissionDialog
        open={showAddDialog}
        onOpenChange={setShowAddDialog}
        onAdd={handleAddPermission}
        bundles={bundles}
        existingPermissions={permissions}
        saving={saving === 'add'}
      />
    </div>
  )
}
