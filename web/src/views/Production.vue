<template>
  <div class="production">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>开始制作</h1>
      </div>
      <div class="header-actions">
        <el-button @click="openBatchDialog" :disabled="selectedEpisodes.length === 0">
          <el-icon><Tickets /></el-icon>
          批量生产 ({{ selectedEpisodes.length }})
        </el-button>
        <el-button type="primary" @click="startProduce" :loading="producing">
          <el-icon><VideoPlay /></el-icon> 启动生产
        </el-button>
      </div>
    </header>

    <!-- 集数选择 -->
    <el-card class="episode-selector">
      <template #header>
        <div class="card-header">
          <span>选择要生产的集数</span>
          <el-button text size="small" @click="toggleAllEpisodes">
            {{ selectedEpisodes.length === episodes.length ? '取消全选' : '全选' }}
          </el-button>
        </div>
      </template>
      <el-checkbox-group v-model="selectedEpisodes">
        <el-checkbox-button v-for="ep in episodes" :key="ep.id" :value="ep.id">
          第{{ ep.episode_number }}集 - {{ ep.title || '未命名' }}
        </el-checkbox-button>
      </el-checkbox-group>
    </el-card>

    <!-- 生产进度 -->
    <div v-if="productionStore.tasks.length > 0" class="progress-section">
      <el-card>
        <template #header>
          <div class="progress-header">
            <span>生产进度</span>
            <el-tag :type="overallStatusType">{{ overallStatusLabel }}</el-tag>
          </div>
        </template>
        <el-progress :percentage="overallProgress" :stroke-width="16" :status="overallProgress >= 100 ? 'success' : undefined" />
      </el-card>

      <!-- 阶段步骤条 -->
      <el-card class="stages-card">
        <el-steps :active="activeStageIndex" finish-status="success" direction="vertical" :space="80">
          <el-step
            v-for="stage in stages"
            :key="stage.key"
            :title="stage.label"
            :status="getStageStatus(stage.key)"
          >
            <template #description>
              <div class="stage-detail">
                <span class="stage-status">{{ stageStatusLabel(stage.key) }}</span>
                <el-progress
                  v-if="getStageProgress(stage.key) > 0"
                  :percentage="getStageProgress(stage.key)"
                  :stroke-width="6"
                  style="width: 200px"
                />
                <div class="stage-actions">
                  <el-button
                    v-if="getStageStatusVal(stage.key) === 'review'"
                    size="small"
                    type="success"
                    @click="approveStage(stage.key)"
                  >
                    审核通过
                  </el-button>
                  <el-button
                    v-if="['completed', 'failed', 'review'].includes(getStageStatusVal(stage.key))"
                    size="small"
                    @click="regenerateSingleStage(stage.key)"
                  >
                    重新生成
                  </el-button>
                  <el-button
                    v-if="getStageStatusVal(stage.key) === 'failed'"
                    size="small"
                    type="danger"
                    @click="viewError(stage.key)"
                  >
                    查看错误
                  </el-button>
                </div>
                <p v-if="getReviewNotes(stage.key)" class="review-notes">
                  备注: {{ getReviewNotes(stage.key) }}
                </p>
              </div>
            </template>
          </el-step>
        </el-steps>
      </el-card>
    </div>

    <div v-else class="empty-state">
      <el-empty description="尚未启动生产，选择集数后点击「启动生产」" />
    </div>

    <!-- 批量生产对话框 -->
    <el-dialog v-model="batchDialogVisible" title="批量生产" width="600px">
      <div class="batch-dialog-content">
        <p class="batch-info">
          将为 <strong>{{ selectedEpisodes.length }}</strong> 集生产所选阶段
        </p>
        
        <el-form label-width="80px">
          <el-form-item label="选择阶段">
            <el-checkbox-group v-model="selectedStages">
              <el-checkbox-button 
                v-for="stage in stages" 
                :key="stage.key" 
                :value="stage.key"
              >
                {{ stage.label }}
              </el-checkbox-button>
            </el-checkbox-group>
          </el-form-item>
          
          <el-form-item label="操作">
            <el-button size="small" @click="selectAllStages">全选</el-button>
            <el-button size="small" @click="selectTypicalStages">常用组合</el-button>
          </el-form-item>
        </el-form>

        <el-alert
          v-if="selectedStages.length > 0"
          type="info"
          :closable="false"
          show-icon
        >
          <template #title>
            将生产: {{ selectedStages.map(s => stages.find(st => st.key === s)?.label).join(' → ') }}
          </template>
        </el-alert>
      </div>
      
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="executeBatchProduce" :loading="batchProducing">
          开始批量生产
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, VideoPlay, Tickets } from '@element-plus/icons-vue'
import { useProductionStore } from '@/stores/production'
import { useProjectStore } from '@/stores/project'
import { PRODUCTION_STAGES, type ProductionStage } from '@/api/production'

