import { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, BarChart3, ArrowRight } from 'lucide-react'
import { fetchToolsUsage } from '@/lib/api'
import { cn } from '@/lib/utils'

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
      <div className="card-premium p-6 h-full">
        <div className="flex items-center gap-3 mb-6">
          <div className="section-header-icon">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Top Tools by Usage</h3>
            <p className="text-xs text-gray-500">Performance metrics</p>
          </div>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 animate-pulse" />
              <div className="absolute inset-0 w-10 h-10 rounded-xl border-2 border-blue-400 border-t-transparent animate-spin" />
            </div>
            <p className="text-sm text-gray-500">Loading usage data...</p>
          </div>
        </div>
      </div>
    )
  }

  const maxCalls = Math.max(...usage.map(t => t.total_calls), 1)

  return (
    <div className="card-premium p-6 h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="section-header-icon">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Top Tools by Usage</h3>
            <p className="text-xs text-gray-500">Performance metrics</p>
          </div>
        </div>
        <select className="text-sm bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-gray-600 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500">
          <option>Last 7 days</option>
          <option>Last 30 days</option>
          <option>All time</option>
        </select>
      </div>
      
      <div className="space-y-5">
        {usage.map((tool, index) => {
          const successRate = tool.total_calls > 0 
            ? (tool.success_calls / tool.total_calls) * 100 
            : 0
          const barWidth = (tool.total_calls / maxCalls) * 100

          return (
            <div 
              key={index} 
              className={cn(
                "group p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-all duration-200 cursor-pointer",
                "animate-fadeIn",
                `stagger-${index + 1}`
              )}
              style={{ opacity: 0 }}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold shadow-sm">
                    {index + 1}
                  </div>
                  <span className="font-semibold text-gray-800 group-hover:text-gray-900">{tool.tool_name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className={cn(
                    "text-sm font-semibold px-2.5 py-1 rounded-lg",
                    successRate >= 95 ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
                  )}>
                    {tool.total_calls.toLocaleString()} calls
                  </span>
                  {successRate >= 95 ? (
                    <TrendingUp className="w-4 h-4 text-emerald-500" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-amber-500" />
                  )}
                </div>
              </div>
              
              {/* Progress Bar */}
              <div className="h-2.5 bg-gray-200 rounded-full overflow-hidden mb-3">
                <div
                  className="h-full rounded-full transition-all duration-700 ease-out"
                  style={{ 
                    width: `${barWidth}%`,
                    background: successRate >= 95 
                      ? 'linear-gradient(90deg, #059669 0%, #10b981 100%)'
                      : 'linear-gradient(90deg, #d97706 0%, #f59e0b 100%)'
                  }}
                />
              </div>
              
              {/* Stats Row */}
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-4">
                  <span className={cn(
                    "font-semibold px-2 py-0.5 rounded",
                    successRate >= 95 ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
                  )}>
                    {successRate.toFixed(1)}% success
                  </span>
                  <span className="text-gray-500">
                    {tool.success_calls} / {tool.total_calls}
                  </span>
                </div>
                <span className="text-gray-500 font-medium">
                  Avg: <span className="text-gray-700">{tool.avg_duration_ms}ms</span>
                </span>
              </div>
            </div>
          )
        })}
      </div>

      <button className="w-full mt-6 py-3 flex items-center justify-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-xl transition-all group">
        View all tools analytics
        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
      </button>
    </div>
  )
}
