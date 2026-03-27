import { ref, onUnmounted } from 'vue'
import { getSocketManager } from '../utils/socket'
import { useMessageStore } from '../pinia/modules/message'

/**
 * WebSocket业务调度员
 * 负责处理具体的业务逻辑，决定什么时候发什么消息
 * @param url WebSocket服务地址
 * @returns WebSocket操作方法和状态
 */
export function useSocket(url: string) {
  const socketManager = getSocketManager(url)
  const messageStore = useMessageStore()

  // 使用响应式状态
  const connected = ref(socketManager.connected)
  const authenticated = ref(socketManager.authenticated)

  /**
   * 连接WebSocket服务器
   */
  const connect = () => {
    socketManager.connect()
  }

  /**
   * 发送原始消息
   * @param data 要发送的数据
   */
  const send = (data: any) => {
    socketManager.send(data)
  }

  /**
   * 注册消息处理器
   * @param handler 消息处理函数
   */
  const onMessage = (handler: (data: any) => void) => {
    socketManager.onMessage(handler)
  }

  /**
   * 移除消息处理器
   * @param handler 要移除的消息处理函数
   */
  const offMessage = (handler: (data: any) => void) => {
    socketManager.offMessage(handler)
  }

  /**
   * 断开WebSocket连接
   */
  const disconnect = () => {
    socketManager.disconnect()
  }

  /**
   * 重新连接WebSocket
   */
  const reconnect = () => {
    socketManager.reconnect()
  }

  /**
   * 发送聊天消息
   * @param question 用户问题
   * @param useContext 是否使用上下文
   * @param conversationId 会话ID
   */
  const sendMessage = (question: string, useContext: boolean, conversationId: number | null) => {
    send({
      question,
      use_context: useContext,
      conversation_id: conversationId,
    })
  }

  /**
   * 处理WebSocket消息
   * 根据消息类型更新状态管理器
   * @param data 接收到的消息数据
   */
  const handleMessage = (data: any) => {
    if (data.type === 'auth_success') {
      messageStore.setConnected(true)
      messageStore.setAuthenticated(true)
      authenticated.value = true
      connected.value = true
    } else if (data.type === 'auth_failed') {
      messageStore.setConnected(false)
      messageStore.setAuthenticated(false)
      authenticated.value = false
      connected.value = false
    } else if (data.type === 'conversation_id') {
      messageStore.setConversationId(data.conversation_id)
    } else if (data.chunk) {
      messageStore.appendChunk(data.chunk)
    } else if (data.done) {
      messageStore.setStreaming(false)
      if (data.sources) {
        messageStore.setSources(data.sources)
      }
      if (data.error) {
        messageStore.setError(data.error)
      }
    } else if (data.error) {
      messageStore.setError(data.error)
    }
  }

  onMessage(handleMessage)

  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    authenticated,
    connect,
    send,
    sendMessage,
    onMessage,
    offMessage,
    disconnect,
    reconnect,
  }
}
