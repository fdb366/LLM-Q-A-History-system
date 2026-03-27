<template>
  <div class="chat-message" :class="[role]">
    <div class="avatar">
      <el-avatar :size="40" :src="avatar" />
    </div>
    <div class="content-wrapper">
      <div class="name">{{ displayName }}</div>
      <div class="bubble">
        <template v-if="role === 'assistant' && typing && !isDone">
          <TMarkdownPreview :defaultVal="displayedText" />
          <span v-if="isTyping" class="cursor">|</span>
        </template>
        <template v-else-if="role === 'assistant' && thinking">
          <!-- 思考内容折叠显示 -->
          <div class="thinking-section">
            <div class="thinking-header" @click="toggleThinking">
              <span class="thinking-icon">{{ isThinkingExpanded ? '▼' : '▶' }}</span>
              <span class="thinking-label">思考过程</span>
            </div>
            <div v-if="isThinkingExpanded" class="thinking-content">
              <TMarkdownPreview :defaultVal="thinking" />
            </div>
          </div>
          <!-- 总结内容 -->
          <div class="summary-content">
            <TMarkdownPreview :defaultVal="summary || content" />
          </div>
        </template>
        <template v-else>
          <TMarkdownPreview :defaultVal="content" />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTyping } from '../composables/useTyping'

const props = defineProps<{
  role: 'user' | 'assistant'
  content: string
  avatar?: string
  name?: string
  typing?: boolean // 是否正在打字（仅 assistant 使用）
  thinking?: string // 思考内容
  summary?: string // 总结内容
  isThinkingExpanded?: boolean // 思考内容是否展开
}>()

const emit = defineEmits(['toggleThinking'])

// 切换思考内容展开/折叠
const toggleThinking = () => {
  emit('toggleThinking')
}

const { displayedText, isTyping, isDone } = useTyping(props.typing ? props.content : '')

const displayName = computed(() => {
  if (props.name) return props.name
  return props.role === 'user' ? '我' : 'AI助手'
})

const avatarUrl = computed(() => {
  if (props.avatar) return props.avatar
  return props.role === 'user'
    ? 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'
    : 'https://cube.elemecdn.com/9/c2/f0ee8a3c7c9638a54940382568c9dpng.png'
})
</script>

<style scoped lang="scss">
.cursor {
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background-color: #333;
  margin-left: 2px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.thinking-section {
  margin-bottom: 12px;
}

.thinking-header {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 12px;
  background-color: #f5f5f5;
  border-radius: 6px;
  margin-bottom: 8px;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: #e8e8e8;
  }
}

.thinking-icon {
  margin-right: 8px;
  font-size: 12px;
  color: #666;
}

.thinking-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.thinking-content {
  padding: 12px;
  background-color: #f9f9f9;
  border-radius: 6px;
  border-left: 3px solid #409eff;
  margin-bottom: 8px;
}

.summary-content {
  padding: 8px 0;
}
</style>