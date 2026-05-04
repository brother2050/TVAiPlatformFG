<template>
  <div class="timeline-editor">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>时间轴编辑器</h1>
      </div>
      <div class="header-actions">
        <el-button-group>
          <el-button :icon="ZoomOut" @click="zoomOut" />
          <el-button disabled>{{ Math.round(zoom * 100) }}%</el-button>
          <el-button :icon="ZoomIn" @click="zoomIn" />
        </el-button-group>
      </div>
    </header>

    <div class="editor-body">
      <!-- 预览区 -->
      <div class="preview-area">
        <div class="preview-screen">
          <el-icon :size="64" color="#999"><VideoPlay /></el-icon>
          <p>预览画面</p>
        </div>
        <div class="playback-controls">
          <el-button :icon="Back" size="small" @click="skipBack" />
          <el-button :type="timelineStore.playing ? 'warning' : 'primary'" size="small" @click="togglePlay">
            <el-icon><VideoPlay v-if="!timelineStore.playing" /><VideoPause v-else /></el-icon>
          </el-button>
          <el-button :icon="Right" size="small" @click="skipForward" />
          <span class="time-display">{{ formatTime(timelineStore.playheadTime) }} / {{ formatTime(totalDuration) }}</span>
        </div>
      </div>

      <!-- 时间轴 -->
      <div class="timeline-container" ref="timelineRef">
        <!-- 时间刻度 -->
        <div class="time-ruler" :style="{ width: rulerWidth + 'px' }">
          <div v-for="mark in timeMarks" :key="mark" class="time-mark" :style="{ left: mark * zoom * pxPerSec + 'px' }">
            {{ formatTime(mark) }}
          </div>
        </div>

        <!-- 播放头 -->
        <div class="playhead" :style="{ left: timelineStore.playheadTime * zoom * pxPerSec + 'px' }" @mousedown="startDragPlayhead">
          <div class="playhead-line" />
          <div class="playhead-handle" />
        </div>

      <!-- 轨道 -->
      <div class="tracks">
        <!-- 视频轨 -->
        <div class="track" @dragover.prevent @drop="onClipDrop($event, 'video')">
          <div class="track-label">
            <el-icon><VideoCamera /></el-icon>
            <span>视频</span>
          </div>
          <div class="track-content" :style="{ width: rulerWidth + 'px' }">
            <div
              v-for="clip in videoClips"
              :key="clip.id"
              class="clip video-clip"
              :style="clipStyle(clip)"
              draggable="true"
              @dragstart="onClipDragStart($event, clip, 'video')"
              @dragend="onClipDragEnd"
              @mousedown="startClipDrag($event, clip, 'video')"
            >
              <span class="clip-label">{{ clip.label }}</span>
            </div>
          </div>
        </div>

        <!-- 人声轨 -->
        <div class="track" @dragover.prevent @drop="onClipDrop($event, 'voice')">
          <div class="track-label">
            <el-icon><Microphone /></el-icon>
            <span>人声</span>
          </div>
          <div class="track-content" :style="{ width: rulerWidth + 'px' }">
            <div
              v-for="clip in voiceClips"
              :key="clip.id"
              class="clip voice-clip"
              :style="clipStyle(clip)"
              draggable="true"
              @dragstart="onClipDragStart($event, clip, 'voice')"
              @dragend="onClipDragEnd"
              @mousedown="startClipDrag($event, clip, 'voice')"
            >
              <span class="clip-label">{{ clip.label }}</span>
            </div>
          </div>
        </div>

        <!-- BGM轨 -->
        <div class="track" @dragover.prevent @drop="onClipDrop($event, 'bgm')">
          <div class="track-label">
            <el-icon><Headset /></el-icon>
            <span>BGM</span>
          </div>
          <div class="track-content" :style="{ width: rulerWidth + 'px' }">
            <div
              v-for="clip in bgmClips"
              :key="clip.id"
              class="clip bgm-clip"
              :style="clipStyle(clip)"
              draggable="true"
              @dragstart="onClipDragStart($event, clip, 'bgm')"
              @dragend="onClipDragEnd"
              @mousedown="startClipDrag($event, clip, 'bgm')"
            >
              <span class="clip-label">{{ clip.label }}</span>
            </div>
          </div>
        </div>

        <!-- 字幕轨 -->
        <div class="track" @dragover.prevent @drop="onClipDrop($event, 'subtitle')">
          <div class="track-label">
            <el-icon><ChatDotSquare /></el-icon>
            <span>字幕</span>
          </div>
          <div class="track-content" :style="{ width: rulerWidth + 'px' }">
            <div
              v-for="clip in subtitleClips"
              :key="clip.id"
              class="clip subtitle-clip"
              :style="clipStyle(clip)"
              draggable="true"
              @dragstart="onClipDragStart($event, clip, 'subtitle')"
              @dragend="onClipDragEnd"
              @mousedown="startClipDrag($event, clip, 'subtitle')"
            >
              <span class="clip-label">{{ clip.label }}</span>
            </div>
          </div>
        </div>

        <!-- SFX轨 -->
        <div class="track" @dragover.prevent @drop="onClipDrop($event, 'sfx')">
          <div class="track-label">
            <el-icon><Bell /></el-icon>
            <span>音效</span>
          </div>
          <div class="track-content" :style="{ width: rulerWidth + 'px' }">
            <div
              v-for="clip in sfxClips"
              :key="clip.id"
              class="clip sfx-clip"
              :style="clipStyle(clip)"
              draggable="true"
              @dragstart="onClipDragStart($event, clip, 'sfx')"
              @dragend="onClipDragEnd"
              @mousedown="startClipDrag($event, clip, 'sfx')"
            >
              <span class="clip-label">{{ clip.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 剪辑属性面板 -->
      <div v-if="selectedClip" class="clip-properties">
        <div class="properties-header">
          <span>剪辑属性</span>
          <el-button text @click="selectedClip = null"><el-icon><Close /></el-icon></el-button>
        </div>
        <el-form label-width="70px" size="small">
          <el-form-item label="名称">
            <el-input v-model="selectedClip.label" />
          </el-form-item>
          <el-form-item label="起始时间">
            <el-input-number v-model="selectedClip.start" :min="0" :step="0.1" :precision="1" @change="onClipUpdate" />
          </el-form-item>
          <el-form-item label="时长">
            <el-input-number v-model="selectedClip.duration" :min="0.1" :step="0.1" :precision="1" @change="onClipUpdate" />
          </el-form-item>
          <el-form-item label="音量">
            <el-slider v-model="selectedClip.volume" :min="0" :max="100" />
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, VideoPlay, VideoPause, Back, Right,
  ZoomIn, ZoomOut, VideoCamera, Microphone, Headset,
  ChatDotSquare, Bell, Close,
} from '@element-plus/icons-vue'
import { useTimelineStore } from '@/stores/timeline'
import { projectApi } from '@/api/project'

const route = useRoute()
const projectId = route.params.id as string
const timelineStore = useTimelineStore()
const timelineRef = ref<HTMLElement>()
let episodeId = ''

const zoom = ref(1)
const pxPerSec = 60
let playTimer: ReturnType<typeof setInterval> | null = null

interface TimelineClip {
  id: string
  label: string
  start: number
  duration: number
  track: string
  volume?: number
}

const selectedClip = ref<TimelineClip | null>(null)
let dragState: { clip: TimelineClip; type: string; startX: number; originalStart: number } | null = null

const videoClips = ref<TimelineClip[]>([
  { id: 'v1', label: '镜头1', start: 0, duration: 5, track: 'video' },
  { id: 'v2', label: '镜头2', start: 5, duration: 4, track: 'video' },
  { id: 'v3', label: '镜头3', start: 9, duration: 6, track: 'video' },
])
const voiceClips = ref<TimelineClip[]>([
  { id: 'vo1', label: '台词1', start: 0.5, duration: 3, track: 'voice' },
  { id: 'vo2', label: '台词2', start: 5.2, duration: 2.5, track: 'voice' },
])
const bgmClips = ref<TimelineClip[]>([
  { id: 'b1', label: '主题曲', start: 0, duration: 15, track: 'bgm' },
])
const subtitleClips = ref<TimelineClip[]>([
  { id: 's1', label: '字幕1', start: 0.5, duration: 3, track: 'subtitle' },
  { id: 's2', label: '字幕2', start: 5.2, duration: 2.5, track: 'subtitle' },
])
const sfxClips = ref<TimelineClip[]>([
  { id: 'fx1', label: '开门声', start: 4.8, duration: 0.5, track: 'sfx' },
])

const totalDuration = computed(() => {
  const all = [...videoClips.value, ...voiceClips.value, ...bgmClips.value, ...subtitleClips.value, ...sfxClips.value]
  return Math.max(...all.map(c => c.start + c.duration), 15)
})

const rulerWidth = computed(() => Math.max(totalDuration.value * zoom.value * pxPerSec + 100, 800))

const timeMarks = computed(() => {
  const marks: number[] = []
  const step = zoom.value < 0.5 ? 5 : zoom.value < 1 ? 2 : 1
  for (let t = 0; t <= totalDuration.value + 5; t += step) {
    marks.push(t)
  }
  return marks
})

function clipStyle(clip: TimelineClip) {
  return {
    left: clip.start * zoom.value * pxPerSec + 'px',
    width: Math.max(clip.duration * zoom.value * pxPerSec - 2, 10) + 'px',
  }
}

function formatTime(sec: number) {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  const ms = Math.floor((sec % 1) * 10)
  return `${m}:${String(s).padStart(2, '0')}.${ms}`
}

function togglePlay() {
  timelineStore.playing = !timelineStore.playing
  if (timelineStore.playing) {
    playTimer = setInterval(() => {
      timelineStore.playheadTime += 0.1
      if (timelineStore.playheadTime >= totalDuration.value) {
        timelineStore.playing = false
        if (playTimer) clearInterval(playTimer)
      }
    }, 100)
  } else {
    if (playTimer) clearInterval(playTimer)
  }
}

function skipBack() {
  timelineStore.playheadTime = Math.max(0, timelineStore.playheadTime - 2)
}

function skipForward() {
  timelineStore.playheadTime = Math.min(totalDuration.value, timelineStore.playheadTime + 2)
}

function zoomIn() { zoom.value = Math.min(4, zoom.value * 1.25) }
function zoomOut() { zoom.value = Math.max(0.1, zoom.value / 1.25) }

function startDragPlayhead(e: MouseEvent) {
  const startX = e.clientX
  const startTime = timelineStore.playheadTime
  const onMove = (ev: MouseEvent) => {
    const dx = ev.clientX - startX
    timelineStore.playheadTime = Math.max(0, startTime + dx / (zoom.value * pxPerSec))
  }
  const onUp = () => {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

// 拖拽开始
function onClipDragStart(e: DragEvent, clip: TimelineClip, type: string) {
  e.dataTransfer!.setData('application/json', JSON.stringify({ id: clip.id, track: type }))
  e.dataTransfer!.effectAllowed = 'move'
}

// 拖拽结束
function onClipDragEnd() {
  // cleanup if needed
}

// 鼠标拖拽剪辑
function startClipDrag(e: MouseEvent, clip: TimelineClip, type: string) {
  if (e.button !== 0) return
  selectedClip.value = clip
  dragState = {
    clip,
    type,
    startX: e.clientX,
    originalStart: clip.start,
  }

  const onMove = (ev: MouseEvent) => {
    if (!dragState) return
    const dx = ev.clientX - dragState.startX
    const newStart = Math.max(0, dragState.originalStart + dx / (zoom.value * pxPerSec))
    dragState.clip.start = Math.round(newStart * 10) / 10
  }

  const onUp = () => {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
    dragState = null
    saveTimelineState()
  }

  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

// 轨道放下处理
function onClipDrop(e: DragEvent, targetTrack: string) {
  e.preventDefault()
  const data = e.dataTransfer?.getData('application/json')
  if (!data) return

  try {
    const { id, track } = JSON.parse(data)
    if (track === targetTrack) return // 同一轨道不处理

    // 从原轨道移除
    const sourceClips = getTrackClips(track)
    const clipIndex = sourceClips.findIndex(c => c.id === id)
    if (clipIndex === -1) return
    const [clip] = sourceClips.splice(clipIndex, 1)

    // 添加到目标轨道
    const targetClips = getTrackClips(targetTrack)
    clip.track = targetTrack
    targetClips.push(clip)

    saveTimelineState()
    ElMessage.success(`已将「${clip.label}」移动到${getTrackName(targetTrack)}轨道`)
  } catch {
    ElMessage.error('移动失败')
  }
}

function getTrackClips(track: string): TimelineClip[] {
  switch (track) {
    case 'video': return videoClips.value
    case 'voice': return voiceClips.value
    case 'bgm': return bgmClips.value
    case 'subtitle': return subtitleClips.value
    case 'sfx': return sfxClips.value
    default: return []
  }
}

function getTrackName(track: string): string {
  const names: Record<string, string> = {
    video: '视频', voice: '人声', bgm: 'BGM', subtitle: '字幕', sfx: '音效',
  }
  return names[track] || track
}

function onClipUpdate() {
  saveTimelineState()
}

async function saveTimelineState() {
  // 保存时间轴状态到后端
  try {
    const timeline = {
      video: videoClips.value,
      voice: voiceClips.value,
      bgm: bgmClips.value,
      subtitle: subtitleClips.value,
      sfx: sfxClips.value,
    }
    console.log('Timeline saved:', timeline)
  } catch (e) {
    console.error('Save failed:', e)
  }
}

onMounted(async () => {
  const res = await projectApi.getEpisodes(projectId)
  const episodes = res.data.data
  if (episodes && episodes.length > 0) {
    episodeId = episodes[0].id
    timelineStore.fetchScenes(episodeId)
  }
})

onUnmounted(() => {
  if (playTimer) clearInterval(playTimer)
})
</script>

<style scoped>
.timeline-editor { padding: 16px 24px; height: 100vh; display: flex; flex-direction: column; box-sizing: border-box; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-shrink: 0; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 20px; }
.editor-body { flex: 1; display: flex; flex-direction: column; gap: 12px; min-height: 0; position: relative; }
.preview-area { flex-shrink: 0; display: flex; flex-direction: column; align-items: center; gap: 12px; }
.preview-screen { width: 480px; height: 270px; background: #1a1a2e; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #666; }
.playback-controls { display: flex; align-items: center; gap: 8px; }
.time-display { font-family: monospace; font-size: 14px; color: var(--el-text-color-regular); margin-left: 12px; }
.timeline-container { flex: 1; overflow-x: auto; overflow-y: auto; border: 1px solid var(--el-border-color-light); border-radius: 8px; position: relative; background: #fafafa; min-height: 0; }
.time-ruler { height: 30px; position: relative; border-bottom: 1px solid var(--el-border-color); background: #f0f0f0; }
.time-mark { position: absolute; top: 4px; font-size: 11px; color: var(--el-text-color-secondary); transform: translateX(-50%); }
.playhead { position: absolute; top: 0; bottom: 0; width: 2px; z-index: 10; pointer-events: none; }
.playhead-line { width: 2px; height: 100%; background: var(--el-color-danger); }
.playhead-handle { position: absolute; top: -2px; left: -6px; width: 14px; height: 14px; background: var(--el-color-danger); border-radius: 50%; cursor: pointer; pointer-events: auto; }
.tracks { display: flex; flex-direction: column; }
.track { display: flex; min-height: 50px; border-bottom: 1px solid var(--el-border-color-lighter); transition: background 0.2s; }
.track:hover { background: rgba(64, 158, 255, 0.05); }
.track-label { width: 80px; flex-shrink: 0; display: flex; align-items: center; gap: 4px; padding: 0 8px; font-size: 12px; font-weight: 600; color: var(--el-text-color-secondary); background: #f5f5f5; border-right: 1px solid var(--el-border-color-lighter); }
.track-content { position: relative; height: 46px; }
.clip { position: absolute; top: 4px; height: 38px; border-radius: 6px; display: flex; align-items: center; padding: 0 8px; cursor: grab; font-size: 11px; overflow: hidden; user-select: none; transition: box-shadow 0.2s, transform 0.1s; }
.clip:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.2); transform: translateY(-1px); }
.clip-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #fff; font-weight: 500; }
.video-clip { background: var(--el-color-primary); }
.voice-clip { background: var(--el-color-success); }
.bgm-clip { background: var(--el-color-warning); }
.subtitle-clip { background: var(--el-color-info); }
.sfx-clip { background: #9b59b6; }
.clip-properties { position: absolute; right: 16px; top: 50%; transform: translateY(-50%); width: 280px; background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); padding: 16px; z-index: 20; }
.properties-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid var(--el-border-color-lighter); }
.properties-header span { font-weight: 600; font-size: 14px; }
</style>
