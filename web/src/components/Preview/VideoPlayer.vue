<template>
  <div class="video-player">
    <video
      ref="videoRef"
      :src="src"
      class="player-video"
      @loadedmetadata="onLoaded"
      @timeupdate="onTimeUpdate"
      @ended="onEnded"
    />
    <SubtitleOverlay
      v-if="currentSubtitle"
      :text="currentSubtitle.text"
      :style-type="subtitleStyle"
    />
    <div class="player-controls">
      <el-button size="small" circle @click="togglePlay">
        <el-icon>
          <VideoPlay v-if="!playing" />
          <VideoPause v-else />
        </el-icon>
      </el-button>
      <div class="progress-bar" @click="seek($event)">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }" />
      </div>
      <span class="time-text">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
      <el-slider
        v-model="volume"
        :min="0"
        :max="100"
        size="small"
        style="width: 80px"
        @input="onVolumeChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { VideoPlay, VideoPause } from '@element-plus/icons-vue'
import SubtitleOverlay from './SubtitleOverlay.vue'

interface SubtitleEntry {
  text: string
  startTime: number
  endTime: number
}

const props = defineProps<{
  src: string
  subtitles?: SubtitleEntry[]
  subtitleStyle?: string
}>()

const videoRef = ref<HTMLVideoElement | null>(null)
const playing = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(80)

const progressPercent = computed(() => duration.value ? (currentTime.value / duration.value) * 100 : 0)

const currentSubtitle = computed(() => {
  if (!props.subtitles) return null
  return props.subtitles.find(
    (s) => currentTime.value >= s.startTime && currentTime.value <= s.endTime
  ) || null
})

function onLoaded() {
  if (!videoRef.value) return
  duration.value = videoRef.value.duration
}

function onTimeUpdate() {
  if (!videoRef.value) return
  currentTime.value = videoRef.value.currentTime
}

function onEnded() {
  playing.value = false
}

function togglePlay() {
  if (!videoRef.value) return
  if (playing.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play()
  }
  playing.value = !playing.value
}

function seek(e: MouseEvent) {
  if (!videoRef.value) return
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const ratio = (e.clientX - rect.left) / rect.width
  videoRef.value.currentTime = ratio * duration.value
}

function onVolumeChange(val: number) {
  if (videoRef.value) videoRef.value.volume = val / 100
}

function formatTime(sec: number) {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
.video-player {
  position: relative;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.player-video {
  width: 100%;
  display: block;
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.7);
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: #333;
  border-radius: 2px;
  cursor: pointer;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #409eff;
  transition: width 0.1s;
}

.time-text {
  font-size: 12px;
  color: #ccc;
  min-width: 80px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}
</style>
