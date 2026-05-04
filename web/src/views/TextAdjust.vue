<template>
  <div class="text-adjust">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>改台词</h1>
      </div>
      <div class="header-actions">
        <el-dropdown @command="handleBatch">
          <el-button>批量操作 <el-icon><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="findReplace">查找替换</el-dropdown-item>
              <el-dropdown-item command="batchSpeed">批量调语速</el-dropdown-item>
              <el-dropdown-item command="batchEmotion">批量调情感</el-dropdown-item>
              <el-dropdown-item command="exportScript">导出台词本</el-dropdown-item>
              <el-dropdown-item command="importScript">导入台词本</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <el-row :gutter="20">
      <!-- 场景概要 -->
      <el-col :span="6">
        <el-card class="scene-info">
          <template #header><span>场景概要</span></template>
          <el-descriptions :column="1" size="small">
            <el-descriptions-item label="场景">{{ currentScene?.scene_number || '-' }}</el-descriptions-item>
            <el-descriptions-item label="地点">{{ currentScene?.location || '-' }}</el-descriptions-item>
            <el-descriptions-item label="时间">{{ currentScene?.time_of_day || '-' }}</el-descriptions-item>
            <el-descriptions-item label="氛围">{{ currentScene?.atmosphere || '-' }}</el-descriptions-item>
          </el-descriptions>
          <el-divider />
          <h4>旁白</h4>
          <el-input
            v-model="narrationText"
            type="textarea"
            :rows="3"
            placeholder="场景旁白（可编辑）"
          />
        </el-card>
      </el-col>

      <!-- 台词列表 -->
      <el-col :span="18">
        <div v-if="dialogues.length === 0" class="empty-hint">
          <el-empty description="当前场景无台词" />
        </div>
        <div v-else class="dialogue-list">
          <div v-for="(d, idx) in dialogues" :key="d.id" class="dialogue-card" :class="{ selected: selectedIds.includes(d.id) }">
            <div class="card-header">
              <el-checkbox v-model="d._selected" @change="toggleSelect(d.id)" />
              <span class="char-name">{{ getCharacterName(d.character_id) }}</span>
              <el-tag size="small" :type="emotionTagType(d.emotion)">{{ emotionLabel(d.emotion) }}</el-tag>
              <span class="line-number">#{{ idx + 1 }}</span>
            </div>
            <el-input
              v-model="d.text"
              type="textarea"
              :rows="2"
              class="dialogue-text"
              @blur="saveDialogueText(d)"
            />
            <div class="card-params">
              <div class="param-item">
                <label>情感</label>
                <el-select v-model="d.emotion" size="small" @change="saveDialogueEmotion(d)">
                  <el-option v-for="e in emotions" :key="e.value" :label="e.label" :value="e.value" />
                </el-select>
              </div>
              <div class="param-item">
                <label>语速</label>
                <el-select v-model="d.pace" size="small" @change="saveDialogueEmotion(d)">
                  <el-option label="慢" value="slow" />
                  <el-option label="正常" value="normal" />
                  <el-option label="快" value="fast" />
                </el-select>
              </div>
              <div class="param-item">
                <label>音量</label>
                <el-select v-model="d.volume" size="small" @change="saveDialogueEmotion(d)">
                  <el-option label="低语" value="whisper" />
                  <el-option label="正常" value="normal" />
                  <el-option label="大声" value="loud" />
                  <el-option label="呐喊" value="shout" />
                </el-select>
              </div>
              <div class="param-item">
                <label>停顿</label>
                <el-input-number v-model="d.pause_after_sec" :min="0" :max="5" :step="0.1" size="small" style="width: 90px" />
              </div>
            </div>
            <div class="card-actions">
              <el-button size="small" type="primary" text @click="playDialogue(d)">
                <el-icon><VideoPlay /></el-icon> 试听
              </el-button>
              <el-button size="small" text @click="regenerateVoice(d)">
                <el-icon><RefreshRight /></el-icon> 重新配音
              </el-button>
              <el-popconfirm title="确定删除此台词？" @confirm="deleteDialogue(d.id)">
                <template #reference>
                  <el-button size="small" type="danger" text><el-icon><Delete /></el-icon> 删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 查找替换弹窗 -->
    <el-dialog v-model="showFindReplace" title="查找替换" width="480px">
      <el-form label-width="60px">
        <el-form-item label="查找">
          <el-input v-model="findText" placeholder="输入要查找的文本" />
        </el-form-item>
        <el-form-item label="替换">
          <el-input v-model="replaceText" placeholder="输入替换文本" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFindReplace = false">取消</el-button>
        <el-button type="primary" @click="doFindReplace">全部替换</el-button>
      </template>
    </el-dialog>

    <!-- 批量调语速/情感弹窗 -->
    <el-dialog v-model="showBatchParam" :title="batchParamTitle" width="400px">
      <el-form label-width="60px">
        <el-form-item :label="batchParamLabel">
          <el-select v-model="batchParamValue">
            <el-option v-for="o in batchParamOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchParam = false">取消</el-button>
        <el-button type="primary" @click="applyBatchParam">应用</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowDown, VideoPlay, RefreshRight, Delete } from '@element-plus/icons-vue'
import { useTimelineStore } from '@/stores/timeline'
import { useCharacterStore } from '@/stores/character'
import { editorApi } from '@/api/editor'
import { projectApi } from '@/api/project'
import type { Dialogue, Scene } from '@/api'

const route = useRoute()
const projectId = route.params.id as string
const timelineStore = useTimelineStore()
const characterStore = useCharacterStore()
let episodeId = ''

