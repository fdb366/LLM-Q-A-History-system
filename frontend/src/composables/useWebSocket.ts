// src/composables/useWebSocket.ts
import { ref, onUnmounted } from 'vue'
import { useUserStore } from '../pinia/modules/user'
import { ElMessage } from 'element-plus'

type MessageHandler = (data: any) => void

export function useWebSocket(url: string) {
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const isAuthenticated = ref(false)
  const messageHandlers = new Set<MessageHandler>()
  let reconnectTimer: number | null = null
  let reconnectInterval = 3000
  let maxReconnectAttempts = 5
  let reconnectAttempts = 0
  let authFailed = false  // 认证永久失败时停止重连

  const userStore = useUserStore()

  const connect = () => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      return
    }
    if (authFailed) return

    const ws = new WebSocket(url)
    socket.value = ws

    ws.onopen = () => {
      console.log('WebSocket connected, sending auth...')
      isConnected.value = true
      // 发送认证消息
      const token = userStore.token
      if (token) {
        ws.send(JSON.stringify({ type: 'auth', token }))
      } else {
        console.warn('No token available for WebSocket auth')
        ws.close()
      }
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        // 处理认证响应
        if (data.type === 'auth_success') {
          isAuthenticated.value = true
          reconnectAttempts = 0  // 重置重连计数
          console.log('WebSocket authenticated')
          return
        } else if (data.type === 'auth_failed') {
          isAuthenticated.value = false
          authFailed = true  // 标记认证失败，不再重连
          console.error('WebSocket auth failed:', data.reason)
          ElMessage.error(`WebSocket认证失败: ${data.reason || '请重新登录'}`)
          ws.close()
          return
        }
        // 正常消息分发
        messageHandlers.forEach(handler => handler(data))
      } catch (e) {
        console.error('Failed to parse WebSocket message', e)
      }
    }

    ws.onclose = () => {
      isConnected.value = false
      isAuthenticated.value = false
      console.log('WebSocket disconnected')
      // 认证失败或超过重连次数则不再重连
      if (!authFailed && reconnectAttempts < maxReconnectAttempts) {
        reconnectTimer = setTimeout(() => {
          reconnectAttempts++
          console.log(`WebSocket reconnecting (${reconnectAttempts}/${maxReconnectAttempts})...`)
          connect()
        }, reconnectInterval) as any
      }
    }

    ws.onerror = (err) => {
      console.error('WebSocket error', err)
    }
  }

  const send = (data: any) => {
    if (socket.value && isConnected.value && isAuthenticated.value) {
      socket.value.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket not ready or not authenticated', {
        connected: isConnected.value,
        authenticated: isAuthenticated.value,
      })
    }
  }

  // 手动重连（重置认证失败状态）
  const reconnect = () => {
    authFailed = false
    reconnectAttempts = 0
    disconnect()
    connect()
  }

  const onMessage = (handler: MessageHandler) => {
    messageHandlers.add(handler)
  }

  const offMessage = (handler: MessageHandler) => {
    messageHandlers.delete(handler)
  }

  const disconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    isAuthenticated,
    send,
    onMessage,
    offMessage,
    disconnect,
    reconnect,
    connect,
  }
}
