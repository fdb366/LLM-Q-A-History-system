import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 导入全局样式
import '@/assets/main.scss'

// 导入全局组件注册
import globalComponents from '@/components'

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus)
app.use(globalComponents)

app.mount('#app')