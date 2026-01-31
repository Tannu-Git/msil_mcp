import { create } from 'zustand'
import { sendChatMessage } from '@/lib/api'

export interface ToolCall {
  name: string
  arguments: Record<string, unknown>
  result?: {
    success: boolean
    data?: unknown
    error?: string
    execution_time_ms?: number
  }
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  toolCalls?: ToolCall[]
  timestamp: Date
}

interface ChatState {
  messages: Message[]
  isLoading: boolean
  sessionId: string | null
  error: string | null
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => string
  updateMessage: (id: string, updates: Partial<Message>) => void
  sendMessage: (content: string) => Promise<void>
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  sessionId: null,
  error: null,

  addMessage: (message) => {
    const id = crypto.randomUUID()
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id,
          timestamp: new Date()
        }
      ]
    }))
    return id
  },

  updateMessage: (id, updates) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      )
    }))
  },

  sendMessage: async (content) => {
    const { addMessage, updateMessage, messages, sessionId } = get()

    // Add user message
    addMessage({
      role: 'user',
      content
    })

    // Add placeholder assistant message
    const assistantId = addMessage({
      role: 'assistant',
      content: ''
    })

    set({ isLoading: true, error: null })

    try {
      // Build history for API
      const history = messages.map((msg) => ({
        role: msg.role,
        content: msg.content
      }))

      // Send to API
      const response = await sendChatMessage(content, sessionId, history)

      // Update assistant message with response
      updateMessage(assistantId, {
        content: response.message,
        toolCalls: response.tool_results?.map((tr: { tool_name: string; arguments: Record<string, unknown>; result: unknown }) => ({
          name: tr.tool_name,
          arguments: tr.arguments,
          result: tr.result
        }))
      })

      set({ sessionId: response.session_id })
    } catch (error) {
      console.error('Chat error:', error)
      updateMessage(assistantId, {
        content: 'Sorry, I encountered an error. Please try again.'
      })
      set({ error: error instanceof Error ? error.message : 'Unknown error' })
    } finally {
      set({ isLoading: false })
    }
  },

  clearMessages: () => {
    set({ messages: [], sessionId: null, error: null })
  }
}))
