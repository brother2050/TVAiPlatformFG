<template>
  <div class="audio-waveform">
    <div ref="containerRef" class="waveform-container" />
    <div class="waveform-controls">
      <el-button size="small" @click="togglePlay">
        <el-icon>
          <VideoPlay v-if="!playing" />
          <VideoPause v-else />
        </el-icon>
        {{ playing ? '暂停' : '播放' }}
      </el-button>
      <span class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { VideoPlay, VideoPause } from '@element-plus/icons-vue'

const props = defineProps<{
  audioUrl: string
}>()

const emit = defineEmits<{
  (e: 'ready', duration: number): void
  (e: 'timeupdate', time: number): void
}>()

const containerRef = ref<HTMLDivElement | null>(null)
const playing = ref(false)
const currentTime = ref(0)
const duration = ref(0)
let ws: any = null

onMounted(async () => {
  if (!containerRef.value) return
  try {
    const WaveSurfer = (await import('wavesurfer.js')).default
    ws = WaveSurfer.create({
      container: containerRef.value,
      waveColor: '#409eff',
      progressColor: '#1d6fd1',
      height: 64,
      responsive: true,
    })
    ws.load(props.audioUrl)
    ws.on('ready', () => {
      duration.value = ws.getDuration()
      emit('ready', duration.value)
    })
    ws.on('audioprocess', () => {
      currentTime.value = ws.getCurrentTime()
      emit('timeupdate', currentTime.value)
    })
    ws.on('finish', () => { playing.value = false })
  } catch {
    // wavesurfer not available — render placeholder
  }
})

watch(() => props.audioUrl, (url) => {
  if (ws && url) ws.load(url)
})

function togglePlay() {
  if (!ws) return
  ws.playPause()
  playing.value = !playing.value
}

function formatTime(sec: number) {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

onBeforeUnmount(() => {
  ws?.destroy()
})
</script>

<style lang="scss" scoped>
.audio-waveform {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.waveform-container {
  background: #1a1a2e;
  border-radius: 8px;
  padding: 12px;
  min-height: 88px;
}

.waveform-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-display {
  font-size: 13px;
  color: #606266;
  font-variant-numeric: tabular-nums;
}
</style>
