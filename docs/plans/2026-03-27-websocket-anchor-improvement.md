# WebSocket连接与锚点联动功能改进实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复WebSocket连接失败问题，实现锚点与消息的双向联动功能

**Architecture:** 
1. WebSocket连接模块：优化连接管理、错误处理和重连机制
2. 锚点联动模块：实现消息与锚点的双向滚动联动

**Tech Stack:** Vue 3, TypeScript, Pinia, Element Plus, WebSocket

---

## 问题分析

### 问题1: WebSocket连接失败
**原因分析:**
1. SocketManager使用单例模式，但状态不是响应式的
2. connected和authenticated状态在组件中无法正确更新
3. 缺少连接状态的实时同步机制

### 问题2: 锚点与消息联动
**原因分析:**
1. ChatMessage组件缺少id属性，无法与锚点关联
2. 没有实现滚动监听，无法自动选中当前可见消息对应的锚点
3. 点击锚点时没有平滑滚动到对应消息

---

## Task 1: 修复WebSocket连接状态响应式问题

**Files:**
- Modify: `d:\桌面\LLM_project\frontend\src\utils\socket.ts:1-191`
- Modify: `d:\桌面\LLM_project\frontend\src\composables\useSocket.ts:1-128`

**Step 1: 修改SocketManager类，使用响应式状态**

修改 `d:\桌面\LLM_project\frontend\src\utils\socket.ts`:

```typescript
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
```

**Step 2: 验证修改**

运行前端开发服务器，检查WebSocket连接是否正常。

---

## Task 2: 为ChatMessage组件添加id属性

**Files:**
- Modify: `d:\桌面\LLM_project\frontend\src\views\ChatView.vue:1-291`

**Step 1: 修改ChatMessage组件，添加id属性**

修改 `d:\桌面\LLM_project\frontend\src\views\ChatView.vue`:

```vue
<template>
  <div class="chat-view">
    <AnchorSidebar />
    <div class="main-area">
      <div class="message-list" ref="messageListRef" :key="forceRenderKey.value">
        <ChatMessage
          v-for="msg in messages"
          :key="msg.id"
          :id="`msg-${msg.id}`"
          :role="msg.role"
          :content="msg.content"
          :typing="msg.role === 'assistant' && msg.streaming"
          :thinking="msg.thinking"
          :summary="msg.summary"
          :isThinkingExpanded="msg.isThinkingExpanded"
          @toggleThinking="() => toggleThinking(msg.id)"
        />
        <div v-if="loading" class="loading-message">
          <ChatMessage role="assistant" content="" typing />
        </div>
      </div>
      <ChatInput @send="handleSend" :loading="loading" />
    </div>
    <Sidebar :container="messageListRef" v-if="messages.length" />
  </div>
</template>
```

**Step 2: 验证修改**

检查消息元素是否有正确的id属性。

---

## Task 3: 实现锚点与消息的双向联动

**Files:**
- Modify: `d:\桌面\LLM_project\frontend\src\views\ChatView.vue:1-291`
- Modify: `d:\桌面\LLM_project\frontend\src\components\AnchorSidebar.vue:1-102`

**Step 1: 在ChatView中添加滚动监听**

修改 `d:\桌面\LLM_project\frontend\src\views\ChatView.vue`:

```typescript
// 添加当前激活的消息ID
const activeMessageId = ref<string | null>(null)

// 监听滚动，更新当前激活的消息
const handleScroll = () => {
  if (!messageListRef.value) return
  
  const container = messageListRef.value
  const scrollTop = container.scrollTop
  const containerHeight = container.clientHeight
  
  // 获取所有消息元素
  const messageElements = container.querySelectorAll('[id^="msg-"]')
  
  for (let i = 0; i < messageElements.length; i++) {
    const element = messageElements[i] as HTMLElement
    const rect = element.getBoundingClientRect()
    const containerRect = container.getBoundingClientRect()
    
    // 判断元素是否在可视区域内
    if (rect.top >= containerRect.top && rect.top <= containerRect.top + containerHeight / 2) {
      const id = element.id.replace('msg-', '')
      activeMessageId.value = id
      break
    }
  }
}

// 添加滚动监听
onMounted(() => {
  if (messageListRef.value) {
    messageListRef.value.addEventListener('scroll', handleScroll)
  }
})

// 移除滚动监听
onUnmounted(() => {
  if (messageListRef.value) {
    messageListRef.value.removeEventListener('scroll', handleScroll)
  }
})
```

**Step 2: 修改AnchorSidebar组件，支持激活状态**

修改 `d:\桌面\LLM_project\frontend\src\components\AnchorSidebar.vue`:

