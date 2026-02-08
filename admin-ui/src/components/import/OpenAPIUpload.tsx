import { useState } from 'react'
import { Upload, FileJson, Link as LinkIcon, Loader2, CheckCircle, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface OpenAPIUploadProps {
  onUploadSuccess: (data: any) => void
}

export function OpenAPIUpload({ onUploadSuccess }: OpenAPIUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadMode, setUploadMode] = useState<'file' | 'url'>('file')
  const [url, setUrl] = useState('')
  const [category, setCategory] = useState('imported')
  const [bundleName, setBundleName] = useState('')

  const handleFileUpload = async (file: File) => {
    setError(null)
    setUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('category', category)
      if (bundleName) {
        formData.append('bundle_name', bundleName)
      }

      const response = await fetch('/api/admin/openapi/upload', {
        method: 'POST',
        headers: {
          'x-api-key': 'msil-mcp-dev-key-2026',
          'Authorization': 'Bearer mock-jwt-token'
        },
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const data = await response.json()
      onUploadSuccess(data)
    } catch (err: any) {
      setError(err.message || 'Failed to upload file')
    } finally {
      setUploading(false)
    }
  }

  const handleURLImport = async () => {
    if (!url.trim()) {
      setError('Please enter a URL')
      return
    }

    setError(null)
    setUploading(true)

    try {
      const params = new URLSearchParams({
        url: url.trim(),
        category,
        ...(bundleName && { bundle_name: bundleName })
      })

      const response = await fetch(`/api/admin/openapi/import-url?${params}`, {
        method: 'POST',
        headers: {
          'x-api-key': 'msil-mcp-dev-key-2026',
          'Authorization': 'Bearer mock-jwt-token'
        }
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Import failed')
      }

      const data = await response.json()
      onUploadSuccess(data)
    } catch (err: any) {
      setError(err.message || 'Failed to import from URL')
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)

    const files = Array.from(e.dataTransfer.files)
    const file = files.find(f => f.name.endsWith('.yaml') || f.name.endsWith('.yml') || f.name.endsWith('.json'))

    if (file) {
      handleFileUpload(file)
    } else {
      setError('Please upload a YAML or JSON file')
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileUpload(file)
    }
  }

  return (
    <div className="space-y-6">
      {/* Mode Selector */}
      <div className="flex gap-4 border-b border-gray-200">
        <button
          onClick={() => setUploadMode('file')}
          className={cn(
            'px-4 py-2 font-medium transition-colors border-b-2',
            uploadMode === 'file'
              ? 'text-msil-blue border-msil-blue'
              : 'text-gray-500 border-transparent hover:text-gray-700'
          )}
        >
          <Upload className="inline-block w-4 h-4 mr-2" />
          Upload File
        </button>
        <button
          onClick={() => setUploadMode('url')}
          className={cn(
            'px-4 py-2 font-medium transition-colors border-b-2',
            uploadMode === 'url'
              ? 'text-msil-blue border-msil-blue'
              : 'text-gray-500 border-transparent hover:text-gray-700'
          )}
        >
          <LinkIcon className="inline-block w-4 h-4 mr-2" />
          Import from URL
        </button>
      </div>

      {/* Configuration */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category
          </label>
          <input
            type="text"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="e.g., customer, vehicle"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-msil-blue"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Bundle Name (Optional)
          </label>
          <input
            type="text"
            value={bundleName}
            onChange={(e) => setBundleName(e.target.value)}
            placeholder="e.g., Service Booking"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-msil-blue"
          />
        </div>
      </div>

      {/* Upload Area */}
      {uploadMode === 'file' ? (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          className={cn(
            'border-2 border-dashed rounded-xl p-12 text-center transition-colors',
            dragOver ? 'border-msil-blue bg-msil-blue/5' : 'border-gray-300 hover:border-gray-400',
            uploading && 'opacity-50 pointer-events-none'
          )}
        >
          {uploading ? (
            <div className="space-y-3">
              <Loader2 className="w-12 h-12 mx-auto text-msil-blue animate-spin" />
              <p className="text-gray-600">Parsing OpenAPI specification...</p>
            </div>
          ) : (
            <div className="space-y-4">
              <FileJson className="w-16 h-16 mx-auto text-gray-400" />
              <div>
                <p className="text-lg font-medium text-gray-700">
                  Drop OpenAPI file here or click to browse
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Supports OpenAPI 3.0, 3.1, Swagger 2.0 (YAML or JSON)
                </p>
              </div>
              <label className="inline-block">
                <span className="px-6 py-2 bg-msil-blue text-white rounded-lg hover:bg-msil-blue-dark cursor-pointer transition-colors">
                  Select File
                </span>
                <input
                  type="file"
                  accept=".yaml,.yml,.json"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              OpenAPI Specification URL
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://api.example.com/openapi.yaml"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-msil-blue"
            />
          </div>
          <button
            onClick={handleURLImport}
            disabled={uploading || !url.trim()}
            className="w-full px-6 py-3 bg-msil-blue text-white rounded-lg hover:bg-msil-blue-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {uploading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <LinkIcon className="w-5 h-5" />
                Import from URL
              </>
            )}
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-800">Upload Failed</p>
            <p className="text-sm text-red-600 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Tip:</strong> The parser will automatically generate MCP tool definitions from your OpenAPI operations.
          You'll be able to review and edit the tools before registering them.
        </p>
      </div>
    </div>
  )
}
