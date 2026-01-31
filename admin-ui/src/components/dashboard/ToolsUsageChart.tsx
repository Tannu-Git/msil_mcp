import { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, Activity } from 'lucide-react'
import { fetchToolsUsage } from '@/lib/api'

interface ToolUsage {
  tool_name: string
  total_calls: number
  success_calls: number
  failed_calls: number
  avg_duration_ms: number
  last_used: string
}

export function ToolsUsageChart() {
  const [usage, setUsage] = useState<ToolUsage[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadUsage() {
      try {
        const data = await fetchToolsUsage(5)
        setUsage(data)
      } catch (error) {
        console.error('Failed to load tools usage:', error)
      } finally {
        setLoading(false)
      }
    }
    loadUsage()
  }, [])

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Top Tools by Usage</h3>
        <div className="flex items-center justify-center h-48">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-msil-blue"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Top Tools by Usage</h3>
        <Activity className="w-5 h-5 text-gray-400" />
      </div>
      
      <div className="space-y-4">
        {usage.map((tool, index) => {
          const successRate = tool.total_calls > 0 
            ? (tool.success_calls / tool.total_calls) * 100 
            : 0

          return (
            <div key={index} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">{tool.tool_name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">{tool.total_calls} calls</span>
                  {successRate >= 95 ? (
                    <TrendingUp className="w-4 h-4 text-green-500" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-500" />
                  )}
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-msil-blue h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(successRate, 100)}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>Success: {successRate.toFixed(1)}%</span>
                <span>Avg: {tool.avg_duration_ms}ms</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
