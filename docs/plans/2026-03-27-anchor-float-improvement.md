# 消息锚点悬浮窗改进实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将消息锚点改造成悬浮窗效果，默认只显示灰色直线，鼠标悬停时显示标题

**Architecture:** 
1. 悬浮窗定位：使用fixed定位，悬浮在页面右侧
2. 视觉效果：默认显示灰色直线指示器，悬停时展开显示标题
3. 交互优化：平滑过渡动画，高亮当前选中项

**Tech Stack:** Vue 3, TypeScript, SCSS, CSS Transitions

---

## 需求分析

### 当前实现
- 固定宽度140px的侧边栏
- 始终显示标题文字
- 占用页面空间

### 目标效果
1. **悬浮窗形式**：小窗口悬浮在页面右侧，不占用页面空间
2. **灰色直线指示器**：每个消息对应一条灰色直线
3. **悬停展开**：鼠标悬停时展开显示标题
4. **选中高亮**：当前选中的消息直线高亮显示

---

## Task 1: 重构AnchorSidebar组件为悬浮窗

**Files:**
- Modify: `d:\桌面\LLM_project\frontend\src\components\AnchorSidebar.vue:1-109`

**Step 1: 修改模板结构**

修改 `d:\桌面\LLM_project\frontend\src\components\AnchorSidebar.vue`:

```vue
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
```

**Step 2: 修改脚本逻辑**

```typescript
<script setup lang="ts">
import { computed, inject, type Ref } from 'vue'
import { useChatStore } from '../pinia/modules/chat'

const props = defineProps<{
  container?: HTMLElement
}>()

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
```

**Step 3: 添加悬浮窗样式**

```scss
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
  }
}
</style>
```

**Step 4: 验证修改**

检查悬浮窗是否正确显示，悬停时是否展开标题。

---

## Task 2: 更新ChatView中的AnchorSidebar使用方式

**Files:**
- Modify: `d:\桌面\LLM_project\frontend\src\views\ChatView.vue:1-297`

**Step 1: 移除AnchorSidebar的container prop**

修改 `d:\桌面\LLM_project\frontend\src\views\ChatView.vue`:

```vue
<template>
  <div class="chat-view">
    <Sidebar />
    <div class="main-area">
      <!-- ... -->
    </div>
    <AnchorSidebar v-if="messages.length" />
  </div>
</template>
```

**Step 2: 验证修改**

检查页面布局是否正常，悬浮窗是否正确定位。

---

## Task 3: 优化滚动监听逻辑

**Files:**
- Modify: `d:\桌面\LLM_project\frontend\src\views\ChatView.vue:58-76`

**Step 1: 优化滚动监听，提高性能**

```typescript
const handleScroll = () => {
  if (!messageListRef.value) return
  
  const container = messageListRef.value
  const containerRect = container.getBoundingClientRect()
  const containerHeight = container.clientHeight
  const messageElements = container.querySelectorAll('[id^="msg-"]')
  
  let foundActive = false
  
  for (let i = messageElements.length - 1; i >= 0; i--) {
    const element = messageElements[i] as HTMLElement
    const rect = element.getBoundingClientRect()
    
    if (rect.top <= containerRect.top + containerHeight / 3 && !foundActive) {
      const id = element.id.replace('msg-', '')
      activeMessageId.value = id
      foundActive = true
    }
  }
}
```

**Step 2: 验证修改**

滚动消息列表，检查悬浮窗指示器是否正确高亮当前消息。

---

## Task 4: 添加响应式适配

**Files:**
- Modify: `d:\桌面\LLM_project\frontend\src\components\AnchorSidebar.vue:57-109`

**Step 1: 添加响应式样式**

```scss
<style scoped lang="scss">
// ... 现有样式 ...

// 响应式适配
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
```

**Step 2: 验证修改**

调整浏览器窗口大小，检查悬浮窗是否正确响应。

---

## Task 5: 提交代码

**Step 1: 添加修改的文件**

```bash
git add frontend/src/components/AnchorSidebar.vue
git add frontend/src/views/ChatView.vue
```

**Step 2: 提交更改**

```bash
git commit -m "feat: 将消息锚点改造成悬浮窗效果

- 重构AnchorSidebar为悬浮窗形式
- 默认显示灰色直线指示器
- 鼠标悬停时展开显示标题
- 当前选中消息高亮显示
- 添加响应式适配"
```

---

## 测试清单

1. **悬浮窗显示测试**
   - [ ] 悬浮窗正确定位在页面右侧
   - [ ] 默认只显示灰色直线指示器
   - [ ] 悬停时展开显示标题

2. **交互测试**
   - [ ] 点击指示器跳转到对应消息
   - [ ] 滚动时当前消息指示器高亮
   - [ ] 平滑过渡动画效果

3. **响应式测试**
   - [ ] 小屏幕隐藏悬浮窗
   - [ ] 中等屏幕隐藏标题提示

4. **性能测试**
   - [ ] 滚动流畅，无卡顿
   - [ ] 动画过渡平滑
