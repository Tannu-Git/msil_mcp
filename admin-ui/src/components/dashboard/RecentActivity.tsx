import { CheckCircle, XCircle, Clock } from 'lucide-react'

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
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Tool Executions</h3>
      <div className="space-y-3">
        {mockActivity.map((activity) => (
          <div 
            key={activity.id}
            className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
          >
            {activity.status === 'success' ? (
              <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
            ) : (
              <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800 truncate">
                {activity.tool}
              </p>
              <p className="text-xs text-gray-500">{activity.time}</p>
            </div>
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Clock className="w-3 h-3" />
              {activity.duration}
            </div>
          </div>
        ))}
      </div>
      <button className="w-full mt-4 text-sm text-msil-blue hover:text-msil-blue-light transition-colors">
        View all executions →
      </button>
    </div>
  )
}
