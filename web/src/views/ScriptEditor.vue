<template>
  <div class="script-editor">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>写剧本</h1>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="generateScript" :loading="generating">
          <el-icon><MagicStick /></el-icon> AI 生成剧本
        </el-button>
      </div>
    </header>

    <div class="editor-layout">
      <!-- 左侧大纲树 -->
      <aside class="outline-panel">
        <div class="panel-header">
          <span>大纲</span>
          <el-button text size="small" @click="addEpisode"><el-icon><Plus /></el-icon></el-button>
        </div>
        <el-tree
          :data="outlineTree"
          :props="{ children: 'children', label: 'label' }"
          node-key="id"
          highlight-current
          default-expand-all
          @node-click="handleNodeClick"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <el-icon v-if="data.type === 'episode'"><Document /></el-icon>
              <el-icon v-else-if="data.type === 'scene'"><Film /></el-icon>
              <el-icon v-else><View /></el-icon>
              <span>{{ node.label }}</span>
            </div>
          </template>
        </el-tree>
      </aside>

      <!-- 右侧编辑区 -->
      <main class="edit-panel">
        <!-- 未选中 -->
        <div v-if="!selectedNode" class="empty-hint">
          <el-empty description="从左侧大纲选择集/场景/镜头开始编辑" />
        </div>

        <!-- 集编辑 -->
        <div v-else-if="selectedNode.type === 'episode'" class="episode-edit">
          <h2>{{ selectedNode.label }}</h2>
          <el-form label-width="80px">
            <el-form-item label="标题">
              <el-input v-model="episodeForm.title" />
            </el-form-item>
            <el-form-item label="梗概">
              <el-input v-model="episodeForm.synopsis" type="textarea" :rows="4" placeholder="输入本集概要…" />
            </el-form-item>
          </el-form>
          <el-button type="primary" size="small" @click="addScene(selectedNode.id)">添加场景</el-button>
        </div>

        <!-- 场景编辑 -->
        <div v-else-if="selectedNode.type === 'scene'" class="scene-edit">
          <h2>{{ selectedNode.label }}</h2>
          <el-form label-width="80px">
            <el-form-item label="地点">
              <el-input v-model="sceneForm.location" />
            </el-form-item>
            <el-form-item label="时间">
              <el-select v-model="sceneForm.time_of_day">
                <el-option label="清晨" value="dawn" />
                <el-option label="白天" value="day" />
                <el-option label="傍晚" value="dusk" />
                <el-option label="夜晚" value="night" />
              </el-select>
            </el-form-item>
            <el-form-item label="天气">
              <el-input v-model="sceneForm.weather" placeholder="晴/雨/雪" />
            </el-form-item>
            <el-form-item label="氛围">
              <el-input v-model="sceneForm.atmosphere" placeholder="紧张/温馨/悲伤" />
            </el-form-item>
            <el-form-item label="角色">
              <el-select v-model="sceneForm.characters_present" multiple placeholder="选择出场角色">
                <el-option v-for="c in characters" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="背景音乐">
              <el-input v-model="sceneForm.background_music" placeholder="描述背景音乐风格" />
            </el-form-item>
            <el-form-item label="环境音">
              <el-input v-model="sceneForm.ambient_sound" placeholder="描述环境声音" />
            </el-form-item>
          </el-form>
          <el-button type="primary" size="small" @click="addShot(selectedNode.id)">添加镜头</el-button>
        </div>

        <!-- 镜头编辑 -->
        <div v-else-if="selectedNode.type === 'shot'" class="shot-edit">
          <h2>{{ selectedNode.label }}</h2>
          <el-form label-width="100px">
            <el-form-item label="镜头类型">
              <el-select v-model="shotForm.shot_type">
                <el-option label="特写" value="closeup" />
                <el-option label="中景" value="medium" />
                <el-option label="远景" value="wide" />
                <el-option label="俯拍" value="overhead" />
              </el-select>
            </el-form-item>
            <el-form-item label="运镜">
              <el-select v-model="shotForm.camera_movement">
                <el-option label="固定" value="static" />
                <el-option label="横摇" value="pan" />
                <el-option label="纵摇" value="tilt" />
                <el-option label="推拉" value="zoom" />
                <el-option label="跟踪" value="tracking" />
              </el-select>
            </el-form-item>
            <el-form-item label="时长(秒)">
              <el-input-number v-model="shotForm.duration_sec" :min="0.5" :max="30" :step="0.5" />
            </el-form-item>
            <el-form-item label="画面描述">
              <el-input v-model="shotForm.visual_description" type="textarea" :rows="3" placeholder="描述这个镜头的画面内容…" />
            </el-form-item>
            <el-form-item label="旁白">
              <el-input v-model="shotForm.narration" type="textarea" :rows="2" placeholder="旁白文本（可选）" />
            </el-form-item>
          </el-form>

          <!-- 台词列表 -->
          <div class="dialogues-section">
            <div class="section-header">
              <h3>台词</h3>
              <el-button size="small" @click="addDialogue"><el-icon><Plus /></el-icon> 添加台词</el-button>
            </div>
            <div v-for="(d, idx) in shotForm.dialogues" :key="idx" class="dialogue-card">
              <div class="dialogue-header">
                <el-select v-model="d.character_id" placeholder="选择角色" size="small" style="width: 140px">
                  <el-option v-for="c in characters" :key="c.id" :label="c.name" :value="c.id" />
                </el-select>
                <el-select v-model="d.emotion" size="small" style="width: 100px">
                  <el-option label="开心" value="happy" />
                  <el-option label="悲伤" value="sad" />
                  <el-option label="愤怒" value="angry" />
                  <el-option label="恐惧" value="fearful" />
                  <el-option label="惊讶" value="surprised" />
                  <el-option label="平静" value="calm" />
                  <el-option label="低语" value="whisper" />
                </el-select>
                <el-select v-model="d.volume" size="small" style="width: 90px">
                  <el-option label="低语" value="whisper" />
                  <el-option label="正常" value="normal" />
                  <el-option label="大声" value="loud" />
                  <el-option label="呐喊" value="shout" />
                </el-select>
                <el-select v-model="d.pace" size="small" style="width: 80px">
                  <el-option label="慢" value="slow" />
                  <el-option label="正常" value="normal" />
                  <el-option label="快" value="fast" />
                </el-select>
                <el-button text type="danger" size="small" @click="removeDialogue(idx)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <el-input v-model="d.text" type="textarea" :rows="2" placeholder="台词内容…" />
            </div>
          </div>

          <div class="shot-actions">
            <el-button type="primary" @click="splitToStoryboard">
              <el-icon><Film /></el-icon> 分镜拆解
            </el-button>
            <el-button @click="saveShot">保存镜头</el-button>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Plus, MagicStick, Document, Film, View, Delete } from '@element-plus/icons-vue'