const route = useRoute()
const projectId = route.params.id as string
const productionStore = useProductionStore()
const projectStore = useProjectStore()

const producing = ref(false)
const batchProducing = ref(false)
const selectedEpisodes = ref<string[]>([])
const batchDialogVisible = ref(false)
const selectedStages = ref<ProductionStage[]>([])

interface Episode {
  id: string
  episode_number: number
  title: string
}
const episodes = ref<Episode[]>([])

const stages = PRODUCTION_STAGES

const overallProgress = computed(() => {
  const p = productionStore.progress
  const values = Object.values(p)
  if (values.length === 0) return 0
  return Math.round(values.reduce((a, b) => a + b, 0) / values.length)
})

const overallStatusType = computed(() => {
  if (overallProgress.value >= 100) return 'success'
  if (productionStore.tasks.some(t => t.status === 'failed')) return 'danger'
  if (productionStore.tasks.some(t => t.status === 'processing')) return 'warning'
  return 'info'
})

const overallStatusLabel = computed(() => {
  if (overallProgress.value >= 100) return '已完成'
  if (productionStore.tasks.some(t => t.status === 'failed')) return '有失败'
  if (productionStore.tasks.some(t => t.status === 'processing')) return '生产中'
  return '待处理'
})

const activeStageIndex = computed(() => {
  const idx = stages.findIndex(s => {
    const task = productionStore.tasks.find(t => t.stage === s.key)
    return !task || task.status === 'pending'
  })
  return idx === -1 ? stages.length : idx
})

function getStageStatusVal(stageKey: string): string {
  return productionStore.tasks.find(t => t.stage === stageKey)?.status || 'pending'
}

function getStageStatus(stageKey: string) {
  const status = getStageStatusVal(stageKey)
  const map: Record<string, string> = {
    pending: 'wait', processing: 'process', review: 'process',
    completed: 'success', failed: 'error',
  }
  return map[status] || 'wait'
}

function stageStatusLabel(stageKey: string) {
  const status = getStageStatusVal(stageKey)
  const map: Record<string, string> = {
    pending: '待处理', processing: '处理中…', review: '待审核',
    completed: '已完成', failed: '失败',
  }
  return map[status] || status
}

function getStageProgress(stageKey: string): number {
  return productionStore.progress[stageKey] || 0
}

function getReviewNotes(stageKey: string): string {
  return productionStore.tasks.find(t => t.stage === stageKey)?.review_notes || ''
}

// 全选/取消全选集数
function toggleAllEpisodes() {
  if (selectedEpisodes.value.length === episodes.value.length) {
    selectedEpisodes.value = []
  } else {
    selectedEpisodes.value = episodes.value.map(ep => ep.id)
  }
}

// 打开批量生产对话框
function openBatchDialog() {
  selectedStages.value = []
  batchDialogVisible.value = true
}

// 全选阶段
function selectAllStages() {
  selectedStages.value = stages.map(s => s.key)
}

