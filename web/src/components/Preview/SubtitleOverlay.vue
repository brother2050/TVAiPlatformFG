<template>
  <div class="subtitle-overlay" :class="styleType">
    <span class="subtitle-text">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  text: string
  styleType?: string
}>()
</script>

<style lang="scss" scoped>
.subtitle-overlay {
  position: absolute;
  bottom: 48px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  padding: 0 16px;
  pointer-events: none;
}

.subtitle-text {
  display: inline-block;
  padding: 4px 12px;
  font-size: 16px;
  color: #fff;
  text-align: center;
  max-width: 80%;
  line-height: 1.5;
}

// 默认样式：白色描边
.default .subtitle-text,
.subtitle-overlay:not(.yellow-bottom):not(.minimal) .subtitle-text {
  text-shadow:
    0 0 4px rgba(0, 0, 0, 0.8),
    1px 1px 2px rgba(0, 0, 0, 0.6);
}

// 黄字底部
.yellow-bottom .subtitle-text {
  color: #ffd700;
  text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
}

// 极简白字
.minimal .subtitle-text {
  color: #fff;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 4px;
}
</style>
