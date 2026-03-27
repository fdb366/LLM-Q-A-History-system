<template>
  <div class="chat-input">
    <el-input
      v-model="inputText"
      type="textarea"
      :rows="3"
      placeholder="请输入历史问题，例如：秦始皇什么时候统一六国的？"
      :disabled="disabled"
      @keydown.enter.prevent="handleSend"
    />
    <div class="actions">
      <el-checkbox v-model="useContext">使用知识库检索</el-checkbox>
      <el-button type="primary" :loading="loading" @click="handleSend" :disabled="!inputText.trim()">
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  loading?: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'send', question: string, useContext: boolean): void
}>()

const inputText = ref('')
const useContext = ref(true)

const handleSend = () => {
  if (!inputText.value.trim() || props.loading) return
  emit('send', inputText.value.trim(), useContext.value)
  inputText.value = ''
}
</script>

<style scoped lang="scss">
.chat-input {
  padding: 20px;
  border-top: 1px solid var(--border-color);
  background-color: #fff;

  .actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 10px;
  }
}
</style>