```vue
<template>
  <aside class="anchor-sidebar scrollbar-thin" v-show="anchorItems.length">
    <div class="anchor-content">
      <el-anchor :container="container" scroll-offset="80" direction="vertical">
        <el-anchor-link
          v-for="item in anchorItems"
          :key="item.id"
          :href="`#msg-${item.id}`"
          :class="{ 'is-active': activeMessageId === item.id }"
          @click="handleAnchorClick(item.id)"
        >
          <el-tooltip :content="item.fullTitle" placement="left" :show-after="300">
            <span class="anchor-title">{{ item.shortTitle }}</span>
          </el-tooltip>
        </el-anchor-link>
      </el-anchor>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, inject, type Ref } from 'vue'
import { ElAnchor, ElAnchorLink, ElTooltip } from 'element-plus'
import { useChatStore } from '../pinia/modules/chat'

const props = defineProps<{
  container?: HTMLElement
}>()

const chatStore = useChatStore()
const messages = computed(() => chatStore.messages)

// 注入当前激活的消息ID
const activeMessageId = inject<Ref<string | null>>('activeMessageId')

const anchorItems = computed(() => {
  return messages.value
    .filter(msg => msg.role === 'user')
    .map(msg => {
      const fullTitle = msg.content
      const shortTitle = fullTitle.length > 12 ? fullTitle.slice(0, 12) + '…' : fullTitle
      return {
        id: msg.id,
        fullTitle,
        shortTitle,
      }
    })
})

// 处理锚点点击
const handleAnchorClick = (id: string) => {
  const element = document.getElementById(`msg-${id}`)
  if (element && props.container) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
</script>
```

**Step 3: 在ChatView中提供activeMessageId**

修改 `d:\桌面\LLM_project\frontend\src\views\ChatView.vue`:

```typescript
// 提供activeMessageId给子组件
provide('activeMessageId', activeMessageId)
```

**Step 4: 验证修改**

测试锚点与消息的双向联动功能。

---

## Task 4: 优化WebSocket连接初始化

**Files:**
- Modify: `d:\桌面\LLM_project\frontend\src\views\ChatView.vue:1-291`

**Step 1: 在组件挂载时初始化WebSocket连接**

修改 `d:\桌面\LLM_project\frontend\src\views\ChatView.vue`:

```typescript
// 组件挂载时初始化WebSocket连接
onMounted(() => {
  if (!connected.value) {
    connect()
  }
})
```

**Step 2: 验证修改**

检查WebSocket连接是否在组件挂载时自动建立。

---

## Task 5: 添加连接状态提示

**Files:**
- Modify: `d:\桌面\LLM_project\frontend\src\views\ChatView.vue:1-291`

**Step 1: 添加连接状态提示**

修改 `d:\桌面\LLM_project\frontend\src\views\ChatView.vue`:

```vue
<template>
  <div class="chat-view">
    <AnchorSidebar />
    <div class="main-area">
      <!-- 添加连接状态提示 -->
      <div v-if="!connected || !authenticated" class="connection-status">
        <el-tag :type="connected ? 'success' : 'danger'" size="small">
          {{ connected ? (authenticated ? '已连接' : '认证中...') : '连接中...' }}
        </el-tag>
      </div>
      <div class="message-list" ref="messageListRef" :key="forceRenderKey.value">
        <!-- ... -->
      </div>
      <ChatInput @send="handleSend" :loading="loading" />
    </div>
    <Sidebar :container="messageListRef" v-if="messages.length" />
  </div>
</template>

<style scoped lang="scss">
.connection-status {
  padding: 8px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: center;
}
</style>
```

**Step 2: 验证修改**

检查连接状态提示是否正确显示。

---

## Task 6: 提交代码

**Step 1: 添加修改的文件**

```bash
git add frontend/src/utils/socket.ts
git add frontend/src/composables/useSocket.ts
git add frontend/src/views/ChatView.vue
git add frontend/src/components/AnchorSidebar.vue
```

**Step 2: 提交更改**

```bash
git commit -m "feat: 修复WebSocket连接问题并实现锚点联动功能

- 修复WebSocket连接状态响应式问题
- 为ChatMessage组件添加id属性
- 实现锚点与消息的双向联动
- 优化WebSocket连接初始化
- 添加连接状态提示"
```

---

## 测试清单

1. **WebSocket连接测试**
   - [ ] 页面加载时WebSocket自动连接
   - [ ] 连接状态正确显示
   - [ ] 认证成功后可以发送消息
   - [ ] Token过期时自动跳转登录页

2. **锚点联动测试**
   - [ ] 发送新消息时自动选中对应锚点
   - [ ] 点击锚点时平滑滚动到对应消息
   - [ ] 滚动消息列表时自动更新锚点激活状态

3. **流式输出测试**
   - [ ] 消息流式输出正常
   - [ ] 思考内容正确解析
   - [ ] 消息保存到数据库
