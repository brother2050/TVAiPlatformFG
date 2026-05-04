<template>
  <div class="audio-track">
    <div
      v-for="block in blocks"
      :key="block.id"
      class="audio-block"
      :style="blockStyle(block)"
    >
      <canvas
        ref="waveformCanvases"
        class="waveform-canvas"
        :width="block.duration * pps"
        height="40"
      />
      <span class="block-label">{{ block.label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

interface AudioBlock {
  id: string
  label: string
  startTime: number
  duration: number
  waveformData?: number[]
  color?: string
}

const props = defineProps<{
  blocks: AudioBlock[]
  pixelsPerSecond?: number
}>()

const pps = props.pixelsPerSecond ?? 10
const waveformCanvases = ref<HTMLCanvasElement[]>([])

function blockStyle(block: AudioBlock) {
  return {
    left: `${block.startTime * pps}px`,
    width: `${block.duration * pps}px`,
  }
}

onMounted(() => {
  waveformCanvases.value.forEach((canvas, i) => {
    const ctx = canvas.getContext('2d')
    if (!ctx || !props.blocks[i]) return
    const data = props.blocks[i].waveformData || generateDummyWaveform(props.blocks[i].duration * pps)
    drawWaveform(ctx, data, canvas.width, canvas.height, props.blocks[i].color || '#67c23a')
  })
})

function generateDummyWaveform(length: number): number[] {
  return Array.from({ length: Math.floor(length / 2) }, () => Math.random())
}

function drawWaveform(ctx: CanvasRenderingContext2D, data: number[], w: number, h: number, color: string) {
  ctx.fillStyle = color
  const barWidth = 2
  const gap = 1
  const mid = h / 2
  for (let i = 0; i < Math.min(data.length, Math.floor(w / (barWidth + gap))); i++) {
    const amp = data[i] * mid * 0.8
    ctx.fillRect(i * (barWidth + gap), mid - amp, barWidth, amp * 2)
  }
}
</script>

<style lang="scss" scoped>
.audio-track {
  position: relative;
  height: 48px;
  background: #16213e;
  border-radius: 4px;
  overflow: hidden;
}

.audio-block {
  position: absolute;
  top: 4px;
  height: 40px;
  border-radius: 4px;
  overflow: hidden;
  background: rgba(103, 194, 58, 0.15);
}

.waveform-canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.block-label {
  position: absolute;
  bottom: 2px;
  left: 6px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 10px;
}
</style>
