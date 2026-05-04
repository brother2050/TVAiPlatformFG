<template>
  <div class="batch-production">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>批量生产</h1>
      </div>
      <div class="header-actions">
        <el-button @click="showBatchDialog = true">
          <el-icon><Setting /></el-icon> 批量设置
        </el-button>
      </div>
    </header>

    <!-- 项目概览 -->
    <el-card class="overview-card">
      <template #header>
        <div class="card-header">
          <span>生产概览</span>
          <el-tag type="success">项目中</el-tag>
        </div>
      </template>
      <el-descriptions :column="4" border>
        <el-descriptions-item label="项目名称">{{ projectInfo.title }}</el-descriptions-item>
        <el-descriptions-item label="总集数">{{ projectInfo.totalEpisodes }} 集</el-descriptions-item>
        <el-descriptions-item label="已完成">
          <el-tag size="small" type="success">{{ completedCount }} 集</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="进行中">
          <el-tag size="small" type="warning">{{ processingCount }} 集</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="待生产">{{ pendingCount }} 集</el-descriptions-item>
        <el-descriptions-item label="预计时长">{{ projectInfo.estimatedDuration }}</el-descriptions-item>
        <el-descriptions-item label="当前阶段">
          <el-tag size="small" type="info">{{ currentStage }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="总进度">
          <el-progress :percentage="overallProgress" :stroke-width="12" style="width: 200px" />
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 批量控制 -->
    <el-card class="control-card">
      <template #header><span>批量控制</span></template>
      <div class="control-bar">
        <div class="stage-select">
          <label>选择阶段：</label>
          <el-checkbox-group v-model="selectedStages">
            <el-checkbox label="keyframes">关键帧</el-checkbox>
            <el-checkbox label="clips">片段剪辑</el-checkbox>
            <el-checkbox label="voices">语音合成</el-checkbox>
            <el-checkbox label="bgm">背景音乐</el-checkbox>
            <el-checkbox label="subtitles">字幕生成</el-checkbox>
            <el-checkbox label="timeline">时间线组装</el-checkbox>
            <el-checkbox label="composite">最终合成</el-checkbox>
          </el-checkbox-group>
        </div>
        <div class="control-buttons">
          <el-button type="primary" size="large" @click="startBatchProduction" :loading="batchProducing">
            <el-icon><VideoPlay /></el-icon> 开始批量生产
          </el-button>
          <el-button size="large" @click="pauseAll" :disabled="!hasProcessing">
            <el-icon><VideoPause /></el-icon> 暂停全部
          </el-button>
          <el-button type="danger" size="large" @click="stopAll" :disabled="!hasProcessing">
            <el-icon><Close /></el-icon> 停止全部
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 集数列表 -->
    <el-card class="episodes-card">
      <template #header>
        <div class="card-header">
          <span>集数列表</span>
          <div class="header-toolbar">
            <el-input v-model="searchKeyword" placeholder="搜索集数" size="small" style="width: 200px" clearable>
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-select v-model="filterStatus" size="small" style="width: 120px" clearable placeholder="状态筛选">
              <el-option label="全部" value="" />
              <el-option label="已完成" value="completed" />
              <el-option label="进行中" value="processing" />
              <el-option label="待生产" value="pending" />
              <el-option label="失败" value="failed" />
            </el-select>
            <el-button size="small" @click="selectAll">全选</el-button>
          </div>
        </div>
      </template>
      <el-table :data="filteredEpisodes" @selection-change="handleSelectionChange" ref="tableRef">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="episode" label="集数" width="80" />
        <el-table-column prop="title" label="标题" min-width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="200">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :stroke-width="10" :show-text="false" />
          </template>
        </el-table-column>
        <el-table-column prop="currentStage" label="当前阶段" width="120">
          <template #default="{ row }">
            {{ stageLabel(row.currentStage) }}
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长" width="80">
          <template #default="{ row }">
            {{ row.duration || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="actions" label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" type="primary" text @click="produceSingle(row)" :loading="row._producing">
              <el-icon><VideoPlay /></el-icon> 生产
            </el-button>
            <el-button size="small" type="info" text @click="viewProgress(row)">
              <el-icon><View /></el-icon> 查看
            </el-button>
            <el-button size="small" type="success" text @click="previewEpisode(row)">
              <el-icon><VideoCamera /></el-icon> 预览
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 任务日志 -->
    <el-card class="log-card">
      <template #header>
        <div class="card-header">
          <span>任务日志</span>
          <el-button size="small" @click="clearLogs">清空</el-button>
        </div>
      </template>
      <div class="log-container" ref="logContainer">
        <div v-for="(log, idx) in logs" :key="idx" class="log-item" :class="log.type">
          <span class="log-time">{{ log.time }}</span>
          <el-tag size="small" :type="logType(log.type)" class="log-tag">{{ log.episode }}</el-tag>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </el-card>

    <!-- 批量设置弹窗 -->
    <el-dialog v-model="showBatchDialog" title="批量生产设置" width="600px">
      <el-form label-width="100px">
        <el-form-item label="并发数量">
          <el-input-number v-model="batchSettings.concurrent" :min="1" :max="5" />
          <span class="form-tip">同时生产的集数数量</span>
        </el-form-item>
        <el-form-item label="失败重试">
          <el-input-number v-model="batchSettings.retryCount" :min="0" :max="5" />
          <span class="form-tip">失败后自动重试次数</span>
        </el-form-item>
        <el-form-item label="质量预设">
          <el-select v-model="batchSettings.qualityPreset">
            <el-option label="快速预览" value="fast" />
            <el-option label="标准质量" value="standard" />
            <el-option label="最高质量" value="high" />
          </el-select>
        </el-form-item>
        <el-form-item label="完成后通知">
          <el-switch v-model="batchSettings.notifyOnComplete" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchDialog = false">取消</el-button>
        <el-button type="primary" @click="saveBatchSettings">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, VideoPlay, VideoPause, Close, Setting, Search, View, VideoCamera } from '@element-plus/icons-vue'
import { productionApi } from '@/api/production'

const route = useRoute()
const projectId = route.params.id as string
const tableRef = ref()
const logContainer = ref()

const batchProducing = ref(false)
const showBatchDialog = ref(false)
const searchKeyword = ref('')
const filterStatus = ref('')
const selectedEpisodes = ref<any[]>([])
const selectedStages = ref<string[]>(['keyframes', 'clips', 'voices', 'bgm', 'subtitles', 'timeline', 'composite'])

interface Episode {
  id: string
  episode: string
  title: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  currentStage: string
  duration?: string
  _producing?: boolean
}

interface LogItem {
  time: string
  episode: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}

const projectInfo = ref({
  title: '短剧项目A',
  totalEpisodes: 12,
  estimatedDuration: '约 30 分钟',
})

const episodes = ref<Episode[]>([
  { id: '1', episode: '第1集', title: '初遇', status: 'completed', progress: 100, currentStage: 'composite', duration: '2:30' },
  { id: '2', episode: '第2集', title: '误会', status: 'completed', progress: 100, currentStage: 'composite', duration: '2:45' },
  { id: '3', episode: '第3集', title: '告白', status: 'completed', progress: 100, currentStage: 'composite', duration: '2:15' },
  { id: '4', episode: '第4集', title: '抉择', status: 'processing', progress: 65, currentStage: 'voices' },
  { id: '5', episode: '第5集', title: '冲突', status: 'processing', progress: 40, currentStage: 'clips' },
  { id: '6', episode: '第6集', title: '和解', status: 'pending', progress: 0, currentStage: 'keyframes' },
  { id: '7', episode: '第7集', title: '转折', status: 'pending', progress: 0, currentStage: 'keyframes' },
  { id: '8', episode: '第8集', title: '高潮', status: 'pending', progress: 0, currentStage: 'keyframes' },
  { id: '9', episode: '第9集', title: '低谷', status: 'pending', progress: 0, currentStage: 'keyframes' },
  { id: '10', episode: '第10集', title: '重逢', status: 'pending', progress: 0, currentStage: 'keyframes' },
  { id: '11', episode: '第11集', title: '危机', status: 'pending', progress: 0, currentStage: 'keyframes' },
  { id: '12', episode: '第12集', title: '结局', status: 'pending', progress: 0, currentStage: 'keyframes' },
])

const batchSettings = ref({
  concurrent: 3,
  retryCount: 2,
  qualityPreset: 'standard',
  notifyOnComplete: true,
})

const logs = ref<LogItem[]>([
  { time: '14:30:25', episode: '第4集', message: '开始生产阶段: voices (语音合成)', type: 'info' },
  { time: '14:30:22', episode: '第5集', message: '开始生产阶段: clips (片段剪辑)', type: 'info' },
  { time: '14:30:20', episode: '第4集', message: '完成阶段: keyframes (关键帧)', type: 'success' },
  { time: '14:30:18', episode: '第4集', message: '开始生产阶段: keyframes (关键帧)', type: 'info' },
  { time: '14:28:15', episode: '第3集', message: '生产完成！', type: 'success' },
])

const completedCount = computed(() => episodes.value.filter(e => e.status === 'completed').length)
const processingCount = computed(() => episodes.value.filter(e => e.status === 'processing').length)
const pendingCount = computed(() => episodes.value.filter(e => e.status === 'pending').length)
const hasProcessing = computed(() => processingCount.value > 0)
const overallProgress = computed(() => {
  const total = episodes.value.reduce((sum, e) => sum + e.progress, 0)
  return Math.round(total / episodes.value.length)
})
const currentStage = computed(() => {
  const processing = episodes.value.find(e => e.status === 'processing')
  return processing ? stageLabel(processing.currentStage) : '等待中'
})

const filteredEpisodes = computed(() => {
  let result = episodes.value
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    result = result.filter(e => e.episode.toLowerCase().includes(kw) || e.title.toLowerCase().includes(kw))
  }
  if (filterStatus.value) {
    result = result.filter(e => e.status === filterStatus.value)
  }
  return result
})

function statusLabel(s: string) {
  const map: Record<string, string> = { completed: '已完成', processing: '进行中', pending: '待生产', failed: '失败' }
  return map[s] || s
}

function statusType(s: string) {
  const map: Record<string, string> = { completed: 'success', processing: 'warning', pending: 'info', failed: 'danger' }
  return map[s] || ''
}

function stageLabel(s: string) {
  const map: Record<string, string> = {
    keyframes: '关键帧', clips: '片段剪辑', voices: '语音合成',
    bgm: '背景音乐', subtitles: '字幕生成', timeline: '时间线组装', composite: '最终合成',
  }
  return map[s] || s
}

function logType(type: string) {
  const map: Record<string, string> = { info: 'info', success: 'success', warning: 'warning', error: 'danger' }
  return map[type] || 'info'
}

function handleSelectionChange(rows: Episode[]) {
  selectedEpisodes.value = rows
}

function selectAll() {
  if (filteredEpisodes.value.length === selectedEpisodes.value.length) {
    tableRef.value.clearSelection()
  } else {
    filteredEpisodes.value.forEach(row => tableRef.value.toggleRowSelection(row, true))
  }
}

function addLog(episode: string, message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') {
  const now = new Date()
  const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
  logs.value.unshift({ time, episode, message, type })
  nextTick(() => {
    if (logContainer.value) logContainer.value.scrollTop = 0
  })
}

async function startBatchProduction() {
  if (selectedEpisodes.value.length === 0) {
    ElMessage.warning('请选择要生产的集数')
    return
  }
  if (selectedStages.value.length === 0) {
    ElMessage.warning('请选择至少一个生产阶段')
    return
  }

  batchProducing.value = true
  try {
    for (const ep of selectedEpisodes.value) {
      if (ep.status === 'pending') {
        await productionApi.batchProduce(ep.id, selectedStages.value as any)
        ep.status = 'processing'
        addLog(ep.episode, `批量生产开始 (${selectedStages.value.length}个阶段)`, 'info')
      }
    }
    ElMessage.success('批量生产已启动')
  } catch (e: any) {
    ElMessage.error(e.message || '启动失败')
  } finally {
    batchProducing.value = false
  }
}

async function produceSingle(ep: Episode) {
  if (ep.status === 'completed') {
    ElMessage.info('该集已完成')
    return
  }
  ep._producing = true
  try {
    await productionApi.batchProduce(ep.id, selectedStages.value as any)
    ep.status = 'processing'
    addLog(ep.episode, '单集生产开始', 'info')
    ElMessage.success(`${ep.episode}生产已启动`)
  } catch (e: any) {
    ElMessage.error(e.message || '启动失败')
  } finally {
    ep._producing = false
  }
}

function viewProgress(ep: Episode) {
  ElMessage.info(`查看${ep.episode}的详细进度`)
}

function previewEpisode(ep: Episode) {
  if (ep.status === 'completed') {
    ElMessage.info(`预览${ep.episode}`)
  } else {
    ElMessage.warning('请先完成生产')
  }
}

async function pauseAll() {
  try {
    await ElMessageBox.confirm('确定暂停所有生产任务？', '暂停确认')
    addLog('系统', '所有生产任务已暂停', 'warning')
    ElMessage.success('已暂停')
  } catch {}
}

async function stopAll() {
  try {
    await ElMessageBox.confirm('确定停止所有生产任务？已生产的内容将保留。', '停止确认')
    for (const ep of episodes.value) {
      if (ep.status === 'processing') {
        ep.status = 'pending'
      }
    }
    addLog('系统', '所有生产任务已停止', 'error')
    ElMessage.success('已停止')
  } catch {}
}

function saveBatchSettings() {
  showBatchDialog.value = false
  ElMessage.success('批量设置已保存')
}

function clearLogs() {
  logs.value = []
}

onMounted(() => {})
</script>

<style scoped>
.batch-production { padding: 24px; max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.overview-card { margin-bottom: 20px; }
.control-card { margin-bottom: 20px; }
.episodes-card { margin-bottom: 20px; }
.log-card { margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.header-toolbar { display: flex; gap: 12px; align-items: center; }
.control-bar { display: flex; flex-direction: column; gap: 16px; }
.stage-select { display: flex; flex-direction: column; gap: 8px; }
.stage-select label { font-weight: 600; }
.control-buttons { display: flex; gap: 12px; }
.log-container { max-height: 300px; overflow-y: auto; }
.log-item { display: flex; align-items: center; gap: 12px; padding: 8px; border-bottom: 1px solid var(--el-border-color-lighter); }
.log-item:last-child { border-bottom: none; }
.log-time { font-family: monospace; font-size: 12px; color: var(--el-text-color-secondary); }
.log-tag { flex-shrink: 0; }
.log-message { font-size: 13px; }
.form-tip { margin-left: 12px; font-size: 12px; color: var(--el-text-color-secondary); }
</style>
