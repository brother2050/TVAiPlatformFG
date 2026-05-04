<template>
  <div class="json-template-editor">
    <div class="editor-header">
      <el-input v-model="templateName" size="small" placeholder="模板名称" style="width: 200px" />
      <el-select v-model="templateCategory" size="small" placeholder="分类" style="width: 120px">
        <el-option label="剧本" value="script" />
        <el-option label="角色" value="character" />
        <el-option label="分镜" value="storyboard" />
        <el-option label="台词" value="dialogue" />
      </el-select>
    </div>
    <div class="editor-body">
      <div ref="editorContainer" class="monaco-container" />
    </div>
    <div class="editor-footer">
      <el-button size="small" @click="handleFormat">格式化</el-button>
      <el-button size="small" type="primary" @click="handleSave">保存</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps<{
  initialContent?: string
  name?: string
  category?: string
}>()

const emit = defineEmits<{
  (e: 'save', data: { name: string; category: string; content: string }): void
}>()

const editorContainer = ref<HTMLDivElement | null>(null)
const templateName = ref(props.name || '')
const templateCategory = ref(props.category || 'script')
let editor: any = null

onMounted(async () => {
  if (!editorContainer.value) return
  try {
    const monaco = await import('monaco-editor')
    editor = monaco.editor.create(editorContainer.value, {
      value: props.initialContent || '{\n  \n}',
      language: 'json',
      theme: 'vs-dark',
      minimap: { enabled: false },
      fontSize: 13,
      lineNumbers: 'on',
      scrollBeyondLastLine: false,
      automaticLayout: true,
    })
  } catch {
    // monaco not available — fallback to textarea handled by parent
  }
})

function handleFormat() {
  if (!editor) return
  try {
    const val = editor.getValue()
    const parsed = JSON.parse(val)
    editor.setValue(JSON.stringify(parsed, null, 2))
  } catch {
    // invalid JSON
  }
}

function handleSave() {
  emit('save', {
    name: templateName.value,
    category: templateCategory.value,
    content: editor?.getValue() || '',
  })
}

onBeforeUnmount(() => {
  editor?.dispose()
})
</script>

<style lang="scss" scoped>
.json-template-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.editor-header {
  display: flex;
  gap: 12px;
}

.editor-body {
  flex: 1;
  min-height: 300px;
}

.monaco-container {
  width: 100%;
  height: 100%;
  border-radius: 6px;
  overflow: hidden;
}

.editor-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
