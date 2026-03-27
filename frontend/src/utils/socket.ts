import { useUserStore } from '../pinia/modules/user'
import { ElMessage } from 'element-plus'

/** WebSocket消息处理函数类型 */
type MessageHandler = (data: any) => void

/**
 * WebSocket管理器类
 * 负责WebSocket连接、认证、重连和消息处理
 */
class SocketManager {
  /** WebSocket实例 */
  private socket: WebSocket | null = null
  /** 是否已连接 */
  private isConnected = false
  /** 是否已认证 */
  private isAuthenticated = false
  /** 消息处理器集合 */
  private messageHandlers = new Set<MessageHandler>()
  /** 重连定时器 */
  private reconnectTimer: number | null = null
  /** 重连间隔(毫秒) */
  private reconnectInterval = 3000
  /** 最大重连尝试次数 */
  private maxReconnectAttempts = 5
  /** 当前重连尝试次数 */
  private reconnectAttempts = 0
  /** 认证是否失败 */
  private authFailed = false
  /** WebSocket服务地址 */
  private url: string

  constructor(url: string) {
    this.url = url
  }

  /**
   * 连接WebSocket服务器
   */
  connect() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return
    }
    if (this.authFailed) return

    const ws = new WebSocket(this.url)
    this.socket = ws

    ws.onopen = () => {
      console.log('WebSocket connected, sending auth...')
      this.isConnected = true
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
          this.isAuthenticated = true
          this.reconnectAttempts = 0
          console.log('WebSocket authenticated')
          return
        } else if (data.type === 'auth_failed') {
          this.isAuthenticated = false
          this.authFailed = true
          console.error('WebSocket auth failed:', data.reason)
          
          // 检查是否是token过期
          if (data.reason && data.reason.includes('expired')) {
            ElMessage.error('登录已过期，请重新登录')
            const userStore = useUserStore()
            userStore.clearToken()
            // 跳转到登录页
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
      this.isConnected = false
      this.isAuthenticated = false
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

  /**
   * 发送消息
   * @param data 要发送的数据
   */
  send(data: any) {
    if (this.socket && this.isConnected && this.isAuthenticated) {
      this.socket.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket not ready or not authenticated', {
        connected: this.isConnected,
        authenticated: this.isAuthenticated,
      })
    }
  }

  /**
   * 注册消息处理器
   * @param handler 消息处理函数
   */
  onMessage(handler: MessageHandler) {
    this.messageHandlers.add(handler)
  }

  /**
   * 移除消息处理器
   * @param handler 要移除的消息处理函数
   */
  offMessage(handler: MessageHandler) {
    this.messageHandlers.delete(handler)
  }

  /**
   * 重新连接WebSocket
   */
  reconnect() {
    this.authFailed = false
    this.reconnectAttempts = 0
    this.disconnect()
    this.connect()
  }

  /**
   * 断开WebSocket连接
   */
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

  /** 获取连接状态 */
  get connected() {
    return this.isConnected
  }

  /** 获取认证状态 */
  get authenticated() {
    return this.isAuthenticated
  }
}

/** SocketManager单例实例 */
let socketManagerInstance: SocketManager | null = null

/**
 * 获取SocketManager单例
 * @param url WebSocket服务地址
 * @returns SocketManager实例
 */
export function getSocketManager(url: string) {
  if (!socketManagerInstance) {
    socketManagerInstance = new SocketManager(url)
  }
  return socketManagerInstance
}
