import { Car, Settings } from 'lucide-react'

export function Header() {
  return (
    <header className="bg-msil-blue text-white shadow-lg">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-white p-2 rounded-lg">
            <Car className="w-6 h-6 text-msil-blue" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">MARUTI SUZUKI</h1>
            <p className="text-xs text-msil-silver-light opacity-80">AI Service Assistant</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right text-sm">
            <p className="text-msil-silver-light">Powered by</p>
            <p className="font-medium">MCP Protocol</p>
          </div>
          <button className="p-2 hover:bg-msil-blue-light rounded-lg transition-colors">
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  )
}
