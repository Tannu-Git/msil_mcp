import { useEffect, useState } from 'react'
import { KPICards } from '@/components/dashboard/KPICards'
import { RecentActivity } from '@/components/dashboard/RecentActivity'
import { ToolsUsageChart } from '@/components/dashboard/ToolsUsageChart'
import { fetchDashboardData } from '@/lib/api'
import { RefreshCw, Database, Trash2, FileSearch, Zap, ArrowRight } from 'lucide-react'

interface DashboardData {
  total_tools: number
  active_tools: number
  total_requests: number
  success_rate: number
  avg_response_time: number
  total_conversations: number
}

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const result = await fetchDashboardData()
        setData(result)
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="relative">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 animate-pulse" />
            <div className="absolute inset-0 w-12 h-12 rounded-xl border-2 border-blue-400 border-t-transparent animate-spin" />
          </div>
          <p className="text-sm text-gray-500 font-medium">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  const quickActions = [
    {
      icon: RefreshCw,
      title: 'Reload Tools',
      description: 'Refresh tool registry from DB',
      gradient: 'from-blue-500 to-blue-600'
    },
    {
      icon: Database,
      title: 'Clear Cache',
      description: 'Clear Redis cache entries',
      gradient: 'from-purple-500 to-purple-600'
    },
    {
      icon: FileSearch,
      title: 'View Logs',
      description: 'Open application logs',
      gradient: 'from-emerald-500 to-emerald-600'
    }
  ]

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title text-3xl">Dashboard</h1>
          <p className="text-gray-500 mt-1">Overview of MCP Server performance and metrics</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-sm font-medium">
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            Live Data
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <KPICards data={data} />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tools Usage - Takes 2 columns */}
        <div className="lg:col-span-2">
          <ToolsUsageChart />
        </div>
        
        {/* Recent Activity */}
        <div className="lg:col-span-1">
          <RecentActivity />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card-premium p-6">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="section-header-icon">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">Quick Actions</h3>
              <p className="text-sm text-gray-500">Common administrative tasks</p>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickActions.map((action, index) => (
            <button
              key={index}
              className="group relative flex items-center gap-4 p-4 bg-gray-50 hover:bg-gray-100 rounded-xl transition-all duration-200 text-left overflow-hidden"
            >
              <div className={`p-3 rounded-xl bg-gradient-to-br ${action.gradient} shadow-lg transition-transform group-hover:scale-110`}>
                <action.icon className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-gray-800 group-hover:text-gray-900">{action.title}</p>
                <p className="text-sm text-gray-500">{action.description}</p>
              </div>
              <ArrowRight className="w-5 h-5 text-gray-300 group-hover:text-gray-400 group-hover:translate-x-1 transition-all" />
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
