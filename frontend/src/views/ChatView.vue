<template>
  <div class="chat-view">
    <Sidebar />
    <div class="main-area">
      <div v-if="!connected || !authenticated" class="connection-status">
        <el-tag :type="connected ? 'success' : 'danger'" size="small">
          {{ connected ? (authenticated ? '已连接' : '认证中...') : '连接中...' }}
        </el-tag>
      </div>
      <div class="message-list" ref="messageListRef">
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
    <AnchorSidebar v-if="messages.length" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed, provide, onMounted, onUnmounted } from 'vue'
import { useChatStore } from '../pinia/modules/chat'
import { useMessageStore } from '../pinia/modules/message'
import { useSocket } from '../composables/useSocket'
import { conversationApi } from '../api/conversation'
import { ElMessage, ElTag } from 'element-plus'
import { v4 as uuidv4 } from 'uuid'

const chatStore = useChatStore()
const messageStore = useMessageStore()

const messages = computed(() => chatStore.messages)
const loading = ref(false)
const messageListRef = ref<HTMLElement>()

const WS_URL = 'ws://localhost:8000/ws/chat'
const { connect, sendMessage, authenticated, connected, reconnect } = useSocket(WS_URL)

let currentAssistantId: string | null = null
let timeoutId: number | null = null

const activeMessageId = ref<string | null>(null)
provide('activeMessageId', activeMessageId)

const handleScroll = () => {
  if (!messageListRef.value) return
  
  const container = messageListRef.value
  const containerHeight = container.clientHeight
  const messageElements = container.querySelectorAll('[id^="msg-"]')
  
  for (let i = 0; i < messageElements.length; i++) {
    const element = messageElements[i] as HTMLElement
    const rect = element.getBoundingClientRect()
    const containerRect = container.getBoundingClientRect()
    
    if (rect.top >= containerRect.top && rect.top <= containerRect.top + containerHeight / 2) {
      const id = element.id.replace('msg-', '')
      activeMessageId.value = id
      break
    }
  }
}

onMounted(() => {
  if (!connected.value || !authenticated.value) {
    reconnect()
  }
  if (messageListRef.value) {
    messageListRef.value.addEventListener('scroll', handleScroll)
  }
})

onUnmounted(() => {
  if (messageListRef.value) {
    messageListRef.value.removeEventListener('scroll', handleScroll)
  }
})

watch(() => messageStore.currentChunk, (newChunk) => {
  if (!currentAssistantId && newChunk) {
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
    chatStore.updateMessage(currentAssistantId, (msg) => {
      msg.content += newChunk
    })
  }
})

watch(() => messageStore.streaming, (isStreaming) => {
  if (!isStreaming && currentAssistantId) {
    chatStore.updateMessage(currentAssistantId, (msg) => {
      msg.streaming = false
      if (messageStore.sources.length > 0) {
        msg.sources = messageStore.sources
      }
      
      const content = msg.content
      const thinkTag = 'usse'
      const thinkTagEnd = 'vaaf'
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

watch(() => messageStore.conversationId, (newId) => {
  if (newId) {
    chatStore.setCurrentSession(newId)
  }
})

watch(() => messageStore.conversationTitle, (newTitle) => {
  if (newTitle && chatStore.currentSessionId) {
    const sessionId = parseInt(chatStore.currentSessionId)
    if (!isNaN(sessionId)) {
      chatStore.updateSession(sessionId, (s) => {
        s.title = newTitle
      })
    }
    messageStore.setConversationTitle('')
  }
})

const handleSend = async (question: string, useContext: boolean) => {
  let conversationId = chatStore.currentSessionId ? parseInt(chatStore.currentSessionId) : null
  let tempSessionId: string | null = null
  
  if (!conversationId) {
    tempSessionId = `temp-${Date.now()}`
    
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
      const newConv = await conversationApi.create({ title: '新对话' })
      
      chatStore.removeSession(-1)
      chatStore.addSession(newConv)
      chatStore.setCurrentSession(String(newConv.id))
      conversationId = newConv.id
      tempSessionId = null
      
    } catch (error) {
      chatStore.removeSession(-1)
      chatStore.setCurrentSession(null)
      ElMessage.error('创建会话失败，请重试')
      return
    }
  }
  
  chatStore.addMessage({
    id: uuidv4(),
    role: 'user',
    content: question,
    timestamp: Date.now(),
  })

  loading.value = true
  messageStore.setStreaming(true)
  
  timeoutId = setTimeout(() => {
    if (loading.value) {
      loading.value = false
      messageStore.setStreaming(false)
      ElMessage.warning('请求超时，请重试')
      if (currentAssistantId) {
        chatStore.updateMessage(currentAssistantId, (msg) => {
          msg.content += '\n\n[请求超时，请重试]'
          msg.streaming = false
        })
        currentAssistantId = null
      }
    }
  }, 180000)
  
  const waitForConnection = () => {
    return new Promise((resolve, reject) => {
      if (connected.value && authenticated.value) {
        resolve(true)
        return
      }
      
      reconnect()
      
      const checkInterval = setInterval(() => {
        if (connected.value && authenticated.value) {
          clearInterval(checkInterval)
          resolve(true)
        }
      }, 100)
      
      setTimeout(() => {
        clearInterval(checkInterval)
        reject(new Error('WebSocket连接超时'))
      }, 10000)
    })
  }
  
  try {
    await waitForConnection()
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

const toggleThinking = (messageId: string) => {
  chatStore.updateMessage(messageId, (msg) => {
    msg.isThinkingExpanded = !msg.isThinkingExpanded
  })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

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

.connection-status {
  padding: 8px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: center;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 40px;
  scroll-behavior: smooth;
}
</style>
