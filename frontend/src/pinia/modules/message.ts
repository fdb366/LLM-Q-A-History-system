import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * WebSocket消息状态管理器
 * 负责记录和管理WebSocket相关的状态数据
 */
export const useMessageStore = defineStore('message', () => {
  /** WebSocket是否已连接 */
  const connected = ref(false)
  /** WebSocket是否已认证 */
  const authenticated = ref(false)
  /** 是否正在流式接收消息 */
  const streaming = ref(false)
  /** 当前接收到的消息片段 */
  const currentChunk = ref('')
  /** 消息来源文档列表 */
  const sources = ref<any[]>([])
  /** 错误信息 */
  const error = ref<string | null>(null)
  /** 当前会话ID */
  const conversationId = ref<number | null>(null)

  /**
   * 设置连接状态
   * @param value 是否已连接
   */
  const setConnected = (value: boolean) => {
    connected.value = value
  }

  /**
   * 设置认证状态
   * @param value 是否已认证
   */
  const setAuthenticated = (value: boolean) => {
    authenticated.value = value
  }

  /**
   * 设置流式接收状态
   * @param value 是否正在流式接收
   */
  const setStreaming = (value: boolean) => {
    streaming.value = value
  }

  /**
   * 追加消息片段
   * @param chunk 要追加的消息片段
   */
  const appendChunk = (chunk: string) => {
    currentChunk.value += chunk
  }

  /**
   * 清空当前消息片段
   */
  const clearChunk = () => {
    currentChunk.value = ''
  }

  /**
   * 设置消息来源文档
   * @param newSources 来源文档列表
   */
  const setSources = (newSources: any[]) => {
    sources.value = newSources
  }

  /**
   * 设置错误信息
   * @param err 错误信息
   */
  const setError = (err: string | null) => {
    error.value = err
  }

  /**
   * 设置会话ID
   * @param id 会话ID
   */
  const setConversationId = (id: number) => {
    conversationId.value = id
  }

  /**
   * 重置所有状态
   */
  const reset = () => {
    connected.value = false
    authenticated.value = false
    streaming.value = false
    currentChunk.value = ''
    sources.value = []
    error.value = null
    conversationId.value = null
  }

  return {
    connected,
    authenticated,
    streaming,
    currentChunk,
    sources,
    error,
    conversationId,
    setConnected,
    setAuthenticated,
    setStreaming,
    appendChunk,
    clearChunk,
    setSources,
    setError,
    setConversationId,
    reset,
  }
})
