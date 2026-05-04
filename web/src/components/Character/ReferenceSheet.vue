<template>
  <div class="reference-sheet">
    <h4 class="sheet-title">参考图</h4>
    <div class="image-grid">
      <div
        v-for="(url, view) in images"
        :key="view"
        class="image-cell"
      >
        <el-image
          v-if="url"
          :src="url"
          fit="cover"
          class="ref-image"
          :preview-src-list="[url]"
        />
        <div v-else class="ref-placeholder">
          <el-icon :size="24"><Plus /></el-icon>
        </div>
        <span class="view-label">{{ view }}</span>
      </div>
    </div>
    <el-button size="small" class="gen-btn" @click="$emit('generate')">
      生成参考图
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'

defineProps<{
  images: Record<string, string>
}>()

defineEmits<{
  (e: 'generate'): void
}>()
</script>

<style lang="scss" scoped>
.reference-sheet {
  padding: 12px;
}

.sheet-title {
  margin-bottom: 12px;
  font-size: 14px;
  color: #303133;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.image-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.ref-image {
  width: 100px;
  height: 130px;
  border-radius: 6px;
}

.ref-placeholder {
  width: 100px;
  height: 130px;
  background: #f5f7fa;
  border: 1px dashed #dcdfe6;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  cursor: pointer;

  &:hover {
    border-color: #409eff;
    color: #409eff;
  }
}

.view-label {
  font-size: 11px;
  color: #909399;
}

.gen-btn {
  width: 100%;
}
</style>
