<template>
  <div class="global-settings">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>全局设定</h1>
      </div>
      <el-button type="primary" @click="saveSettings" :loading="saving">
        <el-icon><Check /></el-icon> 保存设定
      </el-button>
    </header>

    <!-- 第一层：项目全局设定 -->
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>第一层：项目全局设定</span>
          <el-tag size="small">影响全剧</el-tag>
        </div>
      </template>
      <el-form label-width="100px" class="settings-form">
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="题材">
              <el-select v-model="settings.genre" filterable allow-create placeholder="选择或自定义题材">
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
          </el-col>
          <el-col :span="12">
            <el-form-item label="画风">
              <el-select v-model="settings.art_style" filterable allow-create placeholder="选择或自定义画风">
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
          </el-col>
          <el-col :span="12">
            <el-form-item label="色调">
              <el-select v-model="settings.color_palette" filterable allow-create placeholder="选择或自定义色调">
                <el-option label="暖色调" value="warm" />
                <el-option label="冷色调" value="cool" />
                <el-option label="高饱和" value="saturated" />
                <el-option label="低饱和" value="desaturated" />
                <el-option label="黑白" value="monochrome" />
                <el-option label="复古" value="vintage" />
                <el-option label="霓虹" value="neon" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="叙事节奏">
              <el-select v-model="settings.narrative_pace" filterable allow-create>
                <el-option label="快节奏" value="fast" />
                <el-option label="中等" value="medium" />
                <el-option label="慢节奏" value="slow" />
                <el-option label="悬疑推进" value="suspenseful" />
                <el-option label="轻松日常" value="relaxed" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标受众">
              <el-select v-model="settings.target_audience" filterable allow-create>
                <el-option label="青少年" value="teen" />
                <el-option label="年轻人" value="young_adult" />
                <el-option label="全年龄" value="all_ages" />
                <el-option label="成人" value="mature" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="整体氛围">
              <el-select v-model="settings.overall_mood" filterable allow-create>
                <el-option label="温馨" value="warm" />
                <el-option label="紧张" value="tense" />
                <el-option label="悲伤" value="melancholic" />
                <el-option label="欢快" value="cheerful" />
                <el-option label="神秘" value="mysterious" />
                <el-option label="史诗" value="epic" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="音乐风格">
              <el-select v-model="settings.music_style" filterable allow-create>
                <el-option label="管弦乐" value="orchestral" />
                <el-option label="电子" value="electronic" />
                <el-option label="钢琴" value="piano" />
                <el-option label="摇滚" value="rock" />
                <el-option label="民谣" value="folk" />
                <el-option label="爵士" value="jazz" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="字幕风格">
              <el-select v-model="settings.subtitle_style" filterable allow-create>
                <el-option label="简洁白字" value="clean_white" />
                <el-option label="带描边" value="stroked" />
                <el-option label="底栏字幕" value="bottom_bar" />
                <el-option label="创意排版" value="creative" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="全局提示词前缀">
              <el-input
                v-model="settings.global_prompt_prefix"
                type="textarea"
                :rows="3"
                placeholder="追加到所有 AI 生成任务的 prompt 前缀…"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 自定义维度 -->
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>自定义维度</span>
          <el-button size="small" @click="addDimension"><el-icon><Plus /></el-icon> 添加维度</el-button>
        </div>
      </template>
      <div v-if="customDimensions.length === 0" class="no-dimensions">
        <el-text type="info">暂无自定义维度，点击上方按钮添加</el-text>
      </div>
      <div v-else class="dimension-list">
        <div v-for="(dim, idx) in customDimensions" :key="idx" class="dimension-item">
          <el-input v-model="dim.key" placeholder="维度名称" style="width: 200px" />
          <el-select v-model="dim.value" filterable allow-create placeholder="选择或自定义值" style="flex: 1">
            <el-option v-for="opt in dim.options" :key="opt" :label="opt" :value="opt" />
          </el-select>
          <el-button text type="danger" @click="removeDimension(idx)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 第二层：场景级覆盖 -->
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>第二层：场景级覆盖</span>
          <el-tag size="small" type="warning">可选</el-tag>
        </div>
      </template>
      <el-empty v-if="scenes.length === 0" description="暂无场景数据" :image-size="60" />
      <div v-else class="scene-overrides">
        <div v-for="scene in scenes" :key="scene.id" class="scene-override-item">
          <div class="scene-header" @click="toggleSceneExpand(scene.id)">
            <el-icon><Film /></el-icon>
            <span>场景{{ scene.scene_number }} - {{ scene.location }}</span>
            <el-icon class="expand-icon" :class="{ expanded: expandedScenes.includes(scene.id) }"><ArrowDown /></el-icon>
            <el-tag v-if="sceneOverrides[scene.id]" size="small" type="success">已覆盖</el-tag>
          </div>
          <div v-if="expandedScenes.includes(scene.id)" class="scene-form">
            <el-form label-width="80px" size="small">
              <el-form-item label="色调覆盖">
                <el-input v-model="sceneOverrides[scene.id].color_palette" placeholder="留空使用全局设定" />
              </el-form-item>
              <el-form-item label="氛围覆盖">
                <el-input v-model="sceneOverrides[scene.id].mood" placeholder="留空使用全局设定" />
              </el-form-item>
              <el-form-item label="额外提示词">
                <el-input v-model="sceneOverrides[scene.id].extra_prompt" type="textarea" :rows="2" placeholder="仅影响此场景的额外提示词" />
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 第三层：JSON模板 -->
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>第三层：JSON 模板</span>
          <el-button size="small" @click="goToTemplateWorkshop">
            <el-icon><Setting /></el-icon> 打开模板工坊
          </el-button>
        </div>
      </template>
      <el-text type="info">
        JSON 模板用于深度自定义 AI 生成行为。前往「调模板」页面进行编辑。
      </el-text>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Check, Plus, Delete, Film, ArrowDown, Setting } from '@element-plus/icons-vue'