import { useTimelineStore } from '@/stores/timeline'
import { useCharacterStore } from '@/stores/character'
import type { Dialogue } from '@/api'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
const timelineStore = useTimelineStore()
const characterStore = useCharacterStore()

const generating = ref(false)
const selectedNode = ref<{ id: string; type: string; label: string } | null>(null)
const characters = computed(() => characterStore.characters)

interface OutlineNode {
  id: string
  label: string
  type: 'episode' | 'scene' | 'shot'
  children?: OutlineNode[]
}

const outlineTree = computed<OutlineNode[]>(() => {
  return timelineStore.scenes.reduce<OutlineNode[]>((acc, scene) => {
    const episodeNode: OutlineNode = {
      id: scene.episode_id,
      label: `第${scene.scene_number}场 - ${scene.location}`,
      type: 'scene',
      children: (scene.shots || []).map(shot => ({
        id: shot.id,
        label: `镜头${shot.shot_number} [${shot.shot_type}]`,
        type: 'shot' as const,
      })),
    }
    acc.push(episodeNode)
    return acc
  }, [])
})

const episodeForm = reactive({ title: '', synopsis: '' })
const sceneForm = reactive({
  location: '',
  time_of_day: 'day',
  weather: '晴',
  atmosphere: '',
  characters_present: [] as string[],
  background_music: '',
  ambient_sound: '',
})
const shotForm = reactive({
  shot_type: 'medium' as const,
  camera_movement: 'static' as const,
  duration_sec: 3,
  visual_description: '',
  narration: '',
  dialogues: [] as Dialogue[],
})

function handleNodeClick(data: OutlineNode) {
  selectedNode.value = { id: data.id, type: data.type, label: data.label }
}

function addEpisode() {
  ElMessage.info('请通过项目管理添加集数')
}

function addScene(episodeId: string) {
  ElMessage.info(`将在集 ${episodeId} 中添加场景`)
}

function addShot(sceneId: string) {
  ElMessage.info(`将在场景 ${sceneId} 中添加镜头`)
}

function addDialogue() {
  shotForm.dialogues.push({
    id: '',
    character_id: '',
    text: '',
    emotion: 'calm',
    volume: 'normal',
    pace: 'normal',
    pause_after_sec: 0.5,
    overlap_with_previous: false,
  })
}

function removeDialogue(idx: number) {
  shotForm.dialogues.splice(idx, 1)
}

async function generateScript() {
  generating.value = true
  try {
    ElMessage.success('AI 剧本生成任务已提交')
  } catch (e: any) {
    ElMessage.error(e.message || '生成失败')
  } finally {
    generating.value = false
  }
}

async function saveShot() {
  ElMessage.success('镜头已保存')
}

function splitToStoryboard() {
  router.push({ name: 'Storyboard', params: { id: projectId } })
}

onMounted(() => {
  timelineStore.fetchScenes(projectId)
  characterStore.fetchCharacters(projectId)
})
</script>

<style scoped>
.script-editor { padding: 24px; height: 100vh; display: flex; flex-direction: column; box-sizing: border-box; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-shrink: 0; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.editor-layout { display: flex; gap: 16px; flex: 1; min-height: 0; }
.outline-panel { width: 280px; flex-shrink: 0; border: 1px solid var(--el-border-color-light); border-radius: 8px; padding: 12px; overflow-y: auto; background: #fafafa; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-weight: 600; }
.tree-node { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.edit-panel { flex: 1; border: 1px solid var(--el-border-color-light); border-radius: 8px; padding: 20px; overflow-y: auto; }
.episode-edit h2, .scene-edit h2, .shot-edit h2 { margin: 0 0 16px; font-size: 18px; }
.dialogues-section { margin-top: 20px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-header h3 { margin: 0; font-size: 15px; }
.dialogue-card { border: 1px solid var(--el-border-color-lighter); border-radius: 8px; padding: 12px; margin-bottom: 8px; }
.dialogue-header { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }
.shot-actions { display: flex; gap: 8px; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--el-border-color-lighter); }
.empty-hint { display: flex; align-items: center; justify-content: center; height: 100%; }
</style>
