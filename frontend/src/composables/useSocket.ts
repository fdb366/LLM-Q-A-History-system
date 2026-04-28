import { ref, onUnmounted } from 'vue'
import { getSocketManager } from '../utils/socket'
import { useMessageStore } from '../pinia/modules/message'

export function useSocket(url: string) {
  const socketManager = getSocketManager(url)
  const messageStore = useMessageStore()

  const connected = socketManager.connected
  const authenticated = socketManager.authenticated

  const connect = () => {
    socketManager.connect()
  }

  const send = (data: any) => {
    socketManager.send(data)
  }

  const onMessage = (handler: (data: any) => void) => {
    socketManager.onMessage(handler)
  }

  const offMessage = (handler: (data: any) => void) => {
    socketManager.offMessage(handler)
  }

  const disconnect = () => {
    socketManager.disconnect()
  }

  const reconnect = () => {
    socketManager.reconnect()
  }

  const sendMessage = (question: string, useContext: boolean, conversationId: number | null) => {
    send({
      question,
      use_context: useContext,
      conversation_id: conversationId,
    })
  }

  const handleMessage = (data: any) => {
    if (data.type === 'auth_success') {
      messageStore.setConnected(true)
      messageStore.setAuthenticated(true)
    } else if (data.type === 'auth_failed') {
      messageStore.setConnected(false)
      messageStore.setAuthenticated(false)
    } else if (data.type === 'conversation_id') {
      messageStore.setConversationId(data.conversation_id)
    } else if (data.chunk) {
      messageStore.setChunk(data.chunk)
    } else if (data.done) {
      messageStore.setStreaming(false)
      if (data.sources) {
        messageStore.setSources(data.sources)
      }
      if (data.error) {
        messageStore.setError(data.error)
      }
      if (data.conversation_title) {
        messageStore.setConversationTitle(data.conversation_title)
      }
    } else if (data.error) {
      messageStore.setError(data.error)
    }
  }

  onMessage(handleMessage)

  onUnmounted(() => {
    offMessage(handleMessage)
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
