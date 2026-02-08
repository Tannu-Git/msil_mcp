import { Trash2, Loader } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { formatPermission } from '@/lib/api/exposureApi'

interface PermissionsListProps {
  permissions: string[]
  onRemove: (permission: string) => void
  saving: string | null
}

export function PermissionsList({ permissions, onRemove, saving }: PermissionsListProps) {
  if (permissions.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-slate-600">No exposure permissions configured yet</p>
        <p className="text-sm text-slate-500 mt-1">
          Add permissions to grant this role access to tools
        </p>
      </div>
    )
  }

  const sortedPermissions = [...permissions].sort((a, b) => {
    // Sort with 'expose:all' first, then by type
    if (a === 'expose:all') return -1
    if (b === 'expose:all') return 1
    return a.localeCompare(b)
  })

  return (
    <div className="space-y-2">
      {sortedPermissions.map((permission) => {
        const { type, target } = formatPermission(permission)
        const isLoading = saving === permission

        return (
          <div
            key={permission}
            className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-blue-50/50 border border-blue-200 rounded-lg hover:border-blue-300 transition-colors"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3">
                <div className="px-2.5 py-1 bg-blue-600 text-white text-xs font-semibold rounded">
                  {type === 'All Tools' ? '∞' : type === 'Bundle' ? '📦' : '🔧'}
                </div>
                <div className="min-w-0">
                  <h4 className="font-medium text-slate-900">
                    {type === 'All Tools' ? 'Full Access' : type}
                  </h4>
                  {target !== 'Full Access' && (
                    <p className="text-sm text-slate-600 truncate">{target}</p>
                  )}
                </div>
              </div>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRemove(permission)}
              disabled={isLoading}
              className="ml-4 text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              {isLoading ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
            </Button>
          </div>
        )
      })}
    </div>
  )
}
