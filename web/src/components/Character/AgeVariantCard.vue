<template>
  <el-card class="age-variant-card" shadow="hover">
    <template #header>
      <span>{{ ageLabel }}</span>
    </template>
    <div class="variant-body">
      <el-image
        v-if="imageUrl"
        :src="imageUrl"
        fit="cover"
        class="variant-image"
      />
      <div v-else class="variant-placeholder">
        <el-icon :size="32"><User /></el-icon>
      </div>
    </div>
    <div class="variant-info">
      <p>{{ description }}</p>
    </div>
    <div class="variant-actions">
      <el-button size="small" @click="$emit('regenerate')">重新生成</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { User } from '@element-plus/icons-vue'

defineProps<{
  ageLabel: string
  imageUrl?: string
  description?: string
}>()

defineEmits<{
  (e: 'regenerate'): void
}>()
</script>

<style lang="scss" scoped>
.age-variant-card {
  width: 200px;
}

.variant-body {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}

.variant-image {
  width: 120px;
  height: 160px;
  border-radius: 8px;
}

.variant-placeholder {
  width: 120px;
  height: 160px;
  background: #f0f2f5;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}

.variant-info {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.variant-actions {
  display: flex;
  justify-content: center;
}
</style>
