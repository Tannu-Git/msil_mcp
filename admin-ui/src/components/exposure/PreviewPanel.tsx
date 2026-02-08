import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { ExposurePreview, ExposureBundle } from '@/lib/api/exposureApi'

interface PreviewPanelProps {
  preview: ExposurePreview | null | undefined
  bundles: ExposureBundle[]
}

export function PreviewPanel({ preview, bundles }: PreviewPanelProps) {
  if (!preview) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Loading preview...</p>
      </div>
    )
  }

  const exposedBundles = preview?.exposed_bundles || []
  const exposedTools = preview?.exposed_tools || []
  const totalTools = preview?.total_exposed_tools || 0

  const [expandedBundles, setExpandedBundles] = useState<Set<string>>(
    new Set(exposedBundles?.slice(0, 2) || [])
  )

  function toggleBundle(bundleName: string) {
    const updated = new Set(expandedBundles)
    if (updated.has(bundleName)) {
      updated.delete(bundleName)
    } else {
      updated.add(bundleName)
    }
    setExpandedBundles(updated)
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
          <p className="text-xs text-blue-600 font-semibold uppercase tracking-wide">
            Total Tools
          </p>
          <p className="text-3xl font-bold text-blue-900 mt-2">
            {totalTools}
          </p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
          <p className="text-xs text-purple-600 font-semibold uppercase tracking-wide">
            Bundles
          </p>
          <p className="text-3xl font-bold text-purple-900 mt-2">
            {exposedBundles.length}
          </p>
        </div>
        <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-lg p-4 border border-emerald-200">
          <p className="text-xs text-emerald-600 font-semibold uppercase tracking-wide">
            Status
          </p>
          <p className="text-sm font-bold text-emerald-900 mt-2">
            {totalTools > 0 ? '✓ Active' : '○ No Access'}
          </p>
        </div>
      </div>

      {/* Tools by Bundle */}
      {exposedBundles.length > 0 ? (
        <div className="space-y-2">
          {exposedBundles.map((bundleName) => {
            const bundleTools = exposedTools.filter(
              (t) => t.bundle_name === bundleName
            )
            const isExpanded = expandedBundles.has(bundleName)

            return (
              <div key={bundleName} className="border border-slate-200 rounded-lg overflow-hidden">
                {/* Bundle Header */}
                <button
                  onClick={() => toggleBundle(bundleName)}
                  className="w-full px-4 py-3 bg-slate-50 hover:bg-slate-100 flex items-center justify-between transition-colors"
                >
                  <div className="text-left flex-1">
                    <h4 className="font-semibold text-slate-900">{bundleName}</h4>
                    <p className="text-xs text-slate-600 mt-1">
                      {bundleTools.length} tool{bundleTools.length !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <div className="text-slate-600">
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </div>
                </button>

                {/* Bundle Tools */}
                {isExpanded && (
                  <div className="bg-white border-t border-slate-200 divide-y divide-slate-200">
                    {bundleTools.map((tool) => (
                      <div key={tool.id} className="p-4 hover:bg-slate-50 transition-colors">
                        <div className="flex items-start gap-3">
                          <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <h5 className="font-medium text-slate-900">
                              {tool.display_name}
                            </h5>
                            {tool.description && (
                              <p className="text-xs text-slate-600 mt-1 line-clamp-2">
                                {tool.description}
                              </p>
                            )}
                            {tool.category && (
                              <p className="text-xs text-slate-500 mt-2">
                                Category: {tool.category}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-center py-8 bg-slate-50 rounded-lg border border-slate-200">
          <p className="text-slate-600">No tools exposed yet</p>
          <p className="text-sm text-slate-500 mt-1">
            Add permissions to grant this role access to tools
          </p>
        </div>
      )}
    </div>
  )
}
