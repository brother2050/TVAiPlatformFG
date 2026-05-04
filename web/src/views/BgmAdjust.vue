<template>
  <div class="bgm-adjust">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>配音乐</h1>
      </div>
    </header>

    <el-row :gutter="20">
      <el-col :span="16">
        <!-- 背景音乐 -->
        <el-card class="section-card">
          <template #header>
            <div class="section-header">
              <span>背景音乐</span>
              <div>
                <el-button size="small" type="primary" @click="generateBgm" :loading="generating">
                  <el-icon><MagicStick /></el-icon> AI 生成
                </el-button>
                <el-upload :show-file-list="false" :before-upload="handleUploadBgm" accept="audio/*">
                  <el-button size="small"><el-icon><Upload /></el-icon> 上传</el-button>
                </el-upload>
              </div>
            </div>
          </template>
          <el-form label-width="80px">
            <el-form-item label="音乐描述">
              <el-input v-model="bgmDescription" type="textarea" :rows="2" placeholder="描述期望的背景音乐风格，如：温暖的钢琴曲，节奏缓慢…" />
            </el-form-item>
          </el-form>
          <div class="bgm-current">
            <div class="bgm-info">
              <el-icon :size="24"><Headset /></el-icon>
              <div>
                <p class="bgm-name">{{ currentBgm?.name || '未设置背景音乐' }}</p>
                <p class="bgm-desc">{{ currentBgm?.description || '-' }}</p>
              </div>
            </div>
            <div class="bgm-controls">
              <el-button size="small" :type="bgmPlaying ? 'warning' : 'primary'" @click="toggleBgm">
                <el-icon><VideoPlay v-if="!bgmPlaying" /><VideoPause v-else /></el-icon>
              </el-button>
              <el-slider v-model="bgmVolume" :min="0" :max="100" style="width: 120px" />
            </div>
          </div>
        </el-card>

        <!-- 环境音/音效 -->
        <el-card class="section-card">
          <template #header>
            <div class="section-header">
              <span>环境音 / 音效</span>
              <div>
                <el-button size="small" @click="showSfxLibrary = true">
                  <el-icon><Grid /></el-icon> 音效库
                </el-button>
                <el-upload :show-file-list="false" :before-upload="handleUploadSfx" accept="audio/*">
                  <el-button size="small"><el-icon><Upload /></el-icon> 添加</el-button>
                </el-upload>
              </div>
            </div>
          </template>
          <div class="sfx-list">
            <div v-for="sfx in sfxList" :key="sfx.id" class="sfx-item">
              <div class="sfx-info">
                <el-icon><Bell /></el-icon>
                <span class="sfx-name">{{ sfx.name }}</span>
                <el-tag size="small" type="info">{{ sfx.type }}</el-tag>
              </div>
              <div class="sfx-controls">
                <el-button size="small" text @click="playSfx(sfx)">
                  <el-icon><VideoPlay /></el-icon>
                </el-button>
                <el-slider v-model="sfx.volume" :min="0" :max="100" style="width: 80px" />
                <el-button size="small" text type="danger" @click="removeSfx(sfx.id)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <el-empty v-if="sfxList.length === 0" description="暂无音效" :image-size="60" />
          </div>
        </el-card>
      </el-col>

      <!-- 混音预览 -->
      <el-col :span="8">
        <el-card class="mix-card">
          <template #header><span>混音预览</span></template>
          <div class="mix-tracks">
            <div class="mix-track">
              <label>背景音乐</label>
              <el-slider v-model="mixLevels.bgm" :min="0" :max="100" />
              <span class="level-val">{{ mixLevels.bgm }}%</span>
            </div>
            <div class="mix-track">
              <label>人声</label>
              <el-slider v-model="mixLevels.voice" :min="0" :max="100" />
              <span class="level-val">{{ mixLevels.voice }}%</span>
            </div>
            <div class="mix-track">
              <label>环境音</label>
              <el-slider v-model="mixLevels.ambient" :min="0" :max="100" />
              <span class="level-val">{{ mixLevels.ambient }}%</span>
            </div>
            <div class="mix-track">
              <label>音效</label>
              <el-slider v-model="mixLevels.sfx" :min="0" :max="100" />
              <span class="level-val">{{ mixLevels.sfx }}%</span>
            </div>
          </div>
          <el-divider />
          <el-button type="primary" style="width: 100%" @click="previewMix">
            <el-icon><VideoPlay /></el-icon> 混音预览
          </el-button>
          <el-button style="width: 100%; margin-top: 8px" @click="applyMix">
            应用混音设置
          </el-button>
        </el-card>
      </el-col>
    </el-row>

    <!-- 音效库弹窗 -->
    <el-dialog v-model="showSfxLibrary" title="音效库" width="600px">
      <el-input v-model="sfxSearch" placeholder="搜索音效…" prefix-icon="Search" style="margin-bottom: 16px" />
      <el-row :gutter="12">
        <el-col v-for="sfx in filteredLibrary" :key="sfx.name" :span="8">
          <div class="lib-item" @click="addFromLibrary(sfx)">
            <el-icon :size="24"><Bell /></el-icon>
            <span>{{ sfx.name }}</span>
            <el-tag size="small">{{ sfx.category }}</el-tag>
          </div>
        </el-col>
      </el-row>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, MagicStick, Upload, Headset, VideoPlay, VideoPause,
  Bell, Delete, Grid,
} from '@element-plus/icons-vue'
import { editorApi } from '@/api/editor'
import { projectApi } from '@/api/project'
import { useRoute } from 'vue-router'

