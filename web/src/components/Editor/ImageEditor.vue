<template>
  <div class="image-editor">
    <div class="canvas-container">
      <canvas ref="canvasRef" class="edit-canvas" />
    </div>
    <div class="editor-toolbar">
      <el-button-group>
        <el-button size="small" :type="mode === 'draw' ? 'primary' : ''" @click="mode = 'draw'">画笔</el-button>
        <el-button size="small" :type="mode === 'erase' ? 'primary' : ''" @click="mode = 'erase'">橡皮</el-button>
      </el-button-group>
      <el-slider v-model="brushSize" :min="2" :max="50" style="width: 120px" />
      <el-button size="small" @click="clearMask">清除</el-button>
      <el-button size="small" type="primary" @click="handleInpaint">局部重绘</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

const props = defineProps<{
  imageUrl?: string
}>()

const emit = defineEmits<{
  (e: 'inpaint', maskData: string): void
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const mode = ref<'draw' | 'erase'>('draw')
const brushSize = ref(10)
let drawing = false

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return
  canvas.width = 512
  canvas.height = 512

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  if (props.imageUrl) {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
    }
    img.src = props.imageUrl
  }

  canvas.addEventListener('mousedown', (e) => {
    drawing = true
    draw(e)
  })
  canvas.addEventListener('mousemove', (e) => { if (drawing) draw(e) })
  canvas.addEventListener('mouseup', () => { drawing = false })
  canvas.addEventListener('mouseleave', () => { drawing = false })
})

watch(() => props.imageUrl, (url) => {
  const canvas = canvasRef.value
  if (!canvas || !url) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
  img.src = url
})

function draw(e: MouseEvent) {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  const rect = canvas.getBoundingClientRect()
  const x = (e.clientX - rect.left) * (canvas.width / rect.width)
  const y = (e.clientY - rect.top) * (canvas.height / rect.height)

  ctx.beginPath()
  ctx.arc(x, y, brushSize.value, 0, Math.PI * 2)
  ctx.fillStyle = mode.value === 'draw' ? 'rgba(255,0,0,0.5)' : 'rgba(0,0,0,1)'
  ctx.fill()
}

function clearMask() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx || !props.imageUrl) {
    ctx?.clearRect(0, 0, canvas.width, canvas.height)
    return
  }
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
  img.src = props.imageUrl
}

function handleInpaint() {
  const canvas = canvasRef.value
  if (!canvas) return
  emit('inpaint', canvas.toDataURL('image/png'))
}
</script>

<style lang="scss" scoped>
.image-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.canvas-container {
  display: flex;
  justify-content: center;
  background: #1a1a2e;
  border-radius: 8px;
  padding: 12px;
}

.edit-canvas {
  max-width: 100%;
  border-radius: 4px;
  cursor: crosshair;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
</style>
