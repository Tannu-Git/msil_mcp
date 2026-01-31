import { Message } from '@/stores/chatStore'
import { MessageBubble } from './MessageBubble'
import { ToolExecutionCard } from './ToolExecutionCard'

interface MessageListProps {
  messages: Message[]
}

export function MessageList({ messages }: MessageListProps) {
  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <div key={message.id} className="animate-fade-in">
          <MessageBubble message={message} />
          {message.toolCalls && message.toolCalls.length > 0 && (
            <div className="mt-2 ml-12 space-y-2">
              {message.toolCalls.map((toolCall, index) => (
                <ToolExecutionCard 
                  key={index}
                  toolCall={toolCall}
                />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
