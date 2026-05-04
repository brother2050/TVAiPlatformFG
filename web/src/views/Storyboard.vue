<template>
  <div class="storyboard">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>分镜板</h1>
      </div>
      <div class="header-actions">
        <el-select v-model="filterSceneId" placeholder="筛选场景" clearable style="width: 200px">
          <el-option v-for="s in scenes" :key="s.id" :label="`场景${s.scene_number} - ${s.location}`" :value="s.id" />
        </el-select>
      </div>
    </header>

    <div v-if="filteredShots.length === 0" class="empty-state">
      <el-empty description="暂无分镜，请先在「写剧本」中创建场景和镜头" />
    </div>

    <!-- 分镜网格 -->
    <div class="storyboard-grid" ref="gridRef">
      <div
        v-for="(shot, index) in filteredShots"
        :key="shot.id"
        class="storyboard-card"
        draggable="true"
        @dragstart="onDragStart($event, index)"
        @dragover.prevent="onDragOver($event, index)"
        @drop="onDrop($event, index)"
        @click="openDetail(shot)"
      >
        <div class="card-number">{{ index + 1 }}</div>
        <div class="card-thumbnail">
          <div class="thumbnail-placeholder">
            <el-icon :size="32"><Picture /></el-icon>
            <span class="shot-type-badge">{{ shotTypeLabel(shot.shot_type) }}</span>
          </div>
        </div>
        <div class="card-info">
          <p class="camera-info">{{ movementLabel(shot.camera_movement) }} · {{ shot.duration_sec }}s</p>
          <p class="visual-desc">{{ truncate(shot.visual_description, 60) }}</p>
          <div v-if="shot.dialogues.length > 0" class="dialogue-preview">
            <div v-for="d in shot.dialogues.slice(0, 2)" :key="d.id" class="dialogue-line">
              <span class="char-name">{{ getCharacterName(d.character_id) }}:</span>
              <span>{{ truncate(d.text, 30) }}</span>
            </div>
            <span v-if="shot.dialogues.length > 2" class="more-lines">+{{ shot.dialogues.length - 2 }}句</span>
          </div>
          <p v-if="shot.narration" class="narration-preview">
            <el-icon><Edit /></el-icon> {{ truncate(shot.narration, 40) }}
          </p>
        </div>
        <div class="card-drag-handle"><el-icon><Rank /></el-icon></div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="showDetail" title="分镜详情" width="700px" destroy-on-close>
      <div v-if="detailShot" class="detail-content">
        <div class="detail-thumbnail">
          <div class="thumbnail-large">
            <el-icon :size="64"><Picture /></el-icon>
          </div>
        </div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="镜头类型">{{ shotTypeLabel(detailShot.shot_type) }}</el-descriptions-item>
          <el-descriptions-item label="运镜">{{ movementLabel(detailShot.camera_movement) }}</el-descriptions-item>
          <el-descriptions-item label="时长">{{ detailShot.duration_sec }}秒</el-descriptions-item>
          <el-descriptions-item label="情绪标签">
            <el-tag v-for="t in detailShot.emotion_tags" :key="t" size="small" class="mr-1">{{ t }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="画面描述" :span="2">{{ detailShot.visual_description }}</el-descriptions-item>
          <el-descriptions-item v-if="detailShot.narration" label="旁白" :span="2">{{ detailShot.narration }}</el-descriptions-item>
        </el-descriptions>

        <h4>台词</h4>
        <div v-for="d in detailShot.dialogues" :key="d.id" class="detail-dialogue">
          <el-tag size="small">{{ getCharacterName(d.character_id) }}</el-tag>
          <el-tag size="small" type="info">{{ d.emotion }}</el-tag>
          <span class="dialogue-text">{{ d.text }}</span>
        </div>
        <div v-if="detailShot.dialogues.length === 0" class="no-dialogue">无台词</div>
      </div>
      <template #footer>
        <el-button @click="showDetail = false">关闭</el-button>
        <el-button type="primary" @click="editShot">编辑镜头</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Picture, Edit, Rank } from '@element-plus/icons-vue'
import { useTimelineStore } from '@/stores/timeline'
import { useCharacterStore } from '@/stores/character'
import { projectApi } from '@/api/project'
import type { Shot } from '@/api'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
const timelineStore = useTimelineStore()
const characterStore = useCharacterStore()
let episodeId = ''

