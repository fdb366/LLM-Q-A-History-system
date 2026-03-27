import { ref, watch, nextTick } from 'vue'

export function useTyping(text: string, speed = 30) {
  const displayedText = ref('')
  const isTyping = ref(false)
  const isDone = ref(false)
  let index = 0
  let timer: number | null = null

  const start = () => {
    if (isTyping.value) return
    isTyping.value = true
    isDone.value = false
    index = 0
    displayedText.value = ''
    const step = () => {
      if (index < text.length) {
        displayedText.value += text[index]
        index++
        timer = setTimeout(step, speed) as any
      } else {
        isTyping.value = false
        isDone.value = true
      }
    }
    step()
  }

  const stop = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    isTyping.value = false
  }

  const reset = () => {
    stop()
    displayedText.value = ''
    index = 0
    isDone.value = false
  }

  // 当传入的文本变化时，重新开始打字
  watch(() => text, (newVal) => {
    if (newVal) {
      stop()
      reset()
      nextTick(() => start())
    } else {
      reset()
    }
  }, { immediate: true })

  return {
    displayedText,
    isTyping,
    isDone,
    start,
    stop,
    reset,
  }
}