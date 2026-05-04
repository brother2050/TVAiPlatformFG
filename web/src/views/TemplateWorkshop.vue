<template>
  <div class="template-workshop">
    <header class="page-header">
      <h1>调模板</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon> 新建模板
        </el-button>
      </div>
    </header>

    <el-row :gutter="20">
      <!-- 模板列表 -->
      <el-col :span="8">
        <el-card class="template-list-card">
          <template #header>
            <el-input v-model="searchQuery" placeholder="搜索模板…" prefix-icon="Search" clearable size="small" />
          </template>
          <div class="template-items">
            <div
              v-for="tpl in filteredTemplates"
              :key="tpl.id"
              class="template-item"
              :class="{ active: currentTemplate?.id === tpl.id }"
              @click="selectTemplate(tpl)"
            >
              <div class="tpl-info">
                <span class="tpl-name">{{ tpl.name }}</span>
                <span class="tpl-meta">{{ categoryLabel(tpl.category) }} · v{{ tpl.version }}</span>
              </div>
              <el-tag v-if="tpl.is_builtin" size="small" type="info">内置</el-tag>
            </div>
            <el-empty v-if="filteredTemplates.length === 0" description="无模板" :image-size="60" />
          </div>
        </el-card>
      </el-col>

      <!-- 编辑器 -->
      <el-col :span="16">
        <div v-if="!currentTemplate" class="empty-state">
          <el-empty description="选择左侧模板进行编辑" />
        </div>
        <div v-else>
          <el-card class="editor-card">
            <template #header>
              <div class="editor-header">
                <div>
                  <h3>{{ currentTemplate.name }}</h3>
                  <p class="tpl-desc">{{ currentTemplate.description }}</p>
                </div>
                <div class="editor-actions">
                  <el-button size="small" @click="previewTemplate">
                    <el-icon><View /></el-icon> 预览
                  </el-button>
                  <el-button size="small" @click="resetTemplate">
                    <el-icon><RefreshLeft /></el-icon> 恢复默认
                  </el-button>
                  <el-button size="small" type="primary" @click="saveTemplate" :loading="saving">
                    保存
                  </el-button>
                  <el-dropdown @command="handleExport">
                    <el-button size="small">导出 <el-icon><ArrowDown /></el-icon></el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="json">导出 JSON</el-dropdown-item>
                        <el-dropdown-item command="import">导入模板</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </template>

            <!-- Schema 可视化编辑 -->
            <div class="schema-editor">
              <div class="schema-toolbar">
                <el-button size="small" @click="addField"><el-icon><Plus /></el-icon> 添加字段</el-button>
                <el-button size="small" @click="addNestedObject">嵌套子对象</el-button>
                <el-button size="small" @click="setAsArray">设为数组</el-button>
                <el-button size="small" type="danger" @click="deleteSelectedField" :disabled="!selectedField">
                  <el-icon><Delete /></el-icon> 删除字段
                </el-button>
              </div>

              <!-- Schema 树 -->
              <div class="schema-tree">
                <div
                  v-for="(field, key) in schemaFields"
                  :key="key"
                  class="field-item"
                  :class="{ active: selectedField === key, nested: field._nested }"
                  @click="selectedField = key as string"
                >
                  <div class="field-row">
                    <el-icon v-if="field.type === 'object'"><Folder /></el-icon>
                    <el-icon v-else-if="field.type === 'array'"><List /></el-icon>
                    <el-icon v-else><Document /></el-icon>
                    <span class="field-key">{{ key }}</span>
                    <el-tag size="small" type="info">{{ field.type }}</el-tag>
                    <span v-if="field.required" class="required-badge">*</span>
                    <el-input
                      v-if="selectedField === key"
                      v-model="field.description"
                      size="small"
                      placeholder="字段描述"
                      style="flex: 1; margin-left: 8px"
                    />
                  </div>
                  <!-- 嵌套字段 -->
                  <div v-if="field.type === 'object' && field.properties" class="nested-fields">
                    <div
                      v-for="(sub, subKey) in field.properties"
                      :key="subKey"
                      class="field-item nested"
                    >
                      <div class="field-row">
                        <span class="field-key">{{ subKey }}</span>
                        <el-tag size="small" type="info">{{ sub.type || 'string' }}</el-tag>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- JSON 编辑器 -->
            <el-divider>JSON Schema</el-divider>
            <div class="json-editor">
              <el-input
                v-model="jsonEditorContent"
                type="textarea"
                :rows="16"
                placeholder="JSON Schema 内容…"
                class="json-textarea"
                spellcheck="false"
              />
            </div>

            <!-- System Prompt Suffix -->
            <el-divider>System Prompt 补充</el-divider>
            <el-input
              v-model="currentTemplate.system_prompt_suffix"
              type="textarea"
              :rows="4"
              placeholder="追加到 AI system prompt 的内容…"
            />
          </el-card>

          <!-- 预览弹窗 -->
          <el-dialog v-model="showPreview" title="模板预览" width="700px">
            <el-alert title="以下是根据此模板 AI 生成的示例输出" type="info" :closable="false" style="margin-bottom: 16px" />
            <pre class="preview-content">{{ previewContent }}</pre>
          </el-dialog>
        </div>
      </el-col>
    </el-row>

    <!-- 新建模板弹窗 -->
    <el-dialog v-model="showCreateDialog" title="新建模板" width="500px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="createForm.name" /></el-form-item>
        <el-form-item label="标识"><el-input v-model="createForm.slug" placeholder="英文标识，如 my-template" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="createForm.category">
            <el-option label="剧本" value="script" />
            <el-option label="角色" value="character" />
            <el-option label="分镜" value="storyboard" />
            <el-option label="对话" value="dialogue" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="createForm.description" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createTemplate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, View, RefreshLeft, ArrowDown, Folder, List, Document } from '@element-plus/icons-vue'