const filterSceneId = ref('')
const showDetail = ref(false)
const detailShot = ref<Shot | null>(null)
const dragIndex = ref(-1)

const scenes = computed(() => timelineStore.scenes)

const allShots = computed(() => {
  const shots: (Shot & { sceneId: string })[] = []
  for (const scene of timelineStore.scenes) {
    for (const shot of scene.shots || []) {
      shots.push({ ...shot, sceneId: scene.id })
    }
  }
  return shots
})

const filteredShots = computed(() => {
  if (!filterSceneId.value) return allShots.value
  return allShots.value.filter(s => s.sceneId === filterSceneId.value)
})

function shotTypeLabel(type: string) {
  const map: Record<string, string> = { closeup: '特写', medium: '中景', wide: '远景', overhead: '俯拍' }
  return map[type] || type
}

function movementLabel(m: string) {
  const map: Record<string, string> = { static: '固定', pan: '横摇', tilt: '纵摇', zoom: '推拉', tracking: '跟踪' }
  return map[m] || m
}

function getCharacterName(id: string) {
  return characterStore.characters.find(c => c.id === id)?.name || '未知角色'
}

function truncate(text: string, len: number) {
  return text.length > len ? text.slice(0, len) + '…' : text
}

function openDetail(shot: Shot) {
  detailShot.value = shot
  showDetail.value = true
}

function editShot() {
  showDetail.value = false
  router.push({ name: 'Script', params: { id: projectId } })
}

// 拖拽排序
function onDragStart(e: DragEvent, index: number) {
  dragIndex.value = index
  e.dataTransfer!.effectAllowed = 'move'
}

function onDragOver(e: DragEvent, _index: number) {
  e.dataTransfer!.dropEffect = 'move'
}

function onDrop(e: DragEvent, dropIndex: number) {
  e.preventDefault()
  if (dragIndex.value === dropIndex) return
  const items = [...filteredShots.value]
  const [moved] = items.splice(dragIndex.value, 1)
  items.splice(dropIndex, 0, moved)
  dragIndex.value = -1
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
.storyboard { padding: 24px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.storyboard-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
.storyboard-card { border: 1px solid var(--el-border-color-light); border-radius: 12px; overflow: hidden; cursor: pointer; transition: all 0.2s; position: relative; background: #fff; }
.storyboard-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); transform: translateY(-2px); }
.storyboard-card[draggable="true"]:active { opacity: 0.7; }
.card-number { position: absolute; top: 8px; left: 8px; background: var(--el-color-primary); color: #fff; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; z-index: 1; }
.card-thumbnail { height: 140px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); display: flex; align-items: center; justify-content: center; position: relative; }
.thumbnail-placeholder { color: var(--el-text-color-placeholder); display: flex; flex-direction: column; align-items: center; gap: 4px; }
.shot-type-badge { position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.6); color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
.card-info { padding: 12px; }
.camera-info { font-size: 12px; color: var(--el-text-color-secondary); margin: 0 0 4px; }
.visual-desc { font-size: 13px; margin: 0 0 8px; line-height: 1.4; }
.dialogue-preview { background: var(--el-fill-color-lighter); border-radius: 6px; padding: 8px; margin-bottom: 8px; }
.dialogue-line { font-size: 12px; margin-bottom: 2px; }
.char-name { font-weight: 600; color: var(--el-color-primary); }
.more-lines { font-size: 11px; color: var(--el-text-color-secondary); }
.narration-preview { font-size: 12px; color: var(--el-text-color-secondary); margin: 0; display: flex; align-items: center; gap: 4px; }
.card-drag-handle { position: absolute; top: 8px; right: 8px; cursor: grab; color: var(--el-text-color-placeholder); }
.detail-content { display: flex; flex-direction: column; gap: 16px; }
.thumbnail-large { height: 200px; background: linear-gradient(135deg, #f5f7fa, #c3cfe2); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--el-text-color-placeholder); }
.detail-content h4 { margin: 8px 0; }
.detail-dialogue { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid var(--el-border-color-lighter); }
.dialogue-text { font-size: 14px; }
.no-dialogue { color: var(--el-text-color-secondary); font-size: 13px; }
.mr-1 { margin-right: 4px; }
.empty-state { padding: 80px 0; }
</style>
