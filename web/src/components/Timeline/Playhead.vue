<template>
  <div class="playhead" :style="{ left: `${position}px` }">
    <div class="playhead-head" />
    <div class="playhead-line" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  time: number
  pixelsPerSecond?: number
}>()

const position = computed(() => props.time * (props.pixelsPerSecond ?? 10))
</script>

<style lang="scss" scoped>
.playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  z-index: 10;
  pointer-events: none;
}

.playhead-head {
  width: 12px;
  height: 12px;
  background: #f56c6c;
  border-radius: 50%;
  position: absolute;
  top: -2px;
  left: -5px;
}

.playhead-line {
  width: 2px;
  height: 100%;
  background: #f56c6c;
  position: absolute;
  top: 10px;
}
</style>
