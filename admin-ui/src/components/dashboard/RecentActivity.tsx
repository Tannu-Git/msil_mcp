import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Clock, ArrowRight, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'
import { fetchRecentActivity } from '@/lib/api'

interface ActivityItem {
  execution_id: string
  tool_name: string
  status: 'success' | 'failed' | 'running'
  started_at: string | null
  duration_ms?: number
}

function formatRelativeTime(timestamp: string | null) {
  if (!timestamp) return 'just now'
  const date = new Date(timestamp)
  const diffMs = Date.now() - date.getTime()
  const diffSeconds = Math.max(0, Math.floor(diffMs / 1000))
  if (diffSeconds < 60) return `${diffSeconds}s ago`
  const diffMinutes = Math.floor(diffSeconds / 60)
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

export function RecentActivity() {
  const [activity, setActivity] = useState<ActivityItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadActivity() {
      try {
        const data = await fetchRecentActivity(8)
        setActivity(data || [])
      } catch (error) {
        console.error('Failed to load recent activity:', error)
      } finally {
        setLoading(false)
      }
    }
    loadActivity()
  }, [])

  return (
    <div className="card-premium p-6 h-full">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="section-header-icon">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Recent Executions</h3>
            <p className="text-xs text-gray-500">Latest tool activities</p>
          </div>
        </div>
        <span className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-50 text-blue-600 rounded-lg text-xs font-semibold">
          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
          Live
        </span>
      </div>
      
      <div className="space-y-3">
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <div className="flex flex-col items-center gap-3">
              <div className="relative">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 animate-pulse" />
                <div className="absolute inset-0 w-10 h-10 rounded-xl border-2 border-blue-400 border-t-transparent animate-spin" />
              </div>
              <p className="text-sm text-gray-500">Loading activity...</p>
            </div>
          </div>
        ) : activity.length === 0 ? (
          <div className="text-center py-10">
            <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-gray-100 flex items-center justify-center">
              <Activity className="w-6 h-6 text-gray-400" />
            </div>
            <p className="text-sm text-gray-500">No recent activity yet</p>
          </div>
        ) : (
          activity.map((item, index) => (
            <div 
              key={item.execution_id}
              className={cn(
                "flex items-center gap-3 p-3.5 rounded-xl transition-all duration-200 group cursor-pointer",
                item.status === 'success' 
                  ? "bg-gray-50 hover:bg-emerald-50 border border-transparent hover:border-emerald-100" 
                  : item.status === 'failed'
                    ? "bg-red-50/50 hover:bg-red-50 border border-transparent hover:border-red-100"
                    : "bg-amber-50/60 hover:bg-amber-50 border border-transparent hover:border-amber-100",
                "animate-slideInRight",
                `stagger-${index + 1}`
              )}
              style={{ opacity: 0 }}
            >
              {item.status === 'success' ? (
                <div className="p-2 rounded-lg bg-emerald-100 text-emerald-600 group-hover:bg-emerald-200 transition-colors">
                  <CheckCircle className="w-4 h-4" />
                </div>
              ) : item.status === 'failed' ? (
                <div className="p-2 rounded-lg bg-red-100 text-red-600 group-hover:bg-red-200 transition-colors">
                  <XCircle className="w-4 h-4" />
                </div>
              ) : (
                <div className="p-2 rounded-lg bg-amber-100 text-amber-600 group-hover:bg-amber-200 transition-colors">
                  <Clock className="w-4 h-4" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate group-hover:text-gray-900">
                  {item.tool_name}
                </p>
                <p className="text-xs text-gray-500">{formatRelativeTime(item.started_at)}</p>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-white rounded-lg text-xs text-gray-600 font-medium shadow-sm">
                <Clock className="w-3 h-3 text-gray-400" />
                {(item.duration_ms ?? 0)}ms
              </div>
            </div>
          ))
        )}
      </div>
      
      <button className="w-full mt-5 py-3 flex items-center justify-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-xl transition-all group">
        View all executions
        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
      </button>
    </div>
  )
}
