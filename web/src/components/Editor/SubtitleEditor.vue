<template>
  <div class="subtitle-editor">
    <div class="subtitle-list">
      <div
        v-for="(sub, index) in localSubtitles"
        :key="sub.id"
        class="subtitle-row"
        :class="{ active: activeIndex === index }"
        @click="activeIndex = index"
      >
        <span class="sub-index">{{ index + 1 }}</span>
        <el-input
          v-model="sub.text"
          size="small"
          @blur="emitUpdate(sub)"
        />
        <el-input-number
          v-model="sub.startTime"
          :min="0"
          :step="0.1"
          :precision="1"
          size="small"
          controls-position="right"
          style="width: 80px"
          @change="emitUpdate(sub)"
        />
        <el-input-number
          v-model="sub.endTime"
          :min="sub.startTime"
          :step="0.1"
          :precision="1"
          size="small"
          controls-position="right"
          style="width: 80px"
          @change="emitUpdate(sub)"
        />
        <el-button size="small" type="danger" plain @click="removeSub(index)">删</el-button>
      </div>
    </div>
    <el-button size="small" @click="addSub">添加字幕</el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface SubEntry {
  id: string
  text: string
  startTime: number
  endTime: number
}

const props = defineProps<{
  subtitles: SubEntry[]
}>()

const emit = defineEmits<{
  (e: 'update', sub: SubEntry): void
  (e: 'remove', id: string): void
  (e: 'add', sub: SubEntry): void
}>()

const localSubtitles = ref<SubEntry[]>([...props.subtitles])
const activeIndex = ref(0)

watch(() => props.subtitles, (v) => { localSubtitles.value = [...v] }, { deep: true })

function emitUpdate(sub: SubEntry) {
  emit('update', sub)
}

function removeSub(index: number) {
  const sub = localSubtitles.value[index]
  localSubtitles.value.splice(index, 1)
  emit('remove', sub.id)
}

function addSub() {
  const newSub: SubEntry = {
    id: `sub-${Date.now()}`,
    text: '',
    startTime: 0,
    endTime: 1,
  }
  localSubtitles.value.push(newSub)
  emit('add', newSub)
  activeIndex.value = localSubtitles.value.length - 1
}
</script>

<style lang="scss" scoped>
.subtitle-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.subtitle-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 400px;
  overflow-y: auto;
}

.subtitle-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  background: #f5f7fa;
  cursor: pointer;
  transition: background 0.15s;

  &.active {
    background: #ecf5ff;
    border: 1px solid #b3d8ff;
  }
}

.sub-index {
  min-width: 24px;
  font-size: 12px;
  color: #909399;
  text-align: center;
}
</style>