import { useSettingsStore } from '@/stores/settings'
import { useTimelineStore } from '@/stores/timeline'
import { projectApi } from '@/api/project'
import type { ProjectGlobalSettings, Scene, SceneOverride } from '@/api'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
const settingsStore = useSettingsStore()
const timelineStore = useTimelineStore()
let episodeId = ''

const saving = ref(false)
const expandedScenes = ref<string[]>([])

const settings = reactive<ProjectGlobalSettings>({
  genre: '',
  art_style: '',
  color_palette: '',
  narrative_pace: '',
  target_audience: '',
  overall_mood: '',
  music_style: '',
  subtitle_style: '',
  custom_dimensions: {},
  global_prompt_prefix: '',
})

interface CustomDimension {
  key: string
  value: string
  options: string[]
}

const customDimensions = ref<CustomDimension[]>([])
const scenes = ref<Scene[]>([])
const sceneOverrides = ref<Record<string, SceneOverride>>({})

function addDimension() {
  customDimensions.value.push({
    key: '',
    value: '',
    options: [],
  })
}

function removeDimension(idx: number) {
  customDimensions.value.splice(idx, 1)
}

function toggleSceneExpand(sceneId: string) {
  const idx = expandedScenes.value.indexOf(sceneId)
  if (idx >= 0) expandedScenes.value.splice(idx, 1)
  else {
    expandedScenes.value.push(sceneId)
    if (!sceneOverrides.value[sceneId]) {
      sceneOverrides.value[sceneId] = {
        scene_id: sceneId,
        color_palette: '',
        mood: '',
        extra_prompt: '',
        custom_overrides: {},
      }
    }
  }
}

function goToTemplateWorkshop() {
  router.push({ name: 'Templates' })
}

async function saveSettings() {
  saving.value = true
  try {
    // 合并自定义维度到 settings
    const dims: Record<string, string> = {}
    for (const d of customDimensions.value) {
      if (d.key.trim()) dims[d.key.trim()] = d.value
    }
    settings.custom_dimensions = dims

    await settingsStore.updateSettings(projectId, settings)
    ElMessage.success('全局设定已保存')
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  const fetched = await settingsStore.fetchSettings(projectId)
  if (fetched) {
    Object.assign(settings, fetched)
    // 解析自定义维度
    if (fetched.custom_dimensions) {
      customDimensions.value = Object.entries(fetched.custom_dimensions).map(([key, value]) => ({
        key,
        value: String(value),
        options: [],
      }))
    }
  }
  const res = await projectApi.getEpisodes(projectId)
  const episodes = res.data.data
  if (episodes && episodes.length > 0) {
    episodeId = episodes[0].id
    await timelineStore.fetchScenes(episodeId)
  }
  scenes.value = timelineStore.scenes
})
</script>

<style scoped>
.global-settings { padding: 24px; max-width: 1200px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.settings-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.settings-form { margin-top: 8px; }
.no-dimensions { padding: 16px 0; }
.dimension-list { display: flex; flex-direction: column; gap: 8px; }
.dimension-item { display: flex; gap: 8px; align-items: center; }
.scene-overrides { display: flex; flex-direction: column; gap: 4px; }
.scene-override-item { border: 1px solid var(--el-border-color-lighter); border-radius: 8px; overflow: hidden; }
.scene-header { display: flex; align-items: center; gap: 8px; padding: 12px; cursor: pointer; transition: background 0.2s; }
.scene-header:hover { background: var(--el-fill-color-light); }
.expand-icon { margin-left: auto; transition: transform 0.2s; }
.expand-icon.expanded { transform: rotate(180deg); }
.scene-form { padding: 0 16px 16px; border-top: 1px solid var(--el-border-color-lighter); }
</style>
