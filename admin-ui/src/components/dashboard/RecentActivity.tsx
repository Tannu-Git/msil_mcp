import { CheckCircle, XCircle, Clock, ArrowRight, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'

const mockActivity = [
  {
    id: 1,
    tool: 'create_service_booking',
    status: 'success',
    time: '2 minutes ago',
    duration: '234ms'
  },
  {
    id: 2,
    tool: 'resolve_vehicle',
    status: 'success',
    time: '5 minutes ago',
    duration: '156ms'
  },
  {
    id: 3,
    tool: 'get_nearby_dealers',
    status: 'success',
    time: '8 minutes ago',
    duration: '312ms'
  },
  {
    id: 4,
    tool: 'get_available_slots',
    status: 'error',
    time: '12 minutes ago',
    duration: '1024ms'
  },
  {
    id: 5,
    tool: 'resolve_customer',
    status: 'success',
    time: '15 minutes ago',
    duration: '98ms'
  }
]

export function RecentActivity() {
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
        {mockActivity.map((activity, index) => (
          <div 
            key={activity.id}
            className={cn(
              "flex items-center gap-3 p-3.5 rounded-xl transition-all duration-200 group cursor-pointer",
              activity.status === 'success' 
                ? "bg-gray-50 hover:bg-emerald-50 border border-transparent hover:border-emerald-100" 
                : "bg-red-50/50 hover:bg-red-50 border border-transparent hover:border-red-100",
              "animate-slideInRight",
              `stagger-${index + 1}`
            )}
            style={{ opacity: 0 }}
          >
            {activity.status === 'success' ? (
              <div className="p-2 rounded-lg bg-emerald-100 text-emerald-600 group-hover:bg-emerald-200 transition-colors">
                <CheckCircle className="w-4 h-4" />
              </div>
            ) : (
              <div className="p-2 rounded-lg bg-red-100 text-red-600 group-hover:bg-red-200 transition-colors">
                <XCircle className="w-4 h-4" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800 truncate group-hover:text-gray-900">
                {activity.tool}
              </p>
              <p className="text-xs text-gray-500">{activity.time}</p>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-white rounded-lg text-xs text-gray-600 font-medium shadow-sm">
              <Clock className="w-3 h-3 text-gray-400" />
              {activity.duration}
            </div>
          </div>
        ))}
      </div>
      
      <button className="w-full mt-5 py-3 flex items-center justify-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-xl transition-all group">
        View all executions
        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
      </button>
    </div>
  )
}