const route = useRoute()
const projectId = computed(() => route.params.id as string)
let episodeId = ''

const bgmDescription = ref('')
const generating = ref(false)
const bgmPlaying = ref(false)
const bgmVolume = ref(70)
const showSfxLibrary = ref(false)
const sfxSearch = ref('')

interface BgmItem {
  id: string
  name: string
  description: string
  url: string
}

interface SfxItem {
  id: string
  name: string
  type: string
  volume: number
  url: string
}

const currentBgm = ref<BgmItem | null>(null)

const sfxList = ref<SfxItem[]>([])

const mixLevels = reactive({
  bgm: 60,
  voice: 80,
  ambient: 30,
  sfx: 50,
})

// 加载 BGM 数据
async function loadBgmData() {
  if (!episodeId) return
  try {
    const res = await editorApi.getBgmData(episodeId)
    const data = res.data?.data
    if (data) {
      currentBgm.value = data.bgm
      sfxList.value = data.sfx || []
      mixLevels.bgm = data.mixLevels?.bgm ?? 60
      mixLevels.voice = data.mixLevels?.voice ?? 80
      mixLevels.ambient = data.mixLevels?.ambient ?? 30
      mixLevels.sfx = data.mixLevels?.sfx ?? 50
    }
  } catch (err) {
    console.error('加载 BGM 数据失败:', err)
  }
}

onMounted(async () => {
  // 先获取 episodes 列表，取第一个 episode 的 id
  const res = await projectApi.getEpisodes(projectId.value)
  const episodes = res.data.data
  if (episodes && episodes.length > 0) {
    episodeId = episodes[0].id
    loadBgmData()
  }
})

const sfxLibrary = [
  { name: '雨声', category: '环境' },
  { name: '雷声', category: '环境' },
  { name: '鸟鸣', category: '环境' },
  { name: '车流', category: '环境' },
  { name: '敲门', category: '动作' },
  { name: '爆炸', category: '动作' },
  { name: '玻璃碎', category: '动作' },
  { name: '手机铃', category: '日常' },
  { name: '键盘声', category: '日常' },
  { name: '心跳', category: '情感' },
  { name: '风铃', category: '氛围' },
  { name: '钟声', category: '氛围' },
]

const filteredLibrary = computed(() => {
  if (!sfxSearch.value) return sfxLibrary
  return sfxLibrary.filter(s => s.name.includes(sfxSearch.value))
})

async function generateBgm() {
  if (!bgmDescription.value.trim()) {
    ElMessage.warning('请输入音乐描述')
    return
  }
  generating.value = true
  try {
    await editorApi.generateBgm(episodeId, {
      description: bgmDescription.value,
    })
    ElMessage.success('BGM 生成任务已提交，请等待处理')
    await loadBgmData()
  } catch (err) {
    ElMessage.error('BGM 生成失败')
  } finally {
    generating.value = false
  }
}

async function toggleBgm() {
  bgmPlaying.value = !bgmPlaying.value
  // 保存 BGM 播放状态到后端
  try {
    await editorApi.updateBgm(episodeId, {
      is_playing: bgmPlaying.value,
      volume: bgmVolume.value,
    })
  } catch (err) {
    console.error('更新 BGM 状态失败:', err)
  }
}

