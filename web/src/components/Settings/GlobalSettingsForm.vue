<template>
  <el-form :model="form" label-width="100px" class="global-settings-form">
    <el-form-item label="题材">
      <el-select v-model="form.genre" filterable allow-create placeholder="选择或自定义题材">
        <el-option label="都市" value="urban" />
        <el-option label="古装" value="historical" />
        <el-option label="科幻" value="scifi" />
        <el-option label="玄幻" value="fantasy" />
        <el-option label="悬疑" value="mystery" />
        <el-option label="喜剧" value="comedy" />
        <el-option label="爱情" value="romance" />
        <el-option label="动作" value="action" />
        <el-option label="冒险" value="adventure" />
        <el-option label="奇幻" value="magical" />
        <el-option label="校园" value="school" />
        <el-option label="战争" value="war" />
        <el-option label="恐怖" value="horror" />
        <el-option label="运动" value="sports" />
      </el-select>
    </el-form-item>
    <el-form-item label="画风">
      <el-select v-model="form.art_style" filterable allow-create placeholder="选择或自定义画风">
        <el-option label="日系动漫" value="anime" />
        <el-option label="写实" value="realistic" />
        <el-option label="水彩" value="watercolor" />
        <el-option label="油画" value="oil_painting" />
        <el-option label="赛博朋克" value="cyberpunk" />
        <el-option label="像素" value="pixel" />
        <el-option label="国风" value="chinese_style" />
        <el-option label="欧美卡通" value="cartoon_us" />
        <el-option label="二次元" value="2d_anime" />
        <el-option label="3D渲染" value="3d_render" />
        <el-option label="扁平" value="flat" />
        <el-option label="厚涂" value="thick_paint" />
        <el-option label="素描" value="sketch" />
        <el-option label="水墨" value="ink_wash" />
      </el-select>
    </el-form-item>
    <el-form-item label="色调">
      <el-select v-model="form.color_palette" filterable allow-create placeholder="选择或自定义色调">
        <el-option label="暖色调" value="warm" />
        <el-option label="冷色调" value="cool" />
        <el-option label="高饱和" value="saturated" />
        <el-option label="低饱和" value="desaturated" />
        <el-option label="黑白" value="monochrome" />
        <el-option label="复古" value="vintage" />
        <el-option label="霓虹" value="neon" />
      </el-select>
    </el-form-item>
    <el-form-item label="叙事节奏">
      <el-select v-model="form.narrative_pace" filterable allow-create placeholder="选择或自定义节奏">
        <el-option label="快节奏" value="fast" />
        <el-option label="中等" value="medium" />
        <el-option label="慢节奏" value="slow" />
        <el-option label="悬疑推进" value="suspenseful" />
        <el-option label="轻松日常" value="relaxed" />
      </el-select>
    </el-form-item>
    <el-form-item label="目标受众">
      <el-select v-model="form.target_audience" filterable allow-create placeholder="选择或自定义受众">
        <el-option label="青少年" value="teen" />
        <el-option label="年轻人" value="young_adult" />
        <el-option label="全年龄" value="all_ages" />
        <el-option label="成人" value="mature" />
      </el-select>
    </el-form-item>
    <el-form-item label="整体氛围">
      <el-select v-model="form.overall_mood" filterable allow-create placeholder="选择或自定义氛围">
        <el-option label="温馨" value="warm" />
        <el-option label="紧张" value="tense" />
        <el-option label="悲伤" value="melancholic" />
        <el-option label="欢快" value="cheerful" />
        <el-option label="神秘" value="mysterious" />
        <el-option label="史诗" value="epic" />
      </el-select>
    </el-form-item>
    <el-form-item label="音乐风格">
      <el-select v-model="form.music_style" filterable allow-create placeholder="选择或自定义音乐风格">
        <el-option label="管弦乐" value="orchestral" />
        <el-option label="电子" value="electronic" />
        <el-option label="钢琴" value="piano" />
        <el-option label="摇滚" value="rock" />
        <el-option label="民谣" value="folk" />
        <el-option label="爵士" value="jazz" />
      </el-select>
    </el-form-item>
    <el-form-item label="字幕样式">
      <el-select v-model="form.subtitle_style" filterable allow-create placeholder="选择或自定义字幕样式">
        <el-option label="简洁白字" value="clean_white" />
        <el-option label="带描边" value="stroked" />
        <el-option label="底栏字幕" value="bottom_bar" />
        <el-option label="创意排版" value="creative" />
      </el-select>
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
  genre: '',
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
