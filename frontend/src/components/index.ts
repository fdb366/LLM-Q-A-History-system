// src/components/index.ts
import type { App } from 'vue'
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'
import Sidebar from './Sidebar.vue'
import TMarkdownPreview from './TMarkdownPreview.vue'
import AnchorSidebar from './AnchorSidebar.vue'

// 导出组件，方便按需导入
export { ChatMessage, ChatInput, Sidebar, TMarkdownPreview, AnchorSidebar }

// 全局注册
export default {
  install(app: App) {
    app.component('ChatMessage', ChatMessage)
    app.component('ChatInput', ChatInput)
    app.component('Sidebar', Sidebar)
    app.component('TMarkdownPreview', TMarkdownPreview)
    app.component('AnchorSidebar', AnchorSidebar)
  }
}
