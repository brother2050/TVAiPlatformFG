<template>
  <div class="video-trimmer">
    <div class="video-container">
      <video
        ref="videoRef"
        :src="videoUrl"
        class="trim-video"
        @loadedmetadata="onLoaded"
        @timeupdate="onTimeUpdate"
      />
    </div>
    <div class="trim-controls">
      <div class="trim-range">
        <span class="time-label">{{ formatTime(startTime) }}</span>
        <el-slider
          v-model="trimRange"
          range
          :min="0"
          :max="duration"
          :step="0.1"
          :format-tooltip="(v: number) => formatTime(v)"
          class="trim-slider"
          @change="onTrimChange"
        />
        <span class="time-label">{{ formatTime(endTime) }}</span>
      </div>
      <div class="playback-controls">
        <el-button size="small" @click="togglePlay">
          <el-icon><VideoPlay v-if="!playing" /><VideoPause v-else /></el-icon>
          {{ playing ? '暂停' : '播放' }}
        </el-button>
        <el-button size="small" type="primary" @click="handleTrim">应用裁剪</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { VideoPlay, VideoPause } from '@element-plus/icons-vue'

defineProps<{
  videoUrl: string
}>()

const emit = defineEmits<{
  (e: 'trim', range: { start: number; end: number }): void
}>()

const videoRef = ref<HTMLVideoElement | null>(null)
const duration = ref(0)
const currentTime = ref(0)
const trimRange = ref<[number, number]>([0, 0])
const playing = ref(false)

const startTime = computed(() => trimRange.value[0])
const endTime = computed(() => trimRange.value[1])

function onLoaded() {
  if (!videoRef.value) return
  duration.value = videoRef.value.duration
  trimRange.value = [0, videoRef.value.duration]
}

function onTimeUpdate() {
  if (!videoRef.value) return
  currentTime.value = videoRef.value.currentTime
}

function togglePlay() {
  if (!videoRef.value) return
  if (playing.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.currentTime = trimRange.value[0]
    videoRef.value.play()
  }
  playing.value = !playing.value
}

function onTrimChange(val: [number, number]) {
  if (videoRef.value) {
    videoRef.value.currentTime = val[0]
  }
}

function handleTrim() {
  emit('trim', { start: startTime.value, end: endTime.value })
}

function formatTime(sec: number) {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
.video-trimmer {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.video-container {
  display: flex;
  justify-content: center;
  background: #1a1a2e;
  border-radius: 8px;
  padding: 12px;
}

.trim-video {
  max-width: 100%;
  max-height: 300px;
  border-radius: 4px;
}

.trim-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.trim-range {
  display: flex;
  align-items: center;
  gap: 12px;
}

.trim-slider {
  flex: 1;
}

.time-label {
  font-size: 12px;
  color: #909399;
  min-width: 36px;
  font-variant-numeric: tabular-nums;
}

.playback-controls {
  display: flex;
  gap: 8px;
}
</style>
