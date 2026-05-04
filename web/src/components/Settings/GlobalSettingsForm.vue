<template>
  <el-form :model="form" label-width="100px" class="global-settings-form">
    <el-form-item label="画风">
      <el-input v-model="form.art_style" placeholder="如: 赛博朋克、水墨风" />
    </el-form-item>
    <el-form-item label="色调">
      <el-input v-model="form.color_palette" placeholder="如: 暖色调、冷色调" />
    </el-form-item>
    <el-form-item label="叙事节奏">
      <el-select v-model="form.narrative_pace" placeholder="选择节奏">
        <el-option label="快节奏" value="fast" />
        <el-option label="中等" value="medium" />
        <el-option label="慢节奏" value="slow" />
      </el-select>
    </el-form-item>
    <el-form-item label="目标受众">
      <el-input v-model="form.target_audience" placeholder="如: 青年、全年龄" />
    </el-form-item>
    <el-form-item label="整体氛围">
      <el-input v-model="form.overall_mood" placeholder="如: 轻松愉快、紧张悬疑" />
    </el-form-item>
    <el-form-item label="音乐风格">
      <el-input v-model="form.music_style" placeholder="如: 电子、古典" />
    </el-form-item>
    <el-form-item label="字幕样式">
      <el-input v-model="form.subtitle_style" placeholder="如: 白色描边、黄色底部" />
    </el-form-item>
    <el-form-item label="全局前缀">
      <el-input
        v-model="form.global_prompt_prefix"
        type="textarea"
        :rows="3"
        placeholder="添加到所有 AI 提示词前面的通用描述"
      />
    </el-form-item>

    <el-divider>自定义维度</el-divider>
    <div v-for="(val, key) in form.custom_dimensions" :key="key" class="dimension-row">
      <span class="dim-key">{{ key }}</span>
      <el-input :model-value="val" size="small" @update:model-value="(v: string) => updateDimension(key as string, v)" />
      <el-button size="small" type="danger" plain @click="removeDimension(key as string)">删除</el-button>
    </div>

    <el-form-item>
      <el-button type="primary" @click="handleSave">保存设定</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import type { ProjectGlobalSettings } from '@/api/index'

const props = defineProps<{
  settings: ProjectGlobalSettings
}>()

const emit = defineEmits<{
  (e: 'save', data: ProjectGlobalSettings): void
  (e: 'addDimension', key: string, value: string): void
  (e: 'removeDimension', key: string): void
}>()

const form = reactive<ProjectGlobalSettings>({
  art_style: '',
  color_palette: '',
  narrative_pace: 'medium',
  target_audience: '',
  overall_mood: '',
  music_style: '',
  subtitle_style: '',
  custom_dimensions: {},
  global_prompt_prefix: '',
})

watch(() => props.settings, (s) => {
  if (!s) return
  Object.assign(form, s)
}, { immediate: true })

function updateDimension(key: string, value: string) {
  form.custom_dimensions[key] = value
}

function removeDimension(key: string) {
  delete form.custom_dimensions[key]
  emit('removeDimension', key)
}

function handleSave() {
  emit('save', { ...form, custom_dimensions: { ...form.custom_dimensions } })
}
</script>

<style lang="scss" scoped>
.global-settings-form {
  max-width: 600px;
}

.dimension-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.dim-key {
  min-width: 100px;
  font-size: 13px;
  color: #606266;
}
</style>
