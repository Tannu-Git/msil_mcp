import { Wrench, Activity, CheckCircle, XCircle, Clock, Users, Calendar } from 'lucide-react'
import { cn } from '@/lib/utils'

interface KPICardsProps {
  data: {
    total_tools: number
    active_tools: number
    total_requests: number
    success_rate: number
    avg_response_time: number
    total_conversations: number
  } | null
}

export function KPICards({ data }: KPICardsProps) {
  const cards = [
    {
      title: 'Total Tools',
      value: data?.total_tools ?? 0,
      subtitle: `${data?.active_tools ?? 0} active`,
      icon: Wrench,
      color: 'bg-blue-500'
    },
    {
      title: 'Total Requests',
      value: data?.total_requests ?? 0,
      subtitle: 'All time',
      icon: Activity,
      color: 'bg-green-500'
    },
    {
      title: 'Success Rate',
      value: data ? `${data.success_rate.toFixed(1)}%` : '0%',
      subtitle: 'Last 24 hours',
      icon: CheckCircle,
      color: 'bg-emerald-500'
    },
    {
      title: 'Avg Response Time',
      value: `${data?.avg_response_time ?? 0}ms`,
      subtitle: 'All requests',
      icon: Clock,
      color: 'bg-orange-500'
    },
    {
      title: 'Conversations',
      value: data?.total_conversations ?? 0,
      subtitle: 'Total sessions',
      icon: Users,
      color: 'bg-purple-500'
    },
    {
      title: 'Active Tools',
      value: data?.active_tools ?? 0,
      subtitle: 'Ready to use',
      icon: Calendar,
      color: 'bg-msil-red'
    }
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map((card, index) => (
        <div 
          key={index}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500">{card.title}</p>
              <p className="text-2xl font-bold text-gray-800 mt-1">{card.value}</p>
              <p className="text-xs text-gray-400 mt-1">{card.subtitle}</p>
            </div>
            <div className={cn("p-2 rounded-lg", card.color)}>
              <card.icon className="w-5 h-5 text-white" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
