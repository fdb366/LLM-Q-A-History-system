<!-- src/components/AnchorSidebar.vue -->
<template>
  <aside class="anchor-sidebar scrollbar-thin" v-show="anchorItems.length">
    <div class="anchor-content">
      <el-anchor :container="container" scroll-offset="80" direction="vertical">
        <el-anchor-link
          v-for="item in anchorItems"
          :key="item.id"
          :href="`#msg-${item.id}`"
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
import { computed } from 'vue'
import { ElAnchor, ElAnchorLink, ElTooltip } from 'element-plus'
import { useChatStore } from '../pinia/modules/chat'

const props = defineProps<{
  container?: HTMLElement          // 滚动容器，用于锚点定位
}>()

const chatStore = useChatStore()
const messages = computed(() => chatStore.messages)

// 仅过滤用户消息，生成锚点数据
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
</script>

<style scoped lang="scss">
.anchor-sidebar {
  width: 140px;
  height: 100%;
  border-left: 1px solid var(--border-color);
  background-color: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  

  .anchor-content {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;

    :deep(.el-anchor) {
      .el-anchor__item {
        margin-bottom: 4px;
      }

      .el-anchor__link {
        padding: 6px 12px;
        border-radius: 4px;
        transition: background-color 0.2s;
        font-size: 13px;
        line-height: 1.4;
        color: #606266;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;

        &:hover {
          background-color: #f5f7fa;
        }

        &.is-active {
          background-color: #ecf5ff;
          color: #409eff;
          font-weight: 500;
        }
      }
    }
  }
}

.anchor-title {
  display: block;
  width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>