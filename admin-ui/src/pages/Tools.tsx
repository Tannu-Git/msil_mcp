import { useEffect, useState } from 'react'
import { ToolList } from '@/components/tools/ToolList'
import { fetchTools } from '@/lib/api'
import { Search, Filter, Wrench, Plus, Download } from 'lucide-react'

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
        <div className="flex flex-col items-center gap-3">
          <div className="relative">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 animate-pulse" />
            <div className="absolute inset-0 w-12 h-12 rounded-xl border-2 border-blue-400 border-t-transparent animate-spin" />
          </div>
          <p className="text-sm text-gray-500 font-medium">Loading tools...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="section-header-icon">
            <Wrench className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="page-title text-3xl">MCP Tools</h1>
            <p className="text-gray-500 mt-1">Manage and monitor registered tools</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-4 py-2.5 text-gray-600 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all shadow-sm">
            <Download className="w-4 h-4" />
            <span className="font-medium">Export</span>
          </button>
          <button className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-500 hover:to-blue-600 transition-all shadow-lg shadow-blue-500/25 font-medium">
            <Plus className="w-4 h-4" />
            <span>Add Tool</span>
          </button>
        </div>
      </div>

      {/* Search and Filter Bar */}
      <div className="card-premium p-4">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search tools by name, description, or category..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:bg-white transition-all text-sm"
            />
          </div>
          <button className="flex items-center justify-center gap-2 px-5 py-3 border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all text-gray-600 font-medium">
            <Filter className="w-4 h-4" />
            <span>Filters</span>
          </button>
        </div>
      </div>

      {/* Tools Table */}
      <div className="card-premium overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600 font-medium">
              Showing <span className="text-gray-900 font-semibold">{filteredTools.length}</span> of <span className="text-gray-900 font-semibold">{tools.length}</span> tools
            </p>
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-semibold">
                <span className="w-2 h-2 bg-emerald-500 rounded-full" />
                {tools.filter(t => t.is_active).length} Active
              </span>
            </div>
          </div>
        </div>
        <ToolList tools={filteredTools} />
      </div>
    </div>
  )
}
