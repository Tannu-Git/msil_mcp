import { useEffect, useState } from 'react'
import { ToolList } from '@/components/tools/ToolList'
import { fetchTools } from '@/lib/api'
import { Search, Filter } from 'lucide-react'

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

export function Tools() {
  const [tools, setTools] = useState<Tool[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [total, setTotal] = useState(0)

  useEffect(() => {
    async function loadTools() {
      try {
        const result = await fetchTools(0, 50)
        setTools(result.items || [])
        setTotal(result.total || 0)
      } catch (error) {
        console.error('Failed to load tools:', error)
      } finally {
        setLoading(false)
      }
    }
    loadTools()
  }, [])

  const filteredTools = tools.filter(tool =>
    tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tool.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tool.category?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-msil-blue"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">MCP Tools</h1>
          <p className="text-gray-500">Manage and monitor registered tools</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-msil-blue focus:border-transparent"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <Filter className="w-4 h-4" />
            <span>Filter</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <p className="text-sm text-gray-500">
            Showing {filteredTools.length} of {tools.length} tools
          </p>
        </div>
        <ToolList tools={filteredTools} />
      </div>
    </div>
  )
}
