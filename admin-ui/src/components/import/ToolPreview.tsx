import { useState } from 'react'
import { CheckCircle, XCircle, Edit2, Save, X, ChevronDown, ChevronUp, Code } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Tool {
  id: string
  name: string
  display_name: string
  description: string
  category: string
  api_endpoint: string
  http_method: string
  input_schema: any
  is_active: boolean
}

interface ToolPreviewProps {
  tools: Tool[]
  onToolsChange: (tools: Tool[]) => void
  onApprove: (toolIds: string[]) => void
  approving: boolean
}

export function ToolPreview({ tools, onToolsChange, onApprove, approving }: ToolPreviewProps) {
  const [selectedTools, setSelectedTools] = useState<Set<string>>(new Set(tools.map(t => t.id)))
  const [editingTool, setEditingTool] = useState<string | null>(null)
  const [expandedTool, setExpandedTool] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<Partial<Tool>>({})

  const handleSelectAll = () => {
    if (selectedTools.size === tools.length) {
      setSelectedTools(new Set())
    } else {
      setSelectedTools(new Set(tools.map(t => t.id)))
    }
  }

  const handleToggleSelect = (toolId: string) => {
    const newSelected = new Set(selectedTools)
    if (newSelected.has(toolId)) {
      newSelected.delete(toolId)
    } else {
      newSelected.add(toolId)
    }
    setSelectedTools(newSelected)
  }

  const handleStartEdit = (tool: Tool) => {
    setEditingTool(tool.id)
    setEditForm({
      name: tool.name,
      display_name: tool.display_name,
      description: tool.description,
      category: tool.category
    })
  }

  const handleSaveEdit = () => {
    if (!editingTool) return

    const updatedTools = tools.map(t =>
      t.id === editingTool
        ? { ...t, ...editForm }
        : t
    )
    onToolsChange(updatedTools)
    setEditingTool(null)
    setEditForm({})
  }

  const handleCancelEdit = () => {
    setEditingTool(null)
    setEditForm({})
  }

  const handleApprove = () => {
    const toolIds = Array.from(selectedTools)
    onApprove(toolIds)
  }

  const methodColors: Record<string, string> = {
    GET: 'bg-green-100 text-green-800',
    POST: 'bg-blue-100 text-blue-800',
    PUT: 'bg-yellow-100 text-yellow-800',
    PATCH: 'bg-orange-100 text-orange-800',
    DELETE: 'bg-red-100 text-red-800'
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">
            Generated Tools Preview
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Review and edit tools before registering ({tools.length} tools found)
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleSelectAll}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            {selectedTools.size === tools.length ? 'Deselect All' : 'Select All'}
          </button>
          <button
            onClick={handleApprove}
            disabled={selectedTools.size === 0 || approving}
            className="px-6 py-2 bg-msil-blue text-white rounded-lg hover:bg-msil-blue-dark disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {approving ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Registering...
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                Register Selected ({selectedTools.size})
              </>
            )}
          </button>
        </div>
      </div>

      {/* Tools List */}
      <div className="space-y-3">
        {tools.map((tool) => {
          const isSelected = selectedTools.has(tool.id)
          const isEditing = editingTool === tool.id
          const isExpanded = expandedTool === tool.id

          return (
            <div
              key={tool.id}
              className={cn(
                'border rounded-lg p-4 transition-all',
                isSelected ? 'border-msil-blue bg-msil-blue/5' : 'border-gray-200 bg-white'
              )}
            >
              <div className="flex items-start gap-4">
                {/* Checkbox */}
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => handleToggleSelect(tool.id)}
                  className="mt-1 w-4 h-4 text-msil-blue border-gray-300 rounded focus:ring-msil-blue"
                />

                {/* Content */}
                <div className="flex-1 min-w-0">
                  {isEditing ? (
                    // Edit Mode
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Tool Name
                          </label>
                          <input
                            type="text"
                            value={editForm.name || ''}
                            onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-msil-blue"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Display Name
                          </label>
                          <input
                            type="text"
                            value={editForm.display_name || ''}
                            onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })}
                            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-msil-blue"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Description
                        </label>
                        <textarea
                          value={editForm.description || ''}
                          onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                          rows={2}
                          className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-msil-blue"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Category
                        </label>
                        <input
                          type="text"
                          value={editForm.category || ''}
                          onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                          className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-msil-blue"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleSaveEdit}
                          className="px-3 py-1.5 text-sm bg-msil-blue text-white rounded hover:bg-msil-blue-dark flex items-center gap-1"
                        >
                          <Save className="w-3 h-3" />
                          Save
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="px-3 py-1.5 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 flex items-center gap-1"
                        >
                          <X className="w-3 h-3" />
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    // View Mode
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <h4 className="font-semibold text-gray-900">{tool.display_name}</h4>
                          <span className="text-sm font-mono text-gray-600 bg-gray-100 px-2 py-0.5 rounded">
                            {tool.name}
                          </span>
                          <span className={cn('text-xs font-semibold px-2 py-0.5 rounded', methodColors[tool.http_method] || 'bg-gray-100 text-gray-800')}>
                            {tool.http_method}
                          </span>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleStartEdit(tool)}
                            className="p-1.5 text-gray-400 hover:text-msil-blue hover:bg-msil-blue/10 rounded transition-colors"
                            title="Edit tool"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setExpandedTool(isExpanded ? null : tool.id)}
                            className="p-1.5 text-gray-400 hover:text-gray-600 rounded transition-colors"
                            title={isExpanded ? 'Collapse' : 'Expand'}
                          >
                            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>

                      <p className="text-sm text-gray-600">{tool.description}</p>

                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Code className="w-3 h-3" />
                          {tool.api_endpoint}
                        </span>
                        <span className="px-2 py-0.5 bg-gray-100 rounded">
                          {tool.category}
                        </span>
                      </div>

                      {/* Expanded Schema */}
                      {isExpanded && (
                        <div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded">
                          <p className="text-xs font-semibold text-gray-700 mb-2">Input Schema:</p>
                          <pre className="text-xs text-gray-600 overflow-x-auto">
                            {JSON.stringify(tool.input_schema, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
