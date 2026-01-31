import { useEffect, useRef } from 'react'
import { MessageList } from './MessageList'
import { InputArea } from './InputArea'
import { useChatStore } from '@/stores/chatStore'

export function ChatContainer() {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages } = useChatStore()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 ? (
          <WelcomeMessage />
        ) : (
          <MessageList messages={messages} />
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t bg-white px-4 py-4">
        <InputArea />
      </div>
    </div>
  )
}

function WelcomeMessage() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      <div className="bg-msil-blue text-white p-4 rounded-full mb-6">
        <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} 
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </div>
      <h2 className="text-2xl font-bold text-gray-800 mb-2">
        Welcome to MSIL Service Assistant
      </h2>
      <p className="text-gray-600 max-w-md mb-8">
        I can help you book car service appointments, find nearby dealers, 
        and check your booking status. How can I assist you today?
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
        <SuggestionCard 
          icon="🚗"
          title="Book Service"
          description="Book a service appointment for your vehicle"
        />
        <SuggestionCard 
          icon="📍"
          title="Find Dealers"
          description="Locate nearby Maruti Suzuki service centers"
        />
        <SuggestionCard 
          icon="📋"
          title="Check Booking"
          description="View status of your existing booking"
        />
        <SuggestionCard 
          icon="❓"
          title="Get Help"
          description="Ask any questions about car service"
        />
      </div>
    </div>
  )
}

function SuggestionCard({ icon, title, description }: { icon: string; title: string; description: string }) {
  const { sendMessage } = useChatStore()

  const handleClick = () => {
    const prompts: Record<string, string> = {
      'Book Service': 'I want to book a car service appointment',
      'Find Dealers': 'Find nearby Maruti Suzuki dealers in Pune',
      'Check Booking': 'I want to check my booking status',
      'Get Help': 'What services do you offer?'
    }
    sendMessage(prompts[title] || title)
  }

  return (
    <button 
      onClick={handleClick}
      className="flex items-start gap-3 p-4 bg-white border border-gray-200 rounded-xl hover:border-msil-blue hover:shadow-md transition-all text-left"
    >
      <span className="text-2xl">{icon}</span>
      <div>
        <h3 className="font-semibold text-gray-800">{title}</h3>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
    </button>
  )
}
