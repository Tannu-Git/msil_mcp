import { useEffect, useState } from 'react'
import { ToolList } from '@/components/tools/ToolList'
import { createAdminTool, deleteAdminTool, fetchAdminTools, updateAdminTool } from '@/lib/api'
import { Search, Filter, Wrench, Plus, Download, X, Save } from 'lucide-react'

interface Tool {
  id: string
  name: string
  display_name?: string
  description: string
  category: string
  bundle_name?: string
  api_endpoint: string
  http_method: string
  input_schema?: Record<string, any>
  output_schema?: Record<string, any> | null
  headers?: Record<string, string>
  auth_type?: string
  is_active: boolean
  version?: string
  risk_level?: string
  requires_elevation?: boolean
  requires_confirmation?: boolean
  rate_limit_tier?: string
  created_at: string | null
  updated_at: string | null
  tags: string[]
}

export function Tools() {
  const [tools, setTools] = useState<Tool[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [total, setTotal] = useState(0)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState<Tool>({
    id: '',
    name: '',
    display_name: '',
    description: '',
    category: '',
    api_endpoint: '',
    http_method: 'POST',
    input_schema: {},
    output_schema: null,
    headers: {},
    auth_type: 'none',
    is_active: true,
    version: '1.0.0',
    risk_level: 'read',
    requires_elevation: false,
    requires_confirmation: false,
    rate_limit_tier: 'standard',
    created_at: null,
    updated_at: null,
    tags: []
  })
  const [inputSchemaText, setInputSchemaText] = useState('{}')
  const [outputSchemaText, setOutputSchemaText] = useState('')
  const [headersText, setHeadersText] = useState('{}')

  useEffect(() => {
    async function loadTools() {
      try {
        const result = await fetchAdminTools(undefined, false)
        setTools(result.tools || [])
        setTotal(result.total || 0)
      } catch (error) {
        console.error('Failed to load tools:', error)
      } finally {
        setLoading(false)
      }
    }
    loadTools()
  }, [])

  const openCreateModal = () => {
    setIsEditing(false)
    setSelectedTool(null)
    setSaveError(null)
    setForm({
      id: '',
      name: '',
      display_name: '',
      description: '',
      category: '',
      api_endpoint: '',
      http_method: 'POST',
      input_schema: {},
      output_schema: null,
      headers: {},
      auth_type: 'none',
      is_active: true,
      version: '1.0.0',
      risk_level: 'read',
      requires_elevation: false,
      requires_confirmation: false,
      rate_limit_tier: 'standard',
      created_at: null,
      updated_at: null,
      tags: []
    })
    setInputSchemaText('{}')
    setOutputSchemaText('')
    setHeadersText('{}')
    setIsModalOpen(true)
  }

  const openEditModal = (tool: Tool) => {
    setIsEditing(true)
    setSelectedTool(tool)
    setSaveError(null)
    setForm({ ...tool })
    setInputSchemaText(JSON.stringify(tool.input_schema || {}, null, 2))
    setOutputSchemaText(tool.output_schema ? JSON.stringify(tool.output_schema, null, 2) : '')
    setHeadersText(JSON.stringify(tool.headers || {}, null, 2))
    setIsModalOpen(true)
  }

  const parseJson = (value: string, label: string) => {
    if (!value.trim()) return null
    try {
      return JSON.parse(value)
    } catch (error) {
      throw new Error(`${label} must be valid JSON`)
    }
  }

  const saveTool = async () => {
    try {
      setSaving(true)
      setSaveError(null)

      const inputSchema = parseJson(inputSchemaText, 'Input schema') || {}
      const outputSchema = parseJson(outputSchemaText, 'Output schema')
      const headers = parseJson(headersText, 'Headers') || {}

      const payload = {
        name: form.name,
        display_name: form.display_name,
        description: form.description,
        category: form.category,
        api_endpoint: form.api_endpoint,
        http_method: form.http_method,
        input_schema: inputSchema,
        output_schema: outputSchema,
        headers,
        auth_type: form.auth_type,
        is_active: form.is_active,
        version: form.version,
        risk_level: form.risk_level,
        requires_elevation: form.requires_elevation,
        requires_confirmation: form.requires_confirmation,
        rate_limit_tier: form.rate_limit_tier
      }

      if (isEditing && selectedTool) {
        await updateAdminTool(selectedTool.name, payload)
      } else {
        await createAdminTool(payload)
      }

      const refreshed = await fetchAdminTools(undefined, false)
      setTools(refreshed.tools || [])
      setTotal(refreshed.total || 0)
      setIsModalOpen(false)
    } catch (error: any) {
      setSaveError(error?.message || 'Failed to save tool')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleActive = async (tool: Tool) => {
    try {
      await updateAdminTool(tool.name, { is_active: !tool.is_active })
      const refreshed = await fetchAdminTools(undefined, false)
      setTools(refreshed.tools || [])
      setTotal(refreshed.total || 0)
    } catch (error) {
      console.error('Failed to update tool status:', error)
    }
  }

  const handleDelete = async (tool: Tool) => {
    if (!confirm(`Deactivate tool "${tool.name}"?`)) return
    try {
      await deleteAdminTool(tool.name)
      const refreshed = await fetchAdminTools(undefined, false)
      setTools(refreshed.tools || [])
      setTotal(refreshed.total || 0)
    } catch (error) {
      console.error('Failed to delete tool:', error)
    }
  }

  const filteredTools = tools.filter(tool =>
    tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tool.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tool.category?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const groupedTools = filteredTools.reduce((groups, tool) => {
    const key = tool.bundle_name?.trim() || 'Unbundled Tools'
    if (!groups[key]) {
      groups[key] = []
    }
    groups[key].push(tool)
    return groups
  }, {} as Record<string, Tool[]>)

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
          <button
            onClick={openCreateModal}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-500 hover:to-blue-600 transition-all shadow-lg shadow-blue-500/25 font-medium"
          >
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
        {Object.entries(groupedTools).map(([bundleName, bundleTools]) => (
          <div key={bundleName}>
            <div className="px-6 py-3 border-b border-gray-100 bg-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-gray-800">{bundleName}</span>
                <span className="text-xs text-gray-500">({bundleTools.length} tools)</span>
              </div>
            </div>
            <ToolList
              tools={bundleTools}
              onEdit={openEditModal}
              onToggleActive={handleToggleActive}
              onDelete={handleDelete}
            />
          </div>
        ))}
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {isEditing ? 'Edit Tool' : 'Create Tool'}
                </h2>
                <p className="text-sm text-gray-500">Manage tool configuration and security settings</p>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              {saveError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {saveError}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">Tool Name</label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    disabled={isEditing}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Display Name</label>
                  <input
                    type="text"
                    value={form.display_name}
                    onChange={(e) => setForm({ ...form, display_name: e.target.value })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="text-sm font-medium text-gray-700">Description</label>
                  <textarea
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    rows={2}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Category</label>
                  <input
                    type="text"
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">HTTP Method</label>
                  <select
                    value={form.http_method}
                    onChange={(e) => setForm({ ...form, http_method: e.target.value })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20"
                  >
                    <option>GET</option>
                    <option>POST</option>
                    <option>PUT</option>
                    <option>PATCH</option>
                    <option>DELETE</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="text-sm font-medium text-gray-700">API Endpoint</label>
                  <input
                    type="text"
                    value={form.api_endpoint}
                    onChange={(e) => setForm({ ...form, api_endpoint: e.target.value })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Auth Type</label>
                  <input
                    type="text"
                    value={form.auth_type}
                    onChange={(e) => setForm({ ...form, auth_type: e.target.value })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Version</label>
                  <input
                    type="text"
                    value={form.version}
                    onChange={(e) => setForm({ ...form, version: e.target.value })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Risk Level</label>
                  <select
                    value={form.risk_level}
                    onChange={(e) => setForm({ ...form, risk_level: e.target.value })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20"
                  >
                    <option value="read">read</option>
                    <option value="write">write</option>
                    <option value="privileged">privileged</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Rate Limit Tier</label>
                  <select
                    value={form.rate_limit_tier}
                    onChange={(e) => setForm({ ...form, rate_limit_tier: e.target.value })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20"
                  >
                    <option value="permissive">permissive</option>
                    <option value="standard">standard</option>
                    <option value="strict">strict</option>
                  </select>
                </div>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      checked={form.is_active}
                      onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                      className="rounded border-gray-300"
                    />
                    Active
                  </label>
                  <label className="flex items-center gap-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      checked={Boolean(form.requires_elevation)}
                      onChange={(e) => setForm({ ...form, requires_elevation: e.target.checked })}
                      className="rounded border-gray-300"
                    />
                    Requires elevation
                  </label>
                  <label className="flex items-center gap-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      checked={Boolean(form.requires_confirmation)}
                      onChange={(e) => setForm({ ...form, requires_confirmation: e.target.checked })}
                      className="rounded border-gray-300"
                    />
                    Requires confirmation
                  </label>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">Input Schema (JSON)</label>
                  <textarea
                    value={inputSchemaText}
                    onChange={(e) => setInputSchemaText(e.target.value)}
                    rows={6}
                    className="mt-1 w-full px-3 py-2 font-mono text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Output Schema (JSON)</label>
                  <textarea
                    value={outputSchemaText}
                    onChange={(e) => setOutputSchemaText(e.target.value)}
                    rows={6}
                    className="mt-1 w-full px-3 py-2 font-mono text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="text-sm font-medium text-gray-700">Headers (JSON)</label>
                  <textarea
                    value={headersText}
                    onChange={(e) => setHeadersText(e.target.value)}
                    rows={4}
                    className="mt-1 w-full px-3 py-2 font-mono text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-3">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={saveTool}
                disabled={saving}
                className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                {saving ? 'Saving...' : 'Save Tool'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
