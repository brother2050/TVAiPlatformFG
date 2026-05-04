<template>
  <div class="video-track">
    <div
      v-for="clip in clips"
      :key="clip.id"
      class="video-clip"
      :style="clipStyle(clip)"
      @mousedown="startDrag($event, clip)"
    >
      <span class="clip-label">{{ clip.label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
interface VideoClip {
  id: string
  label: string
  startTime: number
  duration: number
  color?: string
}

const props = defineProps<{
  clips: VideoClip[]
  pixelsPerSecond?: number
}>()

const emit = defineEmits<{
  (e: 'update', clip: VideoClip): void
}>()

const pps = props.pixelsPerSecond ?? 10

function clipStyle(clip: VideoClip) {
  return {
    left: `${clip.startTime * pps}px`,
    width: `${clip.duration * pps}px`,
    backgroundColor: clip.color || '#409eff',
  }
}

function startDrag(event: MouseEvent, clip: VideoClip) {
  const startX = event.clientX
  const origStart = clip.startTime

  function onMove(e: MouseEvent) {
    const delta = (e.clientX - startX) / pps
    clip.startTime = Math.max(0, origStart + delta)
    emit('update', clip)
  }

  function onUp() {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }

  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}
</script>

<style lang="scss" scoped>
.video-track {
  position: relative;
  height: 48px;
  background: #1a1a2e;
  border-radius: 4px;
  overflow: hidden;
}

.video-clip {
  position: absolute;
  top: 4px;
  height: 40px;
  border-radius: 4px;
  cursor: grab;
  display: flex;
  align-items: center;
  padding: 0 8px;
  user-select: none;

  &:active {
    cursor: grabbing;
    opacity: 0.85;
  }
}

.clip-label {
  color: #fff;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
