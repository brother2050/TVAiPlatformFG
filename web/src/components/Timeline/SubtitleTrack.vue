<template>
  <div class="subtitle-track">
    <div
      v-for="sub in subtitles"
      :key="sub.id"
      class="subtitle-block"
      :style="blockStyle(sub)"
    >
      <span class="subtitle-text">{{ sub.text }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
interface SubtitleItem {
  id: string
  text: string
  startTime: number
  duration: number
}

const props = defineProps<{
  subtitles: SubtitleItem[]
  pixelsPerSecond?: number
}>()

const pps = props.pixelsPerSecond ?? 10

function blockStyle(sub: SubtitleItem) {
  return {
    left: `${sub.startTime * pps}px`,
    width: `${sub.duration * pps}px`,
  }
}
</script>

<style lang="scss" scoped>
.subtitle-track {
  position: relative;
  height: 36px;
  background: #0f3460;
  border-radius: 4px;
  overflow: hidden;
}

.subtitle-block {
  position: absolute;
  top: 4px;
  height: 28px;
  background: rgba(230, 162, 60, 0.3);
  border: 1px solid rgba(230, 162, 60, 0.6);
  border-radius: 4px;
  display: flex;
  align-items: center;
  padding: 0 6px;
  overflow: hidden;
}

.subtitle-text {
  color: #fff;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
