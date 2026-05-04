<template>
  <div class="bgm-mixer">
    <div class="mixer-header">
      <h4>BGM 混音</h4>
    </div>
    <div class="tracks-list">
      <div v-for="track in tracks" :key="track.id" class="mixer-track">
        <span class="track-name">{{ track.name }}</span>
        <el-slider
          :model-value="track.volume"
          :min="0"
          :max="100"
          size="small"
          class="volume-slider"
          @update:model-value="(v: number) => updateVolume(track.id, v)"
        />
        <span class="volume-label">{{ track.volume }}%</span>
        <el-button size="small" :type="track.muted ? 'danger' : ''" @click="toggleMute(track.id)">
          {{ track.muted ? '已静音' : '静音' }}
        </el-button>
      </div>
    </div>
    <el-button size="small" class="add-btn" @click="handleAdd">添加音轨</el-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface MixerTrack {
  id: string
  name: string
  volume: number
  muted: boolean
}

const tracks = ref<MixerTrack[]>([
  { id: 'bgm', name: '背景音乐', volume: 60, muted: false },
  { id: 'ambient', name: '环境音', volume: 40, muted: false },
])

function updateVolume(id: string, volume: number) {
  const t = tracks.value.find((t) => t.id === id)
  if (t) t.volume = volume
}

function toggleMute(id: string) {
  const t = tracks.value.find((t) => t.id === id)
  if (t) t.muted = !t.muted
}

function handleAdd() {
  tracks.value.push({
    id: `track-${Date.now()}`,
    name: `音轨 ${tracks.value.length + 1}`,
    volume: 50,
    muted: false,
  })
}
</script>

<style lang="scss" scoped>
.bgm-mixer {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mixer-header h4 {
  font-size: 14px;
  color: #303133;
}

.tracks-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mixer-track {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.track-name {
  min-width: 80px;
  font-size: 13px;
  color: #606266;
}

.volume-slider {
  flex: 1;
}

.volume-label {
  min-width: 40px;
  font-size: 12px;
  color: #909399;
  text-align: right;
}

.add-btn {
  align-self: flex-start;
}
</style>
