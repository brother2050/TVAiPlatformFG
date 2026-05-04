<template>
  <el-card class="profile-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="char-name">{{ character.name }}</span>
        <el-tag size="small" :type="genderTagType">{{ genderLabel }}</el-tag>
      </div>
    </template>

    <div class="profile-body">
      <div class="avatar-area">
        <el-avatar :size="64" :src="avatarSrc">
          {{ character.name?.charAt(0) }}
        </el-avatar>
      </div>

      <div class="info-list">
        <div class="info-row">
          <span class="label">脸型</span>
          <span>{{ character.appearance?.face_shape }}</span>
        </div>
        <div class="info-row">
          <span class="label">瞳色</span>
          <span>{{ character.appearance?.eye_color }}</span>
        </div>
        <div class="info-row">
          <span class="label">发型</span>
          <span>{{ character.appearance?.hair_style }}</span>
        </div>
        <div class="info-row">
          <span class="label">身高</span>
          <span>{{ character.body?.height_cm }}cm</span>
        </div>
      </div>
    </div>

    <div class="card-footer">
      <el-button size="small" @click="$emit('edit', character)">编辑</el-button>
      <el-button size="small" type="danger" plain @click="$emit('delete', character.id)">删除</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Character } from '@/api/index'

const props = defineProps<{ character: Character }>()

defineEmits<{
  (e: 'edit', character: Character): void
  (e: 'delete', id: string): void
}>()

const avatarSrc = computed(() => {
  const imgs = props.character.reference_images
  return imgs?.front || ''
})

const genderLabel = computed(() => {
  const map = { male: '男', female: '女', other: '其他' }
  return map[props.character.gender] || props.character.gender
})

const genderTagType = computed(() => {
  const map = { male: '', female: 'danger', other: 'warning' } as const
  return map[props.character.gender] || 'info'
})
</script>

<style lang="scss" scoped>
.profile-card {
  width: 280px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.char-name {
  font-weight: 600;
  font-size: 16px;
}

.profile-body {
  display: flex;
  gap: 16px;
}

.avatar-area {
  flex-shrink: 0;
}

.info-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-row {
  display: flex;
  gap: 8px;
  font-size: 13px;

  .label {
    color: #909399;
    min-width: 36px;
  }
}

.card-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
