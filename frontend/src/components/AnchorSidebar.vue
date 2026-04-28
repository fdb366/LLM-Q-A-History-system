<template>
  <div class="anchor-float" v-if="anchorItems.length">
    <div class="anchor-indicators">
      <div
        v-for="(item, index) in anchorItems"
        :key="item.id"
        class="anchor-indicator"
        :class="{ 'is-active': activeMessageId === item.id }"
        @click="handleAnchorClick(item.id)"
      >
        <div class="indicator-line"></div>
        <div class="indicator-tooltip">
          <span class="tooltip-text">{{ item.shortTitle }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, type Ref } from 'vue'
import { useChatStore } from '../pinia/modules/chat'

const chatStore = useChatStore()
const messages = computed(() => chatStore.messages)

const activeMessageId = inject<Ref<string | null>>('activeMessageId')

const anchorItems = computed(() => {
  return messages.value
    .filter(msg => msg.role === 'user')
    .map(msg => {
      const fullTitle = msg.content
      const shortTitle = fullTitle.length > 15 ? fullTitle.slice(0, 15) + '…' : fullTitle
      return {
        id: msg.id,
        fullTitle,
        shortTitle,
      }
    })
})

const handleAnchorClick = (id: string) => {
  const element = document.getElementById(`msg-${id}`)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
</script>

<style scoped lang="scss">
.anchor-float {
  position: fixed;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
  pointer-events: auto;
}

.anchor-indicators {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 8px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
}

.anchor-indicator {
  position: relative;
  display: flex;
  align-items: center;
  cursor: pointer;
  pointer-events: auto;

  .indicator-line {
    width: 3px;
    height: 16px;
    background-color: #dcdfe6;
    border-radius: 2px;
    transition: all 0.3s ease;
  }

  .indicator-tooltip {
    position: absolute;
    right: 16px;
    top: 50%;
    transform: translateY(-50%);
    background: #303133;
    color: #fff;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 12px;
    white-space: nowrap;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
    pointer-events: none;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);

    .tooltip-text {
      display: block;
      max-width: 150px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    &::after {
      content: '';
      position: absolute;
      right: -6px;
      top: 50%;
      transform: translateY(-50%);
      border: 6px solid transparent;
      border-left-color: #303133;
      border-right: none;
    }
  }

  &:hover {
    .indicator-line {
      background-color: #409eff;
      height: 20px;
    }

    .indicator-tooltip {
      opacity: 1;
      visibility: visible;
      right: 20px;
    }
  }

  &.is-active {
    .indicator-line {
      background-color: #409eff;
      height: 24px;
      width: 4px;
      box-shadow: 0 0 8px rgba(64, 158, 255, 0.4);
    }

    .indicator-tooltip {
      background: #409eff;
      
      &::after {
        border-left-color: #409eff;
      }
    }

    &:hover {
      .indicator-line {
        background-color: #409eff;
        height: 24px;
        width: 4px;
        box-shadow: 0 0 8px rgba(64, 158, 255, 0.6);
      }

      .indicator-tooltip {
        opacity: 1;
        visibility: visible;
        right: 20px;
      }
    }
  }
}

@media screen and (max-width: 1200px) {
  .anchor-float {
    right: 10px;
  }

  .anchor-indicators {
    padding: 8px 6px;
  }

  .anchor-indicator {
    .indicator-tooltip {
      display: none;
    }
  }
}

@media screen and (max-width: 768px) {
  .anchor-float {
    display: none;
  }
}
</style>
