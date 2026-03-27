import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  streaming?: boolean
  sources?: any[]
  thinking?: string // 思考内容
  summary?: string // 总结内容
  isThinkingExpanded?: boolean // 思考内容是否展开
}

export interface Session {
  id: number
  title: string
  created_at: string
  updated_at: string
  tempId?: string // 临时会话ID
}

export const useChatStore = defineStore('chat', () => {
  // 当前会话的消息列表
  const messages = ref<Message[]>([])
  // 当前会话ID（后端返回的是 number，转为字符串方便比较）
  const currentSessionId = ref<string | null>(null)
  // 会话列表
  const sessions = ref<Session[]>([])
  // 加载状态
  const loading = ref(false)

  // ========== 会话相关 ==========
  const setSessions = (newSessions: Session[]) => {
    sessions.value = newSessions
  }

  const addSession = (session: Session) => {
    sessions.value.unshift(session)
  }

  const updateSession = (id: number, updater: (s: Session) => void) => {
    const idx = sessions.value.findIndex(s => s.id === id)
    if (idx !== -1) updater(sessions.value[idx])
  }

  const removeSession = (id: number) => {
    sessions.value = sessions.value.filter(s => s.id !== id)
  }

  const setCurrentSession = (id: string | number | null) => {
    if (id === null) {
      currentSessionId.value = null
    } else {
      currentSessionId.value = String(id)
    }
  }

  // ========== 消息相关 ==========
  const addMessage = (message: Message) => {
    messages.value.push(message)
  }

  const updateMessage = (id: string, updater: (msg: Message) => void) => {
    const msg = messages.value.find(m => m.id === id)
    if (msg) updater(msg)
  }

  const clearMessages = () => {
    messages.value = []
  }

  const setMessages = (msgs: Message[]) => {
    messages.value = msgs
  }

  const setLoading = (value: boolean) => {
    loading.value = value
  }

  return {
    messages,
    currentSessionId,
    sessions,
    loading,
    setSessions,
    addSession,
    updateSession,
    removeSession,
    setCurrentSession,
    addMessage,
    updateMessage,
    clearMessages,
    setMessages,
    setLoading,
  }
})