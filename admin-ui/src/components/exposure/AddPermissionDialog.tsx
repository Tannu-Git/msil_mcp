import { useState } from 'react'
import { AlertCircle, Loader, Check } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { ExposureBundle, formatPermission, buildPermission } from '@/lib/api/exposureApi'

interface AddPermissionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onAdd: (permission: string) => void
  bundles: ExposureBundle[]
  existingPermissions: string[]
  saving: boolean
}

type PermissionType = 'all' | 'bundle' | 'tool'

export function AddPermissionDialog({
  open,
  onOpenChange,
  onAdd,
  bundles,
  existingPermissions,
  saving,
}: AddPermissionDialogProps) {
  const [permissionType, setPermissionType] = useState<PermissionType>('bundle')
  const [selectedBundle, setSelectedBundle] = useState<string>('')
  const [selectedTool, setSelectedTool] = useState<string>('')

  const currentBundle = bundles.find((b) => b.name === selectedBundle)
  const isAllAccess = existingPermissions.includes('expose:all')
  const isBundleAlreadyAdded = selectedBundle
    ? existingPermissions.includes(`expose:bundle:${selectedBundle}`)
    : false

  function handleAdd() {
    let permission = ''

    switch (permissionType) {
      case 'all':
        permission = 'expose:all'
        break
      case 'bundle':
        permission = `expose:bundle:${selectedBundle}`
        break
      case 'tool':
        permission = `expose:tool:${selectedTool}`
        break
    }

    if (permission) {
      onAdd(permission)
      // Reset form
      setPermissionType('bundle')
      setSelectedBundle('')
      setSelectedTool('')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[520px] max-h-[85vh]">
        <DialogHeader>
          <DialogTitle>Add Exposure Permission</DialogTitle>
          <DialogDescription>
            Grant this role access to specific tools or bundles
          </DialogDescription>
        </DialogHeader>

        {/* Alert if already has all access */}
        {isAllAccess && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-2 mx-6">
            <AlertCircle className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-blue-800">
              This role already has access to all tools
            </p>
          </div>
        )}

        <div className="space-y-4 px-6 py-4">
          {/* Permission Type Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-900 mb-2">
              Permission Type
            </label>
            <div className="space-y-2">
              <label className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-slate-50">
                <input
                  type="radio"
                  value="all"
                  checked={permissionType === 'all'}
                  onChange={(e) => setPermissionType(e.target.value as PermissionType)}
                  disabled={isAllAccess}
                  className="w-4 h-4"
                />
                <div>
                  <span className="block font-medium text-slate-900">All Tools</span>
                  <span className="text-xs text-slate-600">
                    Grant access to all tools (no restrictions)
                  </span>
                </div>
              </label>

              <label className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-slate-50">
                <input
                  type="radio"
                  value="bundle"
                  checked={permissionType === 'bundle'}
                  onChange={(e) => setPermissionType(e.target.value as PermissionType)}
                  className="w-4 h-4"
                />
                <div>
                  <span className="block font-medium text-slate-900">Bundle</span>
                  <span className="text-xs text-slate-600">
                    Grant access to all tools in a bundle
                  </span>
                </div>
              </label>

              <label className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-slate-50">
                <input
                  type="radio"
                  value="tool"
                  checked={permissionType === 'tool'}
                  onChange={(e) => setPermissionType(e.target.value as PermissionType)}
                  className="w-4 h-4"
                />
                <div>
                  <span className="block font-medium text-slate-900">Specific Tool</span>
                  <span className="text-xs text-slate-600">
                    Grant access to a single tool
                  </span>
                </div>
              </label>
            </div>
          </div>

          {/* Bundle Selector */}
          {permissionType === 'bundle' && (
            <div>
              <label className="block text-sm font-medium text-slate-900 mb-2">
                Select Bundle
              </label>
              <select
                value={selectedBundle}
                onChange={(e) => setSelectedBundle(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">-- Choose a bundle --</option>
                {bundles.map((bundle) => (
                  <option key={bundle.name} value={bundle.name}>
                    {bundle.name} ({bundle.tool_count} tools)
                  </option>
                ))}
              </select>

              {isBundleAlreadyAdded && (
                <div className="mt-2 text-sm text-amber-600 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  This role already has access to this bundle
                </div>
              )}

              {currentBundle && (
                <div className="mt-3 p-3 bg-slate-50 rounded-lg">
                  <p className="text-sm font-medium text-slate-900">
                    {currentBundle.name}
                  </p>
                  <p className="text-xs text-slate-600 mt-1">
                    {currentBundle.description}
                  </p>
                  <p className="text-xs text-slate-500 mt-2 font-medium">
                    {currentBundle.tool_count} tools available
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Tool Selector */}
          {permissionType === 'tool' && (
            <div>
              <label className="block text-sm font-medium text-slate-900 mb-2">
                Select Tool
              </label>
              <select
                value={selectedTool}
                onChange={(e) => setSelectedTool(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">-- Choose a tool --</option>
                {bundles.flatMap((bundle) =>
                  bundle.tools.map((tool) => (
                    <option key={tool.id} value={tool.name}>
                      {tool.display_name} ({bundle.name})
                    </option>
                  ))
                )}
              </select>

              {selectedTool && (
                <div className="mt-3 p-3 bg-slate-50 rounded-lg">
                  <p className="text-sm font-medium text-slate-900">{selectedTool}</p>
                  <p className="text-xs text-slate-600 mt-1">
                    Will grant access to this specific tool only
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Preview */}
          {(permissionType === 'all' ||
            (permissionType === 'bundle' && selectedBundle) ||
            (permissionType === 'tool' && selectedTool)) && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs text-blue-600 font-medium uppercase tracking-wide">
                Permission to Add
              </p>
              <p className="text-sm font-mono mt-2 text-blue-900">
                {permissionType === 'all'
                  ? 'expose:all'
                  : permissionType === 'bundle'
                    ? `expose:bundle:${selectedBundle}`
                    : `expose:tool:${selectedTool}`}
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleAdd}
            disabled={
              saving ||
              isAllAccess ||
              isBundleAlreadyAdded ||
              (permissionType === 'bundle' && !selectedBundle) ||
              (permissionType === 'tool' && !selectedTool)
            }
            className="gap-2"
          >
            {saving ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                Adding...
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                Add Permission
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