const selectedIds = ref<string[]>([])
const narrationText = ref('')
const showFindReplace = ref(false)
const findText = ref('')
const replaceText = ref('')
const showBatchParam = ref(false)
const batchParamTitle = ref('')
const batchParamLabel = ref('')
const batchParamValue = ref('')
const batchParamType = ref<'speed' | 'emotion'>('speed')

const emotions = [
  { label: '开心', value: 'happy' },
  { label: '悲伤', value: 'sad' },
  { label: '愤怒', value: 'angry' },
  { label: '恐惧', value: 'fearful' },
  { label: '惊讶', value: 'surprised' },
  { label: '平静', value: 'calm' },
  { label: '低语', value: 'whisper' },
]

const batchParamOptions = computed(() => {
  if (batchParamType.value === 'speed') {
    return [{ label: '慢', value: 'slow' }, { label: '正常', value: 'normal' }, { label: '快', value: 'fast' }]
  }
  return emotions
})

interface DialogueWithSelect extends Dialogue {
  _selected?: boolean
}

const currentScene = computed<Scene | null>(() => timelineStore.currentScene)
const dialogues = computed<DialogueWithSelect[]>(() => {
  const scene = currentScene.value
  if (!scene?.shots) return []
  const all: DialogueWithSelect[] = []
  for (const shot of scene.shots) {
    for (const d of shot.dialogues) {
      all.push({ ...d, _selected: selectedIds.value.includes(d.id) })
    }
  }
  return all
})

function getCharacterName(id: string) {
  return characterStore.characters.find(c => c.id === id)?.name || '未知'
}

function emotionLabel(e: string) {
  return emotions.find(em => em.value === e)?.label || e
}

function emotionTagType(e: string) {
  const map: Record<string, string> = { happy: 'success', sad: 'info', angry: 'danger', fearful: 'warning', surprised: '', calm: '', whisper: 'info' }
  return map[e] || ''
}

function toggleSelect(id: string) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

async function saveDialogueText(d: Dialogue) {
  try {
    await editorApi.updateDialogueText(d.id, d.text)
    ElMessage.success('台词已保存')
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  }
}

async function saveDialogueEmotion(d: Dialogue) {
  try {
    await editorApi.updateDialogueEmotion(d.id, {
      emotion: d.emotion,
      volume: d.volume,
      pace: d.pace,
      pause_after_sec: d.pause_after_sec,
    })
    ElMessage.success('参数已保存')
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  }
}

function playDialogue(d: Dialogue) {
  ElMessage.info(`试听台词: "${d.text.substring(0, 20)}…"`)
}

async function regenerateVoice(d: Dialogue) {
  try {
    await editorApi.regenerateVoice(d.id)
    ElMessage.success('重新配音任务已提交')
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  }
}

async function deleteDialogue(id: string) {
  try {
    await editorApi.deleteDialogue(id)
    ElMessage.success('台词已删除')
  } catch (e: any) {
    ElMessage.error(e.message || '删除失败')
  }
}

function handleBatch(cmd: string) {
  if (cmd === 'findReplace') {
    showFindReplace.value = true
  } else if (cmd === 'batchSpeed') {
    batchParamType.value = 'speed'
    batchParamTitle.value = '批量调语速'
    batchParamLabel.value = '语速'
    batchParamValue.value = 'normal'
    showBatchParam.value = true
  } else if (cmd === 'batchEmotion') {
    batchParamType.value = 'emotion'
    batchParamTitle.value = '批量调情感'
    batchParamLabel.value = '情感'
    batchParamValue.value = 'calm'
    showBatchParam.value = true
  } else if (cmd === 'exportScript') {
    ElMessage.success('台词本导出成功')
  } else if (cmd === 'importScript') {
    ElMessage.info('请选择台词本文件')
  }
}

function doFindReplace() {
  let count = 0
  for (const d of dialogues.value) {
    if (d.text.includes(findText.value)) {
      d.text = d.text.replaceAll(findText.value, replaceText.value)
      count++
    }
  }
  showFindReplace.value = false
  ElMessage.success(`已替换 ${count} 处`)
}

function applyBatchParam() {
  const targets = selectedIds.value.length > 0
    ? dialogues.value.filter(d => selectedIds.value.includes(d.id))
    : dialogues.value
  for (const d of targets) {
    if (batchParamType.value === 'speed') d.pace = batchParamValue.value as any
    else d.emotion = batchParamValue.value as any
  }
  showBatchParam.value = false
  ElMessage.success(`已更新 ${targets.length} 条台词`)
}

onMounted(async () => {
  const res = await projectApi.getEpisodes(projectId)
  const episodes = res.data.data
  if (episodes && episodes.length > 0) {
    episodeId = episodes[0].id
    timelineStore.fetchScenes(episodeId)
  }
  characterStore.fetchCharacters(projectId)
})
</script>

<style scoped>
.text-adjust { padding: 24px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.scene-info { position: sticky; top: 24px; }
.dialogue-list { display: flex; flex-direction: column; gap: 12px; }
.dialogue-card { border: 1px solid var(--el-border-color-light); border-radius: 10px; padding: 16px; transition: all 0.2s; background: #fff; }
.dialogue-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.dialogue-card.selected { border-color: var(--el-color-primary); background: var(--el-color-primary-light-9); }
.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.char-name { font-weight: 600; font-size: 14px; }
.line-number { margin-left: auto; font-size: 12px; color: var(--el-text-color-secondary); }
.dialogue-text { margin-bottom: 8px; }
.card-params { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
.param-item { display: flex; align-items: center; gap: 6px; }
.param-item label { font-size: 12px; color: var(--el-text-color-secondary); white-space: nowrap; }
.card-actions { display: flex; gap: 4px; }
.empty-hint { padding: 60px 0; }
</style>
