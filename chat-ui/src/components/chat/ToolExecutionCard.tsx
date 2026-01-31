import { useState } from 'react'
import { ToolCall } from '@/stores/chatStore'
import { Wrench, ChevronDown, ChevronUp, CheckCircle, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ToolExecutionCardProps {
  toolCall: ToolCall
}

export function ToolExecutionCard({ toolCall }: ToolExecutionCardProps) {
  const [expanded, setExpanded] = useState(false)

  const toolDisplayNames: Record<string, string> = {
    'resolve_customer': 'Resolving Customer',
    'resolve_vehicle': 'Looking Up Vehicle',
    'get_nearby_dealers': 'Finding Nearby Dealers',
    'get_available_slots': 'Checking Available Slots',
    'create_service_booking': 'Creating Booking',
    'get_booking_status': 'Fetching Booking Status'
  }

  const displayName = toolDisplayNames[toolCall.name] || toolCall.name

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-100 transition-colors"
      >
        <div className="flex-shrink-0 w-8 h-8 bg-msil-blue/10 rounded-lg flex items-center justify-center">
          <Wrench className="w-4 h-4 text-msil-blue" />
        </div>
        <div className="flex-1 text-left">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-800">{displayName}</span>
            {toolCall.result ? (
              <CheckCircle className="w-4 h-4 text-green-500" />
            ) : (
              <Clock className="w-4 h-4 text-yellow-500 animate-pulse" />
            )}
          </div>
          <span className="text-xs text-gray-500">
            {toolCall.result?.execution_time_ms 
              ? `Completed in ${toolCall.result.execution_time_ms}ms`
              : 'Executing...'}
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-200">
          <div className="mt-3 space-y-3">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase mb-1">Input</p>
              <pre className="text-xs bg-white p-2 rounded border border-gray-200 overflow-x-auto">
                {JSON.stringify(toolCall.arguments, null, 2)}
              </pre>
            </div>
            {toolCall.result && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase mb-1">Output</p>
                <pre className={cn(
                  "text-xs p-2 rounded border overflow-x-auto max-h-48",
                  toolCall.result.success 
                    ? "bg-green-50 border-green-200" 
                    : "bg-red-50 border-red-200"
                )}>
                  {JSON.stringify(toolCall.result.data || toolCall.result.error, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
