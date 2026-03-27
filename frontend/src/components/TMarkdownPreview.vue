<template>
  <div @click="handleClick">
    <v-md-preview :text="defaultVal" @copy-code-success="() => emit('copyCodeSuccess')" :height="height"></v-md-preview>
  </div>
</template>
<script setup name="t-md-preview">
import VMdPreview from "@kangc/v-md-editor/lib/preview"
import "@kangc/v-md-editor/lib/style/preview.css"

// vuepress主题
import vuepressTheme from "@kangc/v-md-editor/lib/theme/vuepress.js"
import "@kangc/v-md-editor/lib/theme/style/vuepress.css"

/** 提示信息 */
import createTipPlugin from "@kangc/v-md-editor/lib/plugins/tip/index"
import "@kangc/v-md-editor/lib/plugins/tip/tip.css"

/** Emoji标签包 */
import createEmojiPlugin from "@kangc/v-md-editor/lib/plugins/emoji/index"
import "@kangc/v-md-editor/lib/plugins/emoji/emoji.css"

/** katex */
import createKatexPlugin from "@kangc/v-md-editor/lib/plugins/katex/npm"

/** todo-list */
import createTodoListPlugin from "@kangc/v-md-editor/lib/plugins/todo-list/index"
import "@kangc/v-md-editor/lib/plugins/todo-list/todo-list.css"

/** 代码拷贝 */
import createCopyCodePlugin from "@kangc/v-md-editor/lib/plugins/copy-code/index"
import "@kangc/v-md-editor/lib/plugins/copy-code/copy-code.css"

import Prism from "prismjs"

VMdPreview.use(vuepressTheme, {
  Prism,
  extend(md) {
    md.set({ quotes: "\"\"''" })
  }
})

VMdPreview.use(createTipPlugin())
VMdPreview.use(createEmojiPlugin())
VMdPreview.use(createKatexPlugin())
VMdPreview.use(createTodoListPlugin())
VMdPreview.use(createCopyCodePlugin())

const props = defineProps({
  defaultVal: {
    type: String,
    default: ""
  },
  height: {
    type: String,
    default: "fit-content"
  }
})

const emit = defineEmits(["copyCodeSuccess", "click"])

// 处理点击事件
const handleClick = (event) => {
  emit("click", event)
}
</script>

<style lang="less" scoped></style>