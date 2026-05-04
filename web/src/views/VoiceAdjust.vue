<template>
  <div class="voice-adjust">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>调配音</h1>
      </div>
    </header>

    <el-row :gutter="20">
      <!-- 波形和控制 -->
      <el-col :span="16">
        <el-card class="waveform-card">
          <template #header>
            <div class="wf-header">
              <span>配音波形</span>
              <span class="current-line">{{ currentDialogue?.text?.substring(0, 30) || '未选择台词' }}…</span>
            </div>
          </template>

          <!-- 波形展示区 -->
          <div class="waveform-display">
            <div class="waveform-bars">
              <div v-for="(bar, i) in waveformBars" :key="i" class="wf-bar" :style="{ height: bar + '%' }" />
            </div>
            <div class="playhead-indicator" :style="{ left: playProgress + '%' }" />
          </div>

          <!-- 播放控制 -->
          <div class="playback-bar">
            <el-button-group>
              <el-button :icon="RefreshLeft" size="small" @click="seekTo(0)" />
              <el-button :type="isPlaying ? 'warning' : 'primary'" size="small" @click="togglePlay">
                <el-icon><VideoPlay v-if="!isPlaying" /><VideoPause v-else /></el-icon>
              </el-button>
              <el-button size="small" @click="toggleLoop" :type="isLoop ? 'success' : ''">
                <el-icon><RefreshRight /></el-icon>
              </el-button>
            </el-button-group>
            <span class="time-info">{{ formatTime(currentTime) }} / {{ formatTime(totalDuration) }}</span>
            <el-slider v-model="playProgress" :min="0" :max="100" :show-tooltip="false" style="flex: 1; margin: 0 16px" />
          </div>

          <!-- 参数调节 -->
          <div class="params-section">
            <h4>参数调节</h4>
            <el-row :gutter="16">
              <el-col :span="6">
                <div class="param-control">
                  <label>情感</label>
                  <el-select v-model="voiceParams.emotion" size="small">
                    <el-option label="开心" value="happy" />
                    <el-option label="悲伤" value="sad" />
                    <el-option label="愤怒" value="angry" />
                    <el-option label="平静" value="calm" />
                    <el-option label="低语" value="whisper" />
                  </el-select>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="param-control">
                  <label>语速 {{ voiceParams.speed }}x</label>
                  <el-slider v-model="voiceParams.speed" :min="0.5" :max="2" :step="0.1" />
                </div>
              </el-col>
              <el-col :span="6">
                <div class="param-control">
                  <label>音调 {{ voiceParams.pitch }}</label>
                  <el-slider v-model="voiceParams.pitch" :min="-10" :max="10" :step="1" />
                </div>
              </el-col>
              <el-col :span="6">
                <div class="param-control">
                  <label>音量 {{ voiceParams.volume }}%</label>
                  <el-slider v-model="voiceParams.volume" :min="0" :max="100" />
                </div>
              </el-col>
            </el-row>
          </div>

          <!-- 操作按钮 -->
          <div class="action-bar">
            <el-button type="primary" @click="saveParams">
              <el-icon><Check /></el-icon> 保存参数
            </el-button>
            <el-button @click="regenerateVoice" :loading="regenerating">
              <el-icon><RefreshRight /></el-icon> 重新生成
            </el-button>
            <el-upload :show-file-list="false" :before-upload="handleUpload" accept="audio/*">
              <el-button><el-icon><Upload /></el-icon> 上传替换</el-button>
            </el-upload>
          </div>
        </el-card>
      </el-col>

      <!-- 台词列表 -->
      <el-col :span="8">
        <el-card class="dialogue-list-card">
          <template #header><span>本场景台词</span></template>
          <div class="dialogue-items">
            <div
              v-for="d in sceneDialogues"
              :key="d.id"
              class="dialogue-item"
              :class="{ active: currentDialogue?.id === d.id }"
              @click="selectDialogue(d)"
            >
              <div class="di-header">
                <el-avatar :size="28" class="di-avatar">{{ getCharName(d.character_id).charAt(0) }}</el-avatar>
                <span class="di-name">{{ getCharName(d.character_id) }}</span>
                <el-tag size="small" :type="emotionType(d.emotion)">{{ emotionLabel(d.emotion) }}</el-tag>
              </div>
              <p class="di-text">{{ d.text }}</p>
              <div class="di-meta">
                <span>{{ d.pace === 'slow' ? '慢' : d.pace === 'fast' ? '快' : '正常' }}</span>
                <span>{{ d.volume === 'whisper' ? '低语' : d.volume === 'loud' ? '大声' : d.volume === 'shout' ? '呐喊' : '正常' }}</span>
              </div>
            </div>
            <div v-if="sceneDialogues.length === 0" class="no-dialogues">本场景无台词</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, VideoPlay, VideoPause, RefreshRight, RefreshLeft, Check, Upload } from '@element-plus/icons-vue'
import { useTimelineStore } from '@/stores/timeline'
import { useCharacterStore } from '@/stores/character'
import { editorApi } from '@/api/editor'
import { projectApi } from '@/api/project'
import type { Dialogue } from '@/api'

const route = useRoute()
const projectId = route.params.id as string
const timelineStore = useTimelineStore()
const characterStore = useCharacterStore()
let episodeId = ''

const currentDialogue = ref<Dialogue | null>(null)
const isPlaying = ref(false)
const isLoop = ref(false)
const playProgress = ref(0)
const currentTime = ref(0)
const totalDuration = ref(5)
const regenerating = ref(false)
let playTimer: ReturnType<typeof setInterval> | null = null

