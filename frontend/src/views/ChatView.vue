<template>
  <div class="chat-view">
    <!-- 左侧会话列表 -->
    <AnchorSidebar />
    <div class="main-area">
      <div class="message-list" ref="messageListRef" :key="forceRenderKey.value">
  <ChatMessage
          v-for="msg in messages"
          :key="msg.id"
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

<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { useChatStore } from '../pinia/modules/chat'
import { useMessageStore } from '../pinia/modules/message'
import { useSocket } from '../composables/useSocket'
import { conversationApi } from '../api/conversation'
import { ElMessage } from 'element-plus'
import { v4 as uuidv4 } from 'uuid'

const chatStore = useChatStore()
const messageStore = useMessageStore()

// 消息列表（从 chat store 获取）
const messages = computed(() => chatStore.messages)
// 加载状态
const loading = ref(false)

// 消息列表 DOM 引用
const messageListRef = ref<HTMLElement>()

// 强制重新渲染的 key
const forceRenderKey = ref(0)
watch(messages, () => {
  forceRenderKey.value++
}, { deep: true })

// WebSocket 连接配置
const WS_URL =  'ws://localhost:8000/ws/chat'
const { connect, sendMessage, authenticated, connected, reconnect } = useSocket(WS_URL)

// 当前助手消息 ID
let currentAssistantId: string | null = null
// 超时定时器
let timeoutId: number | null = null

// 监听消息片段变化（实现流式输出）
watch(() => messageStore.currentChunk, (newChunk) => {
  if (!currentAssistantId && newChunk) {
    // 创建新的助手消息
    currentAssistantId = uuidv4()
    chatStore.addMessage({
      id: currentAssistantId,
      role: 'assistant',
      content: newChunk,
      timestamp: Date.now(),
      streaming: true,
      thinking: '',
      summary: '',
      isThinkingExpanded: false
    })
  } else if (currentAssistantId) {
    // 追加消息内容（实现流式效果）
    chatStore.updateMessage(currentAssistantId, (msg) => {
      msg.content += newChunk
    })
  }
})

// 监听流式状态变化
watch(() => messageStore.streaming, (isStreaming) => {
  if (!isStreaming && currentAssistantId) {
    // 流式结束，处理消息内容
    chatStore.updateMessage(currentAssistantId, (msg) => {
      msg.streaming = false
      if (messageStore.sources.length > 0) {
        msg.sources = messageStore.sources
      }
      
      // 解析思考内容和总结内容
      const content = msg.content
      const thinkTag = '<think>'
      const thinkTagEnd = '</think>'
      const thinkingMatch = content.match(new RegExp(`${thinkTag}(.*?)${thinkTagEnd}`, 's'))
      
      if (thinkingMatch) {
        msg.thinking = thinkingMatch[1].trim()
        msg.summary = content.replace(new RegExp(`${thinkTag}.*?${thinkTagEnd}`, 's'), '').trim()
        msg.isThinkingExpanded = false
      } else {
        msg.summary = content.trim()
      }
    })
    currentAssistantId = null
    messageStore.clearChunk()
    messageStore.setSources([])
  }
})

// 监听会话 ID 变化
watch(() => messageStore.conversationId, (newId) => {
  if (newId) {
    chatStore.setCurrentSession(newId)
    // 刷新会话列表
    conversationApi.getList().then(list => chatStore.setSessions(list)).catch(() => {})
  }
})

/**
 * 处理发送消息
 * @param question 用户问题
 * @param useContext 是否使用上下文
 */
const handleSend = async (question: string, useContext: boolean) => {
  let conversationId = chatStore.currentSessionId ? parseInt(chatStore.currentSessionId) : null
  let tempSessionId: string | null = null
  
  // 如果没有当前会话，先创建会话
  if (!conversationId) {
    // 乐观更新：生成临时会话ID
    tempSessionId = `temp-${Date.now()}`
    
    // 立即更新UI：添加临时会话到列表顶部
    const tempSession = {
      id: -1,
      title: '新对话',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      tempId: tempSessionId
    }
    chatStore.addSession(tempSession)
    chatStore.setCurrentSession(tempSessionId)
    
    try {
      // 发送创建会话请求
      const newConv = await conversationApi.create({ title: '新对话' })
      
      // 替换临时会话为真实会话
      chatStore.removeSession(-1)
      chatStore.addSession(newConv)
      chatStore.setCurrentSession(String(newConv.id))
      conversationId = newConv.id
      tempSessionId = null
      
      // 刷新会话列表
      conversationApi.getList().then(list => chatStore.setSessions(list)).catch(() => {})
      
    } catch (error) {
      // 异常处理：回滚临时会话
      chatStore.removeSession(-1)
      chatStore.setCurrentSession(null)
      ElMessage.error('创建会话失败，请重试')
      return
    }
  }
  
  // 添加用户消息
  chatStore.addMessage({
    id: uuidv4(),
    role: 'user',
    content: question,
    timestamp: Date.now(),
  })

  // 只使用 WebSocket 发送（支持流式响应）
  loading.value = true
  messageStore.setStreaming(true)
  
  // 设置超时处理（180秒，3分钟）
  timeoutId = setTimeout(() => {
    if (loading.value) {
      loading.value = false
      messageStore.setStreaming(false)
      ElMessage.warning('请求超时，请重试')
      // 处理超时的助手消息
      if (currentAssistantId) {
        chatStore.updateMessage(currentAssistantId, (msg) => {
          msg.content += '\n\n[请求超时，请重试]'
          msg.streaming = false
        })
        currentAssistantId = null
      }
    }
  }, 180000)
  
  // 确保WebSocket连接已建立
  const waitForConnection = () => {
    return new Promise((resolve, reject) => {
      if (connected.value && authenticated.value) {
        resolve(true)
        return
      }
      
      // 如果未连接，尝试连接
      if (!connected.value) {
        connect()
      }
      
      // 等待连接建立和认证完成
      const checkInterval = setInterval(() => {
        if (connected.value && authenticated.value) {
          clearInterval(checkInterval)
          resolve(true)
        }
      }, 100)
      
      // WebSocket连接超时（10秒）
      setTimeout(() => {
        clearInterval(checkInterval)
        reject(new Error('WebSocket连接超时'))
      }, 10000)
    })
  }
  
  try {
    // 等待连接建立
    await waitForConnection()
    // 连接建立后发送消息
    sendMessage(question, useContext, conversationId)
  } catch (error) {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    loading.value = false
    messageStore.setStreaming(false)
    ElMessage.error('WebSocket连接失败，请检查网络连接或重试')
  }
}

/**
 * 切换思考内容展开/折叠
 * @param messageId 消息ID
 */
const toggleThinking = (messageId: string) => {
  chatStore.updateMessage(messageId, (msg) => {
    msg.isThinkingExpanded = !msg.isThinkingExpanded
  })
}

/**
 * 滚动到底部
 */
const scrollToBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

// 消息变化时自动滚动到底部
watch(messages, scrollToBottom, { deep: true })
</script>

<style scoped lang="scss">
.chat-view {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scroll-behavior: smooth;
}
</style>