// 选择常用组合 (keyframes -> composite 完整流程)
function selectTypicalStages() {
  selectedStages.value = ['keyframes', 'clips', 'voices', 'bgm', 'subtitles', 'timeline', 'composite']
}

// 执行批量生产
async function executeBatchProduce() {
  if (selectedStages.value.length === 0) {
    ElMessage.warning('请至少选择一个阶段')
    return
  }
  
  batchDialogVisible.value = false
  batchProducing.value = true
  
  try {
    const results = []
    for (const epId of selectedEpisodes.value) {
      const res = await productionStore.batchProduceStages(epId, selectedStages.value)
      results.push(res)
    }
    
    const successCount = results.filter(r => r?.code === 0).length
    ElMessage.success(`批量生产任务已提交: ${successCount}/${selectedEpisodes.value.length} 集`)
    
    // 刷新进度
    for (const epId of selectedEpisodes.value) {
      productionStore.fetchTasks(epId)
    }
  } catch (e: any) {
    ElMessage.error(e.message || '批量生产启动失败')
  } finally {
    batchProducing.value = false
  }
}

async function startProduce() {
  if (selectedEpisodes.value.length === 0) {
    ElMessage.warning('请先选择要生产的集数')
    return
  }
  producing.value = true
  try {
    for (const epId of selectedEpisodes.value) {
      await productionStore.startProduction(epId)
    }
    ElMessage.success('生产任务已提交')
  } catch (e: any) {
    ElMessage.error(e.message || '生产启动失败')
  } finally {
    producing.value = false
  }
}

async function approveStage(stageKey: string) {
  ElMessage.success(`阶段「${stageKey}」审核通过`)
}

async function regenerateSingleStage(stageKey: string) {
  try {
    await ElMessageBox.confirm(`确定重新生成「${stages.find(s => s.key === stageKey)?.label}」阶段？`, '确认')
    
    if (selectedEpisodes.value.length === 0) {
      ElMessage.warning('请先选择要生产的集数')
      return
    }
    
    batchProducing.value = true
    try {
      for (const epId of selectedEpisodes.value) {
        await productionStore.batchProduceStages(epId, [stageKey as ProductionStage])
      }
      ElMessage.success('重新生成任务已提交')
      // 刷新进度
      for (const epId of selectedEpisodes.value) {
        productionStore.fetchTasks(epId)
      }
    } finally {
      batchProducing.value = false
    }
  } catch { /* cancelled */ }
}

function viewError(stageKey: string) {
  const task = productionStore.tasks.find(t => t.stage === stageKey)
  ElMessageBox.alert(task?.review_notes || '无详细错误信息', '错误详情', { type: 'error' })
}

onMounted(async () => {
  const res = await projectStore.fetchProject(projectId)
  if (res) {
    episodes.value = Array.from({ length: res.total_episodes }, (_, i) => ({
      id: `ep-${i + 1}`,
      episode_number: i + 1,
      title: '',
    }))
  }
  productionStore.fetchTasks(projectId)
})
</script>

<style scoped>
.production { padding: 24px; max-width: 1200px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.episode-selector { margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.progress-section { display: flex; flex-direction: column; gap: 16px; }
.progress-header { display: flex; justify-content: space-between; align-items: center; }
.stages-card { min-height: 400px; }
.stage-detail { display: flex; flex-direction: column; gap: 6px; }
.stage-status { font-size: 13px; color: var(--el-text-color-secondary); }
.stage-actions { display: flex; gap: 8px; margin-top: 4px; }
.review-notes { font-size: 12px; color: var(--el-color-danger); margin: 4px 0 0; }
.empty-state { padding: 60px 0; }

/* 批量生产对话框 */
.batch-dialog-content { padding: 10px 0; }
.batch-info { margin-bottom: 20px; font-size: 14px; color: var(--el-text-color-regular); }
</style>
