<template>
  <div class="storage-monitor">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>存储空间</h1>
      </div>
      <div class="header-actions">
        <el-button @click="refreshStorage" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </header>

    <!-- 总体概览 -->
    <el-row :gutter="20" class="overview-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon used">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ formatBytes(storageInfo.used) }}</span>
            <span class="stat-label">已使用</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon total">
            <el-icon><FolderOpened /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ formatBytes(storageInfo.total) }}</span>
            <span class="stat-label">总容量</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon available">
            <el-icon><Box /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ formatBytes(storageInfo.available) }}</span>
            <span class="stat-label">可用空间</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon percent" :class="{ warning: storageInfo.percent > 80, danger: storageInfo.percent > 95 }">
            <el-icon><PieChart /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ storageInfo.percent }}%</span>
            <span class="stat-label">使用率</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 使用率进度条 -->
    <el-card class="progress-card">
      <div class="progress-header">
        <span>磁盘使用率</span>
        <el-tag :type="storageInfo.percent > 90 ? 'danger' : storageInfo.percent > 70 ? 'warning' : 'success'" size="small">
          {{ storageInfo.percent > 90 ? '空间不足' : storageInfo.percent > 70 ? '即将满' : '正常' }}
        </el-tag>
      </div>
      <el-progress
        :percentage="storageInfo.percent"
        :color="getProgressColor(storageInfo.percent)"
        :stroke-width="20"
        :show-text="true"
      />
    </el-card>

    <!-- 资产分类详情 -->
    <el-card class="detail-card">
      <template #header>
        <div class="card-header">
          <span>资产分类</span>
          <el-select v-model="selectedProject" placeholder="选择项目" size="small" style="width: 200px" clearable>
            <el-option v-for="p in projects" :key="p.id" :label="p.title" :value="p.id" />
          </el-select>
        </div>
      </template>
      <el-table :data="categoryData" stripe>
        <el-table-column prop="category" label="资产类型" width="120">
          <template #default="{ row }">
            <div class="category-cell">
              <el-icon :size="18" :color="row.color"><component :is="row.icon" /></el-icon>
              <span>{{ row.category }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="count" label="文件数" width="100" align="center" />
        <el-table-column prop="size" label="占用空间" width="140" align="right">
          <template #default="{ row }">
            <span class="size-value">{{ formatBytes(row.size) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="percent" label="占比" width="200">
          <template #default="{ row }">
            <el-progress :percentage="row.percent" :color="row.color" :stroke-width="10" :show-text="false" />
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作" width="180" align="center">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="optimizeCategory(row)">
              <el-icon><Compress /></el-icon> 优化
            </el-button>
            <el-button size="small" text type="danger" @click="cleanCategory(row)">
              <el-icon><Delete /></el-icon> 清理
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 大文件列表 -->
    <el-card class="files-card">
      <template #header>
        <div class="card-header">
          <span>大文件 (Top 20)</span>
          <el-button size="small" @click="refreshLargeFiles">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>
      <el-table :data="largeFiles" stripe>
        <el-table-column prop="name" label="文件名" min-width="200" />
        <el-table-column prop="type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路径" min-width="150" show-overflow-tooltip />
        <el-table-column prop="size" label="大小" width="120" align="right">
          <template #default="{ row }">
            <span class="size-value">{{ formatBytes(row.size) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="modified" label="修改时间" width="160" />
        <el-table-column prop="action" label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="downloadFile(row)">
              <el-icon><Download /></el-icon>
            </el-button>
            <el-button size="small" text type="danger" @click="deleteFile(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 清理选项 -->
    <el-card class="clean-card">
      <template #header><span>快速清理</span></template>
      <div class="clean-options">
        <el-checkbox v-model="cleanOptions.tempFiles" label="临时文件" />
        <el-checkbox v-model="cleanOptions.duplicates" label="重复文件" />
        <el-checkbox v-model="cleanOptions.oldVersions" label="旧版本" />
        <el-checkbox v-model="cleanOptions.cacheFiles" label="缓存文件" />
        <el-checkbox v-model="cleanOptions.failedJobs" label="失败任务产物" />
      </div>
      <div class="clean-summary">
        <span>预计可释放: <strong>{{ formatBytes(estimatedCleanSize) }}</strong></span>
        <el-button type="danger" @click="executeClean" :loading="cleaning">
          <el-icon><Delete /></el-icon> 执行清理
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Refresh, Folder, FolderOpened, Box, PieChart, Compress, Delete, Download, VideoCamera, Picture, Microphone, Document, Film } from '@element-plus/icons-vue'
import http from '@/api/index'

const loading = ref(false)
const cleaning = ref(false)
const selectedProject = ref('')

interface StorageInfo {
  used: number
  total: number
  available: number
  percent: number
}

interface CategoryItem {
  category: string
  icon: any
  color: string
  count: number
  size: number
  percent: number
}

interface LargeFile {
  name: string
  type: string
  path: string
  size: number
  modified: string
}

const storageInfo = ref<StorageInfo>({
  used: 2.5 * 1024 * 1024 * 1024,
  total: 10 * 1024 * 1024 * 1024,
  available: 7.5 * 1024 * 1024 * 1024,
  percent: 25,
})

const projects = ref<{ id: string; title: string }[]>([])

const categoryData = ref<CategoryItem[]>([
  { category: '视频', icon: VideoCamera, color: '#409eff', count: 45, size: 1.2 * 1024 * 1024 * 1024, percent: 48 },
  { category: '图片', icon: Picture, color: '#67c23a', count: 328, size: 0.6 * 1024 * 1024 * 1024, percent: 24 },
  { category: '音频', icon: Microphone, color: '#e6a23c', count: 156, size: 0.4 * 1024 * 1024 * 1024, percent: 16 },
  { category: '字幕', icon: Document, color: '#909399', count: 89, size: 5 * 1024 * 1024, percent: 2 },
  { category: '其他', icon: Film, color: '#f56c6c', count: 23, size: 0.3 * 1024 * 1024 * 1024, percent: 10 },
])

const largeFiles = ref<LargeFile[]>([])

const cleanOptions = ref({
  tempFiles: true,
  duplicates: false,
  oldVersions: true,
  cacheFiles: true,
  failedJobs: false,
})

const estimatedCleanSize = computed(() => {
  let size = 0
  if (cleanOptions.value.tempFiles) size += 200 * 1024 * 1024
  if (cleanOptions.value.duplicates) size += 500 * 1024 * 1024
  if (cleanOptions.value.oldVersions) size += 300 * 1024 * 1024
  if (cleanOptions.value.cacheFiles) size += 150 * 1024 * 1024
  if (cleanOptions.value.failedJobs) size += 100 * 1024 * 1024
  return size
})

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function getProgressColor(percent: number): string {
  if (percent > 95) return '#f56c6c'
  if (percent > 80) return '#e6a23c'
  return '#67c23a'
}

async function refreshStorage() {
  loading.value = true
  try {
    // 模拟从后端获取存储信息
    await new Promise(resolve => setTimeout(resolve, 500))
    storageInfo.value = {
      used: 2.8 * 1024 * 1024 * 1024,
      total: 10 * 1024 * 1024 * 1024,
      available: 7.2 * 1024 * 1024 * 1024,
      percent: 28,
    }
    ElMessage.success('刷新成功')
  } catch (e) {
    ElMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

async function refreshLargeFiles() {
  largeFiles.value = [
    { name: 'episode_05_final_h265.mp4', type: '视频', path: '/storage/media/episodes/', size: 850 * 1024 * 1024, modified: '2024-01-15 14:30' },
    { name: 'episode_04_final_h265.mp4', type: '视频', path: '/storage/media/episodes/', size: 720 * 1024 * 1024, modified: '2024-01-14 16:20' },
    { name: 'character_ref_batch.webp', type: '图片', path: '/storage/images/characters/', size: 120 * 1024 * 1024, modified: '2024-01-13 10:15' },
    { name: 'voice_全角色.wav', type: '音频', path: '/storage/voices/', size: 85 * 1024 * 1024, modified: '2024-01-12 09:00' },
    { name: 'bgm_cinematic.mp3', type: '音频', path: '/storage/bgm/', size: 45 * 1024 * 1024, modified: '2024-01-11 18:45' },
  ]
}

async function optimizeCategory(row: CategoryItem) {
  try {
    await ElMessageBox.confirm(`将对「${row.category}」进行压缩优化，预计可节省空间。`, '优化确认')
    ElMessage.success(`${row.category}优化完成`)
  } catch {}
}

async function cleanCategory(row: CategoryItem) {
  try {
    await ElMessageBox.confirm(`确定清理所有${row.category}临时文件？`, '清理确认')
    ElMessage.success(`${row.category}清理完成`)
  } catch {}
}

async function downloadFile(row: LargeFile) {
  ElMessage.info(`开始下载: ${row.name}`)
}

async function deleteFile(row: LargeFile) {
  try {
    await ElMessageBox.confirm(`确定删除文件「${row.name}」？此操作不可恢复。`, '删除确认', {
      confirmButtonText: '删除',
      type: 'warning',
    })
    largeFiles.value = largeFiles.value.filter(f => f.name !== row.name)
    ElMessage.success('文件已删除')
  } catch {}
}

async function executeClean() {
  cleaning.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success(`清理完成，已释放 ${formatBytes(estimatedCleanSize.value)}`)
    await refreshStorage()
  } catch {
    ElMessage.error('清理失败')
  } finally {
    cleaning.value = false
  }
}

onMounted(async () => {
  await refreshStorage()
  await refreshLargeFiles()
})
</script>

<style scoped>
.storage-monitor { padding: 24px; max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.overview-row { margin-bottom: 20px; }
.stat-card { display: flex; align-items: center; gap: 16px; padding: 8px; }
.stat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; color: #fff; }
.stat-icon.used { background: linear-gradient(135deg, #667eea, #764ba2); }
.stat-icon.total { background: linear-gradient(135deg, #f093fb, #f5576c); }
.stat-icon.available { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.stat-icon.percent { background: linear-gradient(135deg, #43e97b, #38f9d7); }
.stat-icon.percent.warning { background: linear-gradient(135deg, #f6d365, #fda085); }
.stat-icon.percent.danger { background: linear-gradient(135deg, #ff9a9e, #fecfef); }
.stat-info { display: flex; flex-direction: column; }
.stat-value { font-size: 22px; font-weight: 700; }
.stat-label { font-size: 13px; color: var(--el-text-color-secondary); }
.progress-card { margin-bottom: 20px; }
.progress-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.detail-card { margin-bottom: 20px; }
.files-card { margin-bottom: 20px; }
.clean-card { margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.category-cell { display: flex; align-items: center; gap: 8px; }
.size-value { font-family: monospace; font-weight: 500; }
.clean-options { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 16px; }
.clean-summary { display: flex; justify-content: space-between; align-items: center; padding-top: 16px; border-top: 1px solid var(--el-border-color-lighter); }
</style>