import { useTemplateStore } from '@/stores/template'
import type { JSONTemplate } from '@/api'

const templateStore = useTemplateStore()

const searchQuery = ref('')
const currentTemplate = ref<JSONTemplate | null>(null)
const selectedField = ref('')
const saving = ref(false)
const showPreview = ref(false)
const previewContent = ref('')
const showCreateDialog = ref(false)

const createForm = reactive({
  name: '',
  slug: '',
  category: 'script' as string,
  description: '',
})

interface SchemaField {
  type: string
  description?: string
  required?: boolean
  properties?: Record<string, any>
  _nested?: boolean
}

const schemaFields = ref<Record<string, SchemaField>>({})
const jsonEditorContent = ref('')

const filteredTemplates = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return templateStore.templates.filter(t =>
    !q || t.name.toLowerCase().includes(q) || t.slug.toLowerCase().includes(q)
  )
})

function categoryLabel(c: string) {
  const map: Record<string, string> = { script: '剧本', character: '角色', storyboard: '分镜', dialogue: '对话' }
  return map[c] || c
}

function selectTemplate(tpl: JSONTemplate) {
  currentTemplate.value = tpl
  schemaFields.value = buildSchemaFields(tpl.schema)
  jsonEditorContent.value = JSON.stringify(tpl.schema, null, 2)
}

function buildSchemaFields(schema: Record<string, any>): Record<string, SchemaField> {
  const fields: Record<string, SchemaField> = {}
  for (const [key, val] of Object.entries(schema)) {
    if (typeof val === 'object' && val !== null && !Array.isArray(val)) {
      fields[key] = {
        type: val.type || 'object',
        description: val.description || '',
        required: val.required || false,
        properties: val.properties || undefined,
      }
    } else {
      fields[key] = { type: typeof val, description: String(val) }
    }
  }
  return fields
}

function addField() {
  const key = `new_field_${Date.now()}`
  schemaFields.value[key] = { type: 'string', description: '', required: false }
  syncJsonEditor()
}

function addNestedObject() {
  if (!selectedField.value) {
    ElMessage.warning('请先选择一个字段')
    return
  }
  const key = `nested_${Date.now()}`
  schemaFields.value[key] = { type: 'object', description: '', properties: {}, _nested: true }
  syncJsonEditor()
}

function setAsArray() {
  if (!selectedField.value) {
    ElMessage.warning('请先选择一个字段')
    return
  }
  schemaFields.value[selectedField.value].type = 'array'
  syncJsonEditor()
}

function deleteSelectedField() {
  if (!selectedField.value) return
  delete schemaFields.value[selectedField.value]
  selectedField.value = ''
  syncJsonEditor()
}