async function handleUploadBgm(file: File) {
  try {
    const res = await editorApi.uploadBgm(episodeId, file)
    const result = res.data?.data
    if (result?.url) {
      currentBgm.value = {
        id: result.id,
        name: file.name,
        description: '',
        url: result.url,
      }
      ElMessage.success('背景音乐上传成功')
    }
  } catch (err) {
    ElMessage.error('上传失败')
  }
  return false
}

async function handleUploadSfx(file: File) {
  try {
    const res = await editorApi.uploadSfx(episodeId, file)
    const result = res.data?.data
    sfxList.value.push({
      id: result?.id || Date.now().toString(),
      name: file.name,
      type: '自定义',
      volume: 60,
      url: result?.url || URL.createObjectURL(file),
    })
    ElMessage.success('音效添加成功')
  } catch (err) {
    sfxList.value.push({
      id: Date.now().toString(),
      name: file.name,
      type: '自定义',
      volume: 60,
      url: URL.createObjectURL(file),
    })
    ElMessage.success('音效添加成功')
  }
  return false
}

async function playSfx(sfx: SfxItem) {
  if (sfx.url) {
    const audio = new Audio(sfx.url)
    audio.volume = sfx.volume / 100
    audio.play()
  } else {
    ElMessage.info(`播放: ${sfx.name}`)
  }
}

async function removeSfx(id: string) {
  try {
    await editorApi.deleteSfx(episodeId, id)
  } catch (err) {
    console.error('删除音效失败:', err)
  }
  sfxList.value = sfxList.value.filter(s => s.id !== id)
  ElMessage.success('音效已删除')
}

async function addFromLibrary(sfx: { name: string; category: string }) {
  try {
    const res = await editorApi.addSfxFromLibrary(episodeId, {
      name: sfx.name,
      category: sfx.category,
    })
    const result = res.data?.data
    sfxList.value.push({
      id: result?.id || Date.now().toString(),
      name: sfx.name,
      type: sfx.category,
      volume: 60,
      url: result?.url || '',
    })
  } catch (err) {
    sfxList.value.push({
      id: Date.now().toString(),
      name: sfx.name,
      type: sfx.category,
      volume: 60,
      url: '',
    })
  }
  showSfxLibrary.value = false
  ElMessage.success(`已添加: ${sfx.name}`)
}

async function applyMix() {
  try {
    await editorApi.updateMixLevels(episodeId, {
      bgm: mixLevels.bgm,
      voice: mixLevels.voice,
      ambient: mixLevels.ambient,
      sfx: mixLevels.sfx,
    })
    ElMessage.success('混音设置已应用')
  } catch (err) {
    ElMessage.error('应用失败')
  }
}

function previewMix() {
  ElMessage.info('混音预览播放中…')
}
</script>

<style scoped>
.bgm-adjust { padding: 24px; }
.page-header { display: flex; align-items: center; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.section-card { margin-bottom: 16px; }
.section-header { display: flex; justify-content: space-between; align-items: center; }
.bgm-current { display: flex; justify-content: space-between; align-items: center; padding: 12px; background: var(--el-fill-color-lighter); border-radius: 8px; margin-top: 12px; }
.bgm-info { display: flex; align-items: center; gap: 12px; }
.bgm-name { margin: 0; font-weight: 600; }
.bgm-desc { margin: 2px 0 0; font-size: 12px; color: var(--el-text-color-secondary); }
.bgm-controls { display: flex; align-items: center; gap: 12px; }
.sfx-list { display: flex; flex-direction: column; gap: 8px; }
.sfx-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border: 1px solid var(--el-border-color-lighter); border-radius: 8px; }
.sfx-info { display: flex; align-items: center; gap: 8px; }
.sfx-name { font-weight: 500; }
.sfx-controls { display: flex; align-items: center; gap: 8px; }
.mix-card { position: sticky; top: 24px; }
.mix-tracks { display: flex; flex-direction: column; gap: 16px; }
.mix-track { display: flex; align-items: center; gap: 12px; }
.mix-track label { width: 70px; font-size: 13px; flex-shrink: 0; }
.level-val { width: 36px; text-align: right; font-size: 12px; color: var(--el-text-color-secondary); }
.lib-item { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 16px; border: 1px solid var(--el-border-color-lighter); border-radius: 8px; cursor: pointer; transition: all 0.2s; margin-bottom: 12px; }
.lib-item:hover { background: var(--el-color-primary-light-9); border-color: var(--el-color-primary-light-5); }
</style>