const voiceParams = reactive({
  emotion: 'calm' as string,
  speed: 1,
  pitch: 0,
  volume: 80,
})

// 生成模拟波形数据
const waveformBars = computed(() => {
  return Array.from({ length: 80 }, () => 20 + Math.random() * 60)
})

const sceneDialogues = computed(() => {
  const scene = timelineStore.currentScene
  if (!scene?.shots) return []
  const all: Dialogue[] = []
  for (const shot of scene.shots) {
    all.push(...shot.dialogues)
  }
  return all
})

function getCharName(id: string) {
  return characterStore.characters.find(c => c.id === id)?.name || '未知'
}

function emotionLabel(e: string) {
  const map: Record<string, string> = { happy: '开心', sad: '悲伤', angry: '愤怒', fearful: '恐惧', surprised: '惊讶', calm: '平静', whisper: '低语' }
  return map[e] || e
}

function emotionType(e: string) {
  const map: Record<string, string> = { happy: 'success', sad: 'info', angry: 'danger', calm: '', whisper: 'info' }
  return map[e] || ''
}

function formatTime(sec: number) {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

function selectDialogue(d: Dialogue) {
  currentDialogue.value = d
  voiceParams.emotion = d.emotion
  voiceParams.speed = d.pace === 'slow' ? 0.8 : d.pace === 'fast' ? 1.3 : 1
  voiceParams.volume = d.volume === 'whisper' ? 30 : d.volume === 'loud' ? 90 : d.volume === 'shout' ? 100 : 70
  playProgress.value = 0
  currentTime.value = 0
  totalDuration.value = d.text.length * 0.15 + 1
}

function togglePlay() {
  isPlaying.value = !isPlaying.value
  if (isPlaying.value) {
    playTimer = setInterval(() => {
      currentTime.value += 0.1
      playProgress.value = (currentTime.value / totalDuration.value) * 100
      if (currentTime.value >= totalDuration.value) {
        if (isLoop.value) {
          currentTime.value = 0
        } else {
          isPlaying.value = false
          if (playTimer) clearInterval(playTimer)
        }
      }
    }, 100)
  } else {
    if (playTimer) clearInterval(playTimer)
  }
}

function toggleLoop() {
  isLoop.value = !isLoop.value
}

function seekTo(pct: number) {
  playProgress.value = pct
  currentTime.value = (pct / 100) * totalDuration.value
}

async function saveParams() {
  if (!currentDialogue.value) return
  try {
    await editorApi.updateVoiceParams(currentDialogue.value.id, {
      emotion: voiceParams.emotion,
      speed: String(voiceParams.speed),
      pitch: String(voiceParams.pitch),
      volume: String(voiceParams.volume),
    })
    ElMessage.success('参数已保存')
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  }
}

async function regenerateVoice() {
  if (!currentDialogue.value) return
  regenerating.value = true
  try {
    await editorApi.regenerateVoice(currentDialogue.value.id)
    ElMessage.success('重新生成任务已提交')
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    regenerating.value = false
  }
}

function handleUpload(_file: File) {
  ElMessage.success('音频上传成功')
  return false
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

onUnmounted(() => {
  if (playTimer) clearInterval(playTimer)
})
</script>

<style scoped>
.voice-adjust { padding: 24px; }
.page-header { display: flex; align-items: center; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.wf-header { display: flex; justify-content: space-between; align-items: center; }
.current-line { font-size: 13px; color: var(--el-text-color-secondary); max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.waveform-display { height: 160px; background: #1a1a2e; border-radius: 8px; position: relative; overflow: hidden; padding: 16px; }
.waveform-bars { display: flex; align-items: flex-end; height: 100%; gap: 2px; }
.wf-bar { flex: 1; background: var(--el-color-primary); border-radius: 2px 2px 0 0; min-width: 3px; transition: height 0.1s; }
.playhead-indicator { position: absolute; top: 0; bottom: 0; width: 2px; background: var(--el-color-danger); transition: left 0.1s; }
.playback-bar { display: flex; align-items: center; gap: 12px; margin-top: 16px; }
.time-info { font-family: monospace; font-size: 13px; white-space: nowrap; }
.params-section { margin-top: 20px; }
.params-section h4 { margin: 0 0 12px; font-size: 15px; }
.param-control { display: flex; flex-direction: column; gap: 4px; }
.param-control label { font-size: 12px; color: var(--el-text-color-secondary); }
.action-bar { display: flex; gap: 8px; margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--el-border-color-lighter); }
.dialogue-list-card { height: calc(100vh - 140px); overflow-y: auto; }
.dialogue-items { display: flex; flex-direction: column; gap: 8px; }
.dialogue-item { padding: 12px; border: 1px solid var(--el-border-color-lighter); border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.dialogue-item:hover { background: var(--el-fill-color-light); }
.dialogue-item.active { border-color: var(--el-color-primary); background: var(--el-color-primary-light-9); }
.di-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.di-avatar { background: var(--el-color-primary); color: #fff; font-size: 12px; }
.di-name { font-weight: 600; font-size: 13px; }
.di-text { font-size: 14px; margin: 0 0 4px; line-height: 1.4; }
.di-meta { display: flex; gap: 12px; font-size: 11px; color: var(--el-text-color-secondary); }
.no-dialogues { text-align: center; color: var(--el-text-color-secondary); padding: 40px 0; }
</style>
