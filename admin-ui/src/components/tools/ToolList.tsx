import { Wrench, ExternalLink, CheckCircle, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Tool {
  id: number
  name: string
  description: string
  category: string
  api_endpoint: string
  http_method: string
  is_active: boolean
  created_at: string | null
  updated_at: string | null
  tags: string[]
}

interface ToolListProps {
  tools: Tool[]
}

export function ToolList({ tools }: ToolListProps) {
  const methodColors: Record<string, string> = {
    GET: 'bg-green-100 text-green-700',
    POST: 'bg-blue-100 text-blue-700',
    PUT: 'bg-yellow-100 text-yellow-700',
    DELETE: 'bg-red-100 text-red-700'
  }

  if (tools.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        <Wrench className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No tools found</p>
      </div>
    )
  }

  return (
    <div className="divide-y divide-gray-200">
      {tools.map((tool) => (
        <div 
          key={tool.id}
          className="px-6 py-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4 flex-1 min-w-0">
              <div className="flex-shrink-0 w-10 h-10 bg-msil-blue/10 rounded-lg flex items-center justify-center">
                <Wrench className="w-5 h-5 text-msil-blue" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium text-gray-800">{tool.name}</h3>
                  <span className={cn(
                    "px-2 py-0.5 text-xs font-medium rounded",
                    methodColors[tool.http_method] || 'bg-gray-100 text-gray-700'
                  )}>
                    {tool.http_method}
                  </span>
                  {tool.is_active ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-500" />
                  )}
                </div>
                <p className="text-sm text-gray-500 mt-0.5">{tool.description}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                  <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">
                    {tool.api_endpoint}
                  </span>
                  <span>Category: {tool.category || 'N/A'}</span>
                  {tool.tags && tool.tags.length > 0 && (
                    <span>Tags: {tool.tags.join(', ')}</span>
                  )}
                </div>
              </div>
            </div>
            <button className="flex-shrink-0 p-2 text-gray-400 hover:text-msil-blue hover:bg-msil-blue/5 rounded-lg transition-colors">
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
