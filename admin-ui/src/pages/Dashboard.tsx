import { useEffect, useState } from 'react'
import { KPICards } from '@/components/dashboard/KPICards'
import { RecentActivity } from '@/components/dashboard/RecentActivity'
import { ToolsUsageChart } from '@/components/dashboard/ToolsUsageChart'
import { fetchDashboardData } from '@/lib/api'

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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-msil-blue"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        <p className="text-gray-500">Overview of MCP Server performance and metrics</p>
      </div>

      <KPICards data={data} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ToolsUsageChart />
        <RecentActivity />
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button className="w-full text-left px-4 py-3 bg-msil-blue/5 hover:bg-msil-blue/10 rounded-lg transition-colors">
              <span className="font-medium text-msil-blue">Reload Tools from Database</span>
              <p className="text-sm text-gray-500">Refresh tool registry from DB</p>
            </button>
            <button className="w-full text-left px-4 py-3 bg-msil-blue/5 hover:bg-msil-blue/10 rounded-lg transition-colors">
              <span className="font-medium text-msil-blue">Clear Cache</span>
              <p className="text-sm text-gray-500">Clear Redis cache entries</p>
            </button>
            <button className="w-full text-left px-4 py-3 bg-msil-blue/5 hover:bg-msil-blue/10 rounded-lg transition-colors">
              <span className="font-medium text-msil-blue">View Logs</span>
              <p className="text-sm text-gray-500">Open application logs</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