function syncJsonEditor() {
  const schema: Record<string, any> = {}
  for (const [key, field] of Object.entries(schemaFields.value)) {
    schema[key] = { type: field.type, description: field.description }
    if (field.properties) schema[key].properties = field.properties
  }
  jsonEditorContent.value = JSON.stringify(schema, null, 2)
}

async function saveTemplate() {
  if (!currentTemplate.value) return
  saving.value = true
  try {
    await templateStore.updateTemplate(currentTemplate.value.slug, {
      schema: JSON.parse(jsonEditorContent.value),
      system_prompt_suffix: currentTemplate.value.system_prompt_suffix,
    })
    ElMessage.success('模板已保存')
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function resetTemplate() {
  if (!currentTemplate.value) return
  try {
    await ElMessageBox.confirm('确定恢复默认？所有修改将丢失', '确认')
    await templateStore.resetTemplate(currentTemplate.value.slug)
    ElMessage.success('已恢复默认')
    templateStore.fetchTemplates()
  } catch { /* cancelled */ }
}

async function previewTemplate() {
  if (!currentTemplate.value) return
  try {
    const res = await templateStore.previewTemplate(currentTemplate.value.slug)
    previewContent.value = JSON.stringify(res, null, 2)
    showPreview.value = true
  } catch (e: any) {
    ElMessage.error(e.message || '预览失败')
  }
}

function handleExport(cmd: string) {
  if (cmd === 'json') {
    const blob = new Blob([jsonEditorContent.value], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${currentTemplate.value?.slug || 'template'}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } else if (cmd === 'import') {
    ElMessage.info('请选择 JSON 文件导入')
  }
}

async function createTemplate() {
  if (!createForm.name || !createForm.slug) {
    ElMessage.warning('请填写名称和标识')
    return
  }
  try {
    await templateStore.createTemplate({
      name: createForm.name,
      slug: createForm.slug,
      category: createForm.category as any,
      description: createForm.description,
      schema: {},
      example: {},
      system_prompt_suffix: '',
    })
    showCreateDialog.value = false
    ElMessage.success('模板创建成功')
  } catch (e: any) {
    ElMessage.error(e.message || '创建失败')
  }
}

onMounted(() => {
  templateStore.fetchTemplates()
})
</script>

<style scoped>
.template-workshop { padding: 24px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h1 { margin: 0; font-size: 22px; }
.template-list-card { height: calc(100vh - 140px); overflow-y: auto; }
.template-items { display: flex; flex-direction: column; gap: 6px; }
.template-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-radius: 8px; cursor: pointer; transition: background 0.2s; }
.template-item:hover { background: var(--el-fill-color-light); }
.template-item.active { background: var(--el-color-primary-light-9); border: 1px solid var(--el-color-primary-light-5); }
.tpl-name { font-weight: 600; font-size: 14px; }
.tpl-meta { font-size: 12px; color: var(--el-text-color-secondary); }
.tpl-info { display: flex; flex-direction: column; gap: 2px; }
.editor-header { display: flex; justify-content: space-between; align-items: flex-start; }
.editor-header h3 { margin: 0; }
.tpl-desc { font-size: 13px; color: var(--el-text-color-secondary); margin: 4px 0 0; }
.editor-actions { display: flex; gap: 6px; flex-shrink: 0; }
.schema-toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
.schema-tree { border: 1px solid var(--el-border-color-lighter); border-radius: 8px; padding: 8px; min-height: 200px; }
.field-item { padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.15s; }
.field-item:hover { background: var(--el-fill-color-light); }
.field-item.active { background: var(--el-color-primary-light-9); }
.field-item.nested { padding-left: 24px; }
.field-row { display: flex; align-items: center; gap: 8px; }
.field-key { font-weight: 600; font-size: 13px; min-width: 80px; }
.required-badge { color: var(--el-color-danger); font-weight: 700; }
.nested-fields { margin-left: 20px; }
.json-textarea { font-family: 'Fira Code', 'Consolas', monospace; font-size: 13px; }
.preview-content { background: #f5f7fa; padding: 16px; border-radius: 8px; font-size: 13px; max-height: 400px; overflow: auto; white-space: pre-wrap; }
.empty-state { padding: 80px 0; }
</style>
