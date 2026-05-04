<template>
  <el-card class="wardrobe-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span>{{ wardrobeName || '默认服装' }}</span>
        <el-tag size="small" type="info">服装</el-tag>
      </div>
    </template>
    <div class="wardrobe-body">
      <div class="wardrobe-row">
        <span class="label">上装</span>
        <span>{{ wardrobe.top }}</span>
      </div>
      <div class="wardrobe-row">
        <span class="label">下装</span>
        <span>{{ wardrobe.bottom }}</span>
      </div>
      <div class="wardrobe-row">
        <span class="label">鞋</span>
        <span>{{ wardrobe.shoes }}</span>
      </div>
      <div class="wardrobe-row">
        <span class="label">配色</span>
        <div class="palette">
          <span
            v-for="(c, i) in wardrobe.color_palette"
            :key="i"
            class="color-dot"
            :style="{ backgroundColor: c }"
          />
        </div>
      </div>
    </div>
    <div class="wardrobe-actions">
      <el-button size="small" @click="$emit('edit')">编辑</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { WardrobeSpec } from '@/api/index'

defineProps<{
  wardrobe: WardrobeSpec
  wardrobeName?: string
}>()

defineEmits<{
  (e: 'edit'): void
}>()
</script>

<style lang="scss" scoped>
.wardrobe-card {
  width: 240px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.wardrobe-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.wardrobe-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;

  .label {
    color: #909399;
    min-width: 36px;
  }
}

.palette {
  display: flex;
  gap: 4px;
}

.color-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1px solid #dcdfe6;
}

.wardrobe-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
