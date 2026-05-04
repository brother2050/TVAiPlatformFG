<template>
  <div class="export-page">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>导出作品</h1>
      </div>
    </header>

    <el-row :gutter="24">
      <!-- 视频预览 -->
      <el-col :span="16">
        <el-card class="preview-card">
          <template #header><span>最终视频预览</span></template>
          <div class="video-preview">
            <div class="preview-screen">
              <el-icon :size="64" color="#666"><VideoPlay /></el-icon>
              <p>最终成品预览</p>
            </div>
          </div>
          <div class="playback-controls">
            <el-button :type="isPlaying ? 'warning' : 'primary'" size="small" @click="isPlaying = !isPlaying">
              <el-icon><VideoPlay v-if="!isPlaying" /><VideoPause v-else /></el-icon>
            </el-button>
            <span class="time-info">0:00 / 2:00</span>
            <el-slider v-model="playPosition" :min="0" :max="100" style="flex: 1; margin: 0 16px" />
          </div>
        </el-card>

        <!-- 批量导出列表 -->
        <el-card class="batch-card" style="margin-top: 16px">
          <template #header>
            <div class="card-header">
              <span>批量导出</span>
              <el-checkbox v-model="selectAll" @change="handleSelectAll">全选</el-checkbox>
            </div>
          </template>
          <el-table :data="episodeList" @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="40" />
            <el-table-column label="集数" prop="episode" width="80" />
            <el-table-column label="标题" prop="title" />
            <el-table-column label="时长" prop="duration" width="100" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'ready' ? 'success' : row.status === 'pending' ? 'info' : 'warning'" size="small">
                  {{ statusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 12px; display: flex; justify-content: flex-end">
            <el-button type="primary" @click="batchExport" :disabled="selectedEpisodes.length === 0" :loading="exporting">
              批量导出 ({{ selectedEpisodes.length }}集)
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 导出设置 -->
      <el-col :span="8">
        <el-card class="settings-card">
          <template #header><span>导出设置</span></template>

          <!-- 分辨率 -->
          <div class="setting-group">
            <label>分辨率</label>
            <el-radio-group v-model="exportSettings.resolution" class="resolution-group">
              <el-radio-button value="720p">
                <div class="res-option">
                  <span class="res-label">720p</span>
                  <span class="res-detail">1280×720</span>
                </div>
              </el-radio-button>
              <el-radio-button value="1080p">
                <div class="res-option">
                  <span class="res-label">1080p</span>
                  <span class="res-detail">1920×1080</span>
                </div>
              </el-radio-button>
              <el-radio-button value="4k">
                <div class="res-option">
                  <span class="res-label">4K</span>
                  <span class="res-detail">3840×2160</span>
                </div>
              </el-radio-button>
            </el-radio-group>
          </div>

          <!-- 编码质量 -->
          <div class="setting-group">
            <label>编码质量</label>
            <el-slider
              v-model="exportSettings.quality"
              :min="1"
              :max="100"
              show-input
              :format-tooltip="(v: number) => `${v}%`"
            />
            <span class="quality-hint">
              {{ qualityLabel }} · 预估大小: {{ estimatedSize }}
            </span>
          </div>

          <!-- 水印 -->
          <div class="setting-group">
            <label>水印</label>
            <el-upload
              :show-file-list="false"
              :before-upload="handleWatermark"
              accept="image/*"
            >
              <el-button size="small">
                <el-icon><Upload /></el-icon>
                {{ exportSettings.watermark ? '更换水印' : '上传水印' }}
              </el-button>
            </el-upload>
            <div v-if="exportSettings.watermark" class="watermark-preview">
              <el-image :src="exportSettings.watermark" fit="contain" style="width: 80px; height: 40px" />
              <el-button text type="danger" size="small" @click="exportSettings.watermark = ''">移除</el-button>
            </div>
          </div>

          <!-- 片头 -->
          <div class="setting-group">
            <label>片头</label>
            <el-upload :show-file-list="false" :before-upload="handleIntro" accept="video/*">
              <el-button size="small"><el-icon><Upload /></el-icon> {{ exportSettings.intro ? '更换片头' : '上传片头' }}</el-button>
            </el-upload>
            <el-tag v-if="exportSettings.intro" size="small" closable @close="exportSettings.intro = ''">已设置</el-tag>
          </div>

          <!-- 片尾 -->
          <div class="setting-group">
            <label>片尾</label>
            <el-upload :show-file-list="false" :before-upload="handleOutro" accept="video/*">
              <el-button size="small"><el-icon><Upload /></el-icon> {{ exportSettings.outro ? '更换片尾' : '上传片尾' }}</el-button>
            </el-upload>
            <el-tag v-if="exportSettings.outro" size="small" closable @close="exportSettings.outro = ''">已设置</el-tag>
          </div>

          <!-- 编码格式 -->
          <div class="setting-group">
            <label>编码格式</label>
            <el-select v-model="exportSettings.codec" style="width: 100%">
              <el-option label="H.264 (兼容性最好)" value="h264" />
              <el-option label="H.265 (体积更小)" value="h265" />
              <el-option label="VP9 (WebM)" value="vp9" />
            </el-select>
          </div>

          <!-- 帧率 -->
          <div class="setting-group">
            <label>帧率</label>
            <el-select v-model="exportSettings.fps" style="width: 100%">
              <el-option label="24 fps (电影)" :value="24" />
              <el-option label="30 fps (标准)" :value="30" />
              <el-option label="60 fps (流畅)" :value="60" />
            </el-select>
          </div>

          <el-divider />

          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            @click="startExport"
            :loading="exporting"
          >
            <el-icon><Download /></el-icon> 一键导出
          </el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, VideoPlay, VideoPause, Upload, Download,
} from '@element-plus/icons-vue'


const isPlaying = ref(false)
const playPosition = ref(0)
const exporting = ref(false)
const selectAll = ref(false)

const exportSettings = reactive({
  resolution: '1080p' as string,
  quality: 80,
  watermark: '',
  intro: '',
  outro: '',
  codec: 'h264',
  fps: 30,
})

interface EpisodeItem {
  id: string
  episode: string
  title: string
  duration: string
  status: 'ready' | 'pending' | 'processing'
}

const episodeList = ref<EpisodeItem[]>([
  { id: '1', episode: '第1集', title: '初遇', duration: '2:00', status: 'ready' },
  { id: '2', episode: '第2集', title: '误会', duration: '2:15', status: 'ready' },
  { id: '3', episode: '第3集', title: '告白', duration: '1:50', status: 'pending' },
  { id: '4', episode: '第4集', title: '抉择', duration: '2:30', status: 'processing' },
  { id: '5', episode: '第5集', title: '结局', duration: '3:00', status: 'ready' },
])

const selectedEpisodes = ref<EpisodeItem[]>([])

const qualityLabel = computed(() => {
  if (exportSettings.quality >= 90) return '极高质量'
  if (exportSettings.quality >= 70) return '高质量'
  if (exportSettings.quality >= 50) return '标准'
  return '压缩'
})

const estimatedSize = computed(() => {
  const base = exportSettings.resolution === '4k' ? 200 : exportSettings.resolution === '1080p' ? 80 : 30
  const size = base * (exportSettings.quality / 100)
  return `~${size.toFixed(0)} MB/集`
})

function statusLabel(s: string) {
  const map: Record<string, string> = { ready: '就绪', pending: '待处理', processing: '处理中' }
  return map[s] || s
}

function handleSelectionChange(rows: EpisodeItem[]) {
  selectedEpisodes.value = rows
}

function handleSelectAll(_val: boolean) {
  // el-table handles via toggleAllSelection
}

function handleWatermark(file: File) {
  exportSettings.watermark = URL.createObjectURL(file)
  ElMessage.success('水印已上传')
  return false
}

function handleIntro(file: File) {
  exportSettings.intro = URL.createObjectURL(file)
  ElMessage.success('片头已上传')
  return false
}

function handleOutro(file: File) {
  exportSettings.outro = URL.createObjectURL(file)
  ElMessage.success('片尾已上传')
  return false
}

async function startExport() {
  exporting.value = true
  try {
    ElMessage.success('导出任务已提交，请在任务中心查看进度')
  } catch (e: any) {
    ElMessage.error(e.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

async function batchExport() {
  exporting.value = true
  try {
    ElMessage.success(`批量导出 ${selectedEpisodes.value.length} 集，任务已提交`)
  } catch (e: any) {
    ElMessage.error(e.message || '批量导出失败')
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.export-page { padding: 24px; max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; align-items: center; margin-bottom: 24px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.preview-card { margin-bottom: 0; }
.video-preview { margin-bottom: 12px; }
.preview-screen { height: 400px; background: #1a1a2e; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #666; }
.playback-controls { display: flex; align-items: center; gap: 12px; }
.time-info { font-family: monospace; font-size: 13px; white-space: nowrap; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.settings-card { position: sticky; top: 24px; }
.setting-group { margin-bottom: 20px; }
.setting-group label { display: block; font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.resolution-group { display: flex; flex-direction: column; gap: 6px; }
.res-option { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.res-label { font-weight: 600; }
.res-detail { font-size: 11px; color: var(--el-text-color-secondary); }
.quality-hint { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px; display: block; }
.watermark-preview { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
</style>
