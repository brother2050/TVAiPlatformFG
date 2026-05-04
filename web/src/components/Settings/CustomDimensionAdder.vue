<template>
  <div class="custom-dimension-adder">
    <div class="add-form">
      <el-input v-model="newKey" size="small" placeholder="维度名称" style="width: 140px" />
      <el-input v-model="newValue" size="small" placeholder="维度值" style="width: 200px" />
      <el-button size="small" type="primary" :disabled="!newKey || !newValue" @click="handleAdd">
        添加
      </el-button>
    </div>
    <div class="existing-dimensions">
      <el-tag
        v-for="(val, key) in dimensions"
        :key="key"
        closable
        class="dim-tag"
        @close="handleRemove(key as string)"
      >
        {{ key }}: {{ val }}
      </el-tag>
      <span v-if="!Object.keys(dimensions).length" class="empty-hint">暂无自定义维度</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  dimensions: Record<string, string>
}>()

const emit = defineEmits<{
  (e: 'add', key: string, value: string): void
  (e: 'remove', key: string): void
}>()

const newKey = ref('')
const newValue = ref('')

function handleAdd() {
  emit('add', newKey.value, newValue.value)
  newKey.value = ''
  newValue.value = ''
}

function handleRemove(key: string) {
  emit('remove', key)
}
</script>

<style lang="scss" scoped>
.custom-dimension-adder {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.add-form {
  display: flex;
  gap: 8px;
  align-items: center;
}

.existing-dimensions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dim-tag {
  max-width: 200px;
}

.empty-hint {
  font-size: 13px;
  color: #c0c4cc;
}
</style>
