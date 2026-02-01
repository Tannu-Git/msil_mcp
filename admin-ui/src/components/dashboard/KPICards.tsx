import { Wrench, Activity, CheckCircle, Clock, Users, Zap, TrendingUp, ArrowUpRight } from 'lucide-react'
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
      gradient: 'from-blue-600 to-blue-800',
      shadowColor: 'shadow-blue-500/25',
      trend: '+2',
      trendLabel: 'this week'
    },
    {
      title: 'Total Requests',
      value: data?.total_requests ?? 0,
      subtitle: 'All time',
      icon: Activity,
      gradient: 'from-emerald-500 to-emerald-700',
      shadowColor: 'shadow-emerald-500/25',
      trend: '+12%',
      trendLabel: 'vs last week'
    },
    {
      title: 'Success Rate',
      value: data ? `${data.success_rate.toFixed(1)}%` : '0%',
      subtitle: 'Last 24 hours',
      icon: CheckCircle,
      gradient: 'from-violet-500 to-violet-700',
      shadowColor: 'shadow-violet-500/25',
      trend: '+2.1%',
      trendLabel: 'improvement'
    },
    {
      title: 'Avg Response',
      value: `${data?.avg_response_time ?? 0}ms`,
      subtitle: 'All requests',
      icon: Clock,
      gradient: 'from-amber-500 to-orange-600',
      shadowColor: 'shadow-amber-500/25',
      trend: '-15ms',
      trendLabel: 'faster'
    },
    {
      title: 'Conversations',
      value: data?.total_conversations ?? 0,
      subtitle: 'Total sessions',
      icon: Users,
      gradient: 'from-cyan-500 to-cyan-700',
      shadowColor: 'shadow-cyan-500/25',
      trend: '+8',
      trendLabel: 'today'
    },
    {
      title: 'Active Tools',
      value: data?.active_tools ?? 0,
      subtitle: 'Ready to use',
      icon: Zap,
      gradient: 'from-rose-500 to-rose-700',
      shadowColor: 'shadow-rose-500/25',
      trend: '100%',
      trendLabel: 'uptime'
    }
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map((card, index) => (
        <div 
          key={index}
          className={cn(
            "relative overflow-hidden rounded-2xl p-5 text-white stats-card",
            "bg-gradient-to-br",
            card.gradient,
            "shadow-lg",
            card.shadowColor,
            "transition-all duration-300 hover:scale-[1.02] hover:shadow-xl",
            "animate-fadeIn",
            `stagger-${index + 1}`
          )}
          style={{ opacity: 0 }}
        >
          {/* Background Pattern */}
          <div className="absolute top-0 right-0 w-24 h-24 transform translate-x-8 -translate-y-8">
            <div className="w-full h-full rounded-full bg-white/10" />
          </div>
          <div className="absolute bottom-0 left-0 w-16 h-16 transform -translate-x-6 translate-y-6">
            <div className="w-full h-full rounded-full bg-white/5" />
          </div>
          
          {/* Content */}
          <div className="relative">
            <div className="flex items-start justify-between mb-3">
              <div className="p-2 rounded-xl bg-white/20 backdrop-blur-sm">
                <card.icon className="w-5 h-5" />
              </div>
              <div className="flex items-center gap-1 text-xs font-medium bg-white/20 px-2 py-1 rounded-full backdrop-blur-sm">
                <TrendingUp className="w-3 h-3" />
                {card.trend}
              </div>
            </div>
            
            <div className="mt-4">
              <p className="text-3xl font-bold tracking-tight">{card.value}</p>
              <p className="text-sm font-medium text-white/90 mt-1">{card.title}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-white/70">{card.subtitle}</span>
                <span className="text-xs text-white/50">·</span>
                <span className="text-xs text-white/70">{card.trendLabel}</span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
