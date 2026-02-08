import { Wrench, ExternalLink, CheckCircle, XCircle, Copy, Edit, Power, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Tool {
  id: number
  name: string
  description: string
  category: string
  bundle_name?: string
  api_endpoint: string
  http_method: string
  is_active: boolean
  created_at: string | null
  updated_at: string | null
  tags: string[]
}

interface ToolListProps {
  tools: Tool[]
  onEdit?: (tool: Tool) => void
  onToggleActive?: (tool: Tool) => void
  onDelete?: (tool: Tool) => void
}

export function ToolList({ tools, onEdit, onToggleActive, onDelete }: ToolListProps) {
  const methodColors: Record<string, string> = {
    GET: 'bg-emerald-100 text-emerald-700 border border-emerald-200',
    POST: 'bg-blue-100 text-blue-700 border border-blue-200',
    PUT: 'bg-amber-100 text-amber-700 border border-amber-200',
    DELETE: 'bg-red-100 text-red-700 border border-red-200',
    PATCH: 'bg-purple-100 text-purple-700 border border-purple-200'
  }

  if (tools.length === 0) {
    return (
      <div className="p-12 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-100 flex items-center justify-center">
          <Wrench className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-800 mb-1">No tools found</h3>
        <p className="text-gray-500 text-sm">Try adjusting your search or filters</p>
      </div>
    )
  }

  return (
    <div className="divide-y divide-gray-100">
      {tools.map((tool, index) => (
        <div 
          key={tool.id}
          className={cn(
            "px-6 py-5 hover:bg-blue-50/50 transition-all duration-200 cursor-pointer group animate-fadeIn",
            `stagger-${Math.min(index + 1, 6)}`
          )}
          style={{ opacity: 0 }}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4 flex-1 min-w-0">
              {/* Icon */}
              <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/30 transition-shadow">
                <Wrench className="w-6 h-6 text-white" />
              </div>
              
              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="font-semibold text-gray-800 group-hover:text-blue-700 transition-colors">{tool.name}</h3>
                  <span className={cn(
                    "px-2.5 py-0.5 text-xs font-bold rounded-md",
                    methodColors[tool.http_method] || 'bg-gray-100 text-gray-700 border border-gray-200'
                  )}>
                    {tool.http_method}
                  </span>
                  {tool.is_active ? (
                    <span className="badge-success">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Active
                    </span>
                  ) : (
                    <span className="badge-danger">
                      <XCircle className="w-3 h-3 mr-1" />
                      Inactive
                    </span>
                  )}
                </div>
                
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">{tool.description}</p>
                
                <div className="flex flex-wrap items-center gap-3">
                  <span className="inline-flex items-center gap-1.5 font-mono text-xs bg-gray-100 text-gray-600 px-3 py-1.5 rounded-lg border border-gray-200">
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full" />
                    {tool.api_endpoint}
                  </span>
                  {tool.category && (
                    <span className="text-xs text-gray-500 bg-gray-50 px-2.5 py-1 rounded-lg">
                      {tool.category}
                    </span>
                  )}
                  {tool.bundle_name && (
                    <span className="text-xs text-blue-600 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-100">
                      Toolkit: {tool.bundle_name}
                    </span>
                  )}
                  {tool.tags && tool.tags.length > 0 && tool.tags.map((tag, i) => (
                    <span key={i} className="text-xs text-blue-600 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-100">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Actions */}
            <div className="flex-shrink-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                title="Copy endpoint"
                onClick={() => navigator.clipboard.writeText(tool.api_endpoint)}
              >
                <Copy className="w-4 h-4" />
              </button>
              <button
                className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                title="Edit tool"
                onClick={() => onEdit?.(tool)}
              >
                <Edit className="w-4 h-4" />
              </button>
              <button
                className={cn(
                  "p-2 rounded-lg transition-colors",
                  tool.is_active
                    ? "text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                    : "text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                )}
                title={tool.is_active ? "Deactivate tool" : "Activate tool"}
                onClick={() => onToggleActive?.(tool)}
              >
                <Power className="w-4 h-4" />
              </button>
              <button
                className="p-2 text-red-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Delete tool"
                onClick={() => onDelete?.(tool)}
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
