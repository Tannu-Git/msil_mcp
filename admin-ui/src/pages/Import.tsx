import { useState } from 'react'
import { OpenAPIUpload } from '@/components/import/OpenAPIUpload'
import { ToolPreview } from '@/components/import/ToolPreview'
import { CheckCircle, AlertCircle } from 'lucide-react'
import { getApiUrl } from '@/lib/config'

interface UploadResult {
  spec_id: string
  name: string
  version: string
  description: string
  tools_generated: number
  tools: any[]
  errors: string[]
  status: string
}

export function Import() {
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [tools, setTools] = useState<any[]>([])
  const [approving, setApproving] = useState(false)
  const [approved, setApproved] = useState(false)
  const [approvalResult, setApprovalResult] = useState<any>(null)

  const handleUploadSuccess = (data: UploadResult) => {
    setUploadResult(data)
    setTools(data.tools)
    setApproved(false)
    setApprovalResult(null)
  }

  const handleApprove = async (toolIds: string[]) => {
    if (!uploadResult) return

    setApproving(true)
    try {
      const response = await fetch(getApiUrl('/api/admin/openapi/approve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': 'msil-mcp-dev-key-2026',
          'Authorization': 'Bearer mock-jwt-token'
        },
        body: JSON.stringify({
          spec_id: uploadResult.spec_id,
          tool_ids: toolIds
        })
      })

      if (!response.ok) {
        throw new Error('Failed to register tools')
      }

      const result = await response.json()
      setApprovalResult(result)
      setApproved(true)
    } catch (error) {
      console.error('Approval error:', error)
      alert('Failed to register tools. Please try again.')
    } finally {
      setApproving(false)
    }
  }

  const handleNewImport = () => {
    setUploadResult(null)
    setTools([])
    setApproved(false)
    setApprovalResult(null)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Import OpenAPI Specification</h1>
        <p className="text-gray-500">
          Upload or import OpenAPI/Swagger specs to automatically generate MCP tools
        </p>
      </div>

      {!uploadResult && !approved && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <OpenAPIUpload onUploadSuccess={handleUploadSuccess} />
        </div>
      )}

      {uploadResult && !approved && (
        <div className="space-y-6">
          {/* Spec Info */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-800">{uploadResult.name}</h2>
                <p className="text-sm text-gray-500 mt-1">
                  Version {uploadResult.version} • {uploadResult.tools_generated} tools generated
                </p>
                {uploadResult.description && (
                  <p className="text-sm text-gray-600 mt-2">{uploadResult.description}</p>
                )}
              </div>
              <button
                onClick={handleNewImport}
                className="text-sm text-gray-600 hover:text-gray-800"
              >
                Import Different Spec
              </button>
            </div>

            {/* Errors */}
            {uploadResult.errors && uploadResult.errors.length > 0 && (
              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800">
                      Some issues were found during parsing:
                    </p>
                    <ul className="mt-2 text-sm text-yellow-700 space-y-1">
                      {uploadResult.errors.map((error, idx) => (
                        <li key={idx}>• {error}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Tool Preview */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <ToolPreview
              tools={tools}
              onToolsChange={setTools}
              onApprove={handleApprove}
              approving={approving}
            />
          </div>
        </div>
      )}

      {approved && approvalResult && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="text-center py-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Tools Registered Successfully!
            </h2>
            <p className="text-gray-600 mb-6">
              {approvalResult.tools_registered} tools have been registered and are now available via MCP protocol
            </p>

            {/* Registered Tools List */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left max-w-2xl mx-auto">
              <p className="text-sm font-semibold text-gray-700 mb-2">Registered Tools:</p>
              <div className="space-y-1">
                {approvalResult.tool_names.map((name: string, idx: number) => (
                  <div key={idx} className="text-sm text-gray-600 flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <code className="font-mono">{name}</code>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4 justify-center">
              <button
                onClick={handleNewImport}
                className="px-6 py-2 bg-msil-blue text-white rounded-lg hover:bg-msil-blue-dark"
              >
                Import Another Spec
              </button>
              <button
                onClick={() => window.location.href = '/tools'}
                className="px-6 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                View All Tools
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Info Box */}
      {!uploadResult && (
        <div className="bg-msil-blue/5 border border-msil-blue/20 rounded-xl p-6">
          <h3 className="font-semibold text-gray-800 mb-2">How it works</h3>
          <ol className="space-y-2 text-sm text-gray-600">
            <li className="flex gap-2">
              <span className="font-semibold text-msil-blue">1.</span>
              Upload your OpenAPI 3.0/3.1 or Swagger 2.0 specification (YAML or JSON)
            </li>
            <li className="flex gap-2">
              <span className="font-semibold text-msil-blue">2.</span>
              The system automatically generates MCP tool definitions from your API operations
            </li>
            <li className="flex gap-2">
              <span className="font-semibold text-msil-blue">3.</span>
              Review and edit the generated tools (optional)
            </li>
            <li className="flex gap-2">
              <span className="font-semibold text-msil-blue">4.</span>
              Register selected tools - they become immediately available to AI agents via MCP protocol
            </li>
          </ol>
        </div>
      )}
    </div>
  )
}
