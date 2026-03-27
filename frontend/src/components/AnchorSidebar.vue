<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <div class="header-left" v-if="!isCollapsed">
        <h3>历史对话</h3>
      </div>
      <div class="header-actions">
        <el-button 
          :type="isCollapsed ? 'text' : 'primary'" 
          :size="isCollapsed ? 'large' : 'small'"
          @click="createNewChat" 
          :loading="creating"
          :icon="Plus"
          circle
          v-if="isCollapsed"
        />
        <el-button 
          v-else
          type="primary" 
          size="small" 
          @click="createNewChat" 
          :loading="creating"
        >
          + 新对话
        </el-button>
        <el-button 
          :icon="isCollapsed ? 'Expand' : 'Fold'" 
          @click="toggleCollapse"
          circle
          size="small"
        />
      </div>
    </div>
    <div class="sidebar-content scrollbar-thin" v-show="!isCollapsed">
      <!-- 按时间分组渲染 -->
      <div v-for="group in groupedConversations" :key="group.label" class="conv-group">
        <div class="group-label">{{ group.label }}</div>
        <div
          v-for="conv in group.list"
          :key="conv.id"
          class="conv-item"
          :class="{ active: currentConvId === conv.id }"
          @click="selectConversation(conv.id)"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span class="title ellipsis">{{ conv.title }}</span>
          <el-icon class="delete-icon" @click.stop="deleteConversation(conv.id)"><Delete /></el-icon>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatDotRound, Delete, Plus, Fold, Expand } from '@element-plus/icons-vue'
import { useChatStore } from '../pinia/modules/chat'
import { useUserStore } from '../pinia/modules/user'
import { conversationApi } from '../api/conversation'

const chatStore = useChatStore()
const userStore = useUserStore()
const creating = ref(false)
const isCollapsed = ref(false) // 折叠状态

const currentConvId = computed(() => chatStore.currentSessionId ? parseInt(chatStore.currentSessionId) : null)
const conversations = computed(() => chatStore.sessions)

// 按时间分组（同之前）
const groupedConversations = computed(() => {
  const groups: { label: string; list: any[] }[] = []
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const yesterday = today - 86400000
  const weekAgo = today - 7 * 86400000
  const monthAgo = today - 30 * 86400000

  const todayList: any[] = []
  const yesterdayList: any[] = []
  const weekList: any[] = []
  const monthList: any[] = []
  const olderList: any[] = []

  conversations.value.forEach(conv => {
    const updated = new Date(conv.updated_at).getTime()
    if (updated >= today) {
      todayList.push(conv)
    } else if (updated >= yesterday) {
      yesterdayList.push(conv)
    } else if (updated >= weekAgo) {
      weekList.push(conv)
    } else if (updated >= monthAgo) {
      monthList.push(conv)
    } else {
      olderList.push(conv)
    }
  })

  if (todayList.length) groups.push({ label: '今天', list: todayList })
  if (yesterdayList.length) groups.push({ label: '昨天', list: yesterdayList })
  if (weekList.length) groups.push({ label: '7天', list: weekList })
  if (monthList.length) groups.push({ label: '30天', list: monthList })
  if (olderList.length) groups.push({ label: '更早', list: olderList })
  return groups
})

// 加载会话列表（通过 store 已有的方法）
const loadConversations = async () => {
  if (!userStore.token) return
  try {
    const data = await conversationApi.getList()
    chatStore.setSessions(data)
  } catch (error) {
    console.error('加载会话失败', error)
  }
}

// 新建对话
const createNewChat = async () => {
  creating.value = true
  try {
    const newConv = await conversationApi.create({ title: '新对话' })
    chatStore.addSession(newConv)
    chatStore.setCurrentSession(newConv.id)
    chatStore.clearMessages()
    // 如果侧边栏折叠，自动展开以显示新对话？（可选）
    // isCollapsed.value = false
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

// 选择对话
const selectConversation = (id: number) => {
  if (currentConvId.value === id) return
  chatStore.setCurrentSession(id)
  // 切换会话时先清空当前消息
  chatStore.clearMessages()
  loadMessages(id)
}

const loadMessages = async (convId: number) => {
  try {
    const msgs = await conversationApi.getMessages(convId)
    console.log('加载到的消息数据:', msgs)
    // 转换消息格式以匹配 store 的 Message 类型，并解析思考内容
    const formatted = msgs.map((m: any) => {
      const content = m.content
      const thinkingMatch = content.match(/<think>(.*?)<\/think>/s)
      
      let thinking = ''
      let summary = ''
      
      if (thinkingMatch) {
        // 包含思考内容
        thinking = thinkingMatch[1].trim()
        summary = content.replace(/<think>.*?<\/think>/s, '').trim()
      } else {
        // 只有总结内容
        summary = content.trim()
      }
      
      return {
        id: String(m.id),
        role: m.role,
        content: m.content,
        timestamp: new Date(m.created_at).getTime(),
        thinking: thinking,
        summary: summary,
        isThinkingExpanded: true  // 历史消息默认折叠思考内容
      }
    })
    console.log('转换后的消息格式:', formatted)
    chatStore.setMessages(formatted)
    console.log('Store中的消息数量:', chatStore.messages.length)
  } catch (error) {
    console.error('加载消息失败:', error)
    ElMessage.error('加载消息失败')
  }
}

// 删除对话
const deleteConversation = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定删除该对话吗？')
    await conversationApi.delete(id)
    chatStore.removeSession(id)
    if (currentConvId.value === id) {
      chatStore.setCurrentSession(null)
      chatStore.clearMessages()
    }
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

// 切换折叠状态
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

onMounted(() => {
  loadConversations()
})
</script>

<style scoped lang="scss">
.sidebar {
  width: 260px;
  height: 100%;
  background-color: #f9f9f9;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;

  &.collapsed {
    width: 60px;

    .sidebar-header {
      justify-content: center;
      padding: 16px 0;
    }

    .header-left {
      display: none;
    }

    .sidebar-content {
      display: none;
    }
  }
}

.sidebar-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);

  .header-left {
    h3 {
      margin: 0;
      font-size: 16px;
    }
  }

  .header-actions {
    display: flex;
    gap: 8px;
  }
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conv-group {
  margin-bottom: 16px;

  .group-label {
    font-size: 12px;
    color: #999;
    padding: 4px 8px;
  }

  .conv-item {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
    margin: 2px 0;

    &:hover {
      background-color: rgba(0, 0, 0, 0.05);
      .delete-icon {
        opacity: 1;
      }
    }

    &.active {
      background-color: #e6f4ff;
    }

    .el-icon {
      margin-right: 8px;
      font-size: 16px;
    }

    .title {
      flex: 1;
      font-size: 14px;
    }

    .delete-icon {
      opacity: 0;
      transition: opacity 0.2s;
      font-size: 14px;
      color: #999;

      &:hover {
        color: #f56c6c;
      }
    }
  }
}
</style>