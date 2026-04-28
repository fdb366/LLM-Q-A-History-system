import { useUserStore } from '../pinia/modules/user'
import { ElMessage } from 'element-plus'
import { ref, type Ref } from 'vue'

type MessageHandler = (data: any) => void

class SocketManager {
  private socket: WebSocket | null = null
  private messageHandlers = new Set<MessageHandler>()
  private reconnectTimer: number | null = null
  private reconnectInterval = 3000
  private maxReconnectAttempts = 5
  private reconnectAttempts = 0
  private authFailed = false
  private url: string
  
  public isConnected: Ref<boolean> = ref(false)
  public isAuthenticated: Ref<boolean> = ref(false)

  constructor(url: string) {
    this.url = url
  }

  connect() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return
    }
    if (this.authFailed) return

    const ws = new WebSocket(this.url)
    this.socket = ws

    ws.onopen = () => {
      console.log('WebSocket connected, sending auth...')
      this.isConnected.value = true
      const userStore = useUserStore()
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
        if (data.type === 'auth_success') {
          this.isAuthenticated.value = true
          this.reconnectAttempts = 0
          console.log('WebSocket authenticated')
          return
        } else if (data.type === 'auth_failed') {
          this.isAuthenticated.value = false
          this.authFailed = true
          console.error('WebSocket auth failed:', data.reason)
          
          if (data.reason && data.reason.includes('expired')) {
            ElMessage.error('登录已过期，请重新登录')
            const userStore = useUserStore()
            userStore.clearToken()
            window.location.href = '/login'
          } else {
            ElMessage.error(`WebSocket认证失败: ${data.reason || '请重新登录'}`)
          }
          ws.close()
          return
        }
        this.messageHandlers.forEach(handler => handler(data))
      } catch (e) {
        console.error('Failed to parse WebSocket message', e)
      }
    }

    ws.onclose = () => {
      this.isConnected.value = false
      this.isAuthenticated.value = false
      console.log('WebSocket disconnected')
      if (!this.authFailed && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectTimer = setTimeout(() => {
          this.reconnectAttempts++
          console.log(`WebSocket reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
          this.connect()
        }, this.reconnectInterval) as any
      }
    }

    ws.onerror = (err) => {
      console.error('WebSocket error', err)
    }
  }

  send(data: any) {
    if (this.socket && this.isConnected.value && this.isAuthenticated.value) {
      this.socket.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket not ready or not authenticated', {
        connected: this.isConnected.value,
        authenticated: this.isAuthenticated.value,
      })
    }
  }

  onMessage(handler: MessageHandler) {
    this.messageHandlers.add(handler)
  }

  offMessage(handler: MessageHandler) {
    this.messageHandlers.delete(handler)
  }

  reconnect() {
    this.authFailed = false
    this.reconnectAttempts = 0
    this.disconnect()
    this.connect()
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
  }

  get connected() {
    return this.isConnected
  }

  get authenticated() {
    return this.isAuthenticated
  }
}

let socketManagerInstance: SocketManager | null = null

export function getSocketManager(url: string) {
  if (!socketManagerInstance) {
    socketManagerInstance = new SocketManager(url)
  }
  return socketManagerInstance
}
