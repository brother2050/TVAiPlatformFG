<template>
  <div class="image-adjust">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>修图片</h1>
      </div>
    </header>

    <el-row :gutter="20">
      <!-- 图片预览 -->
      <el-col :span="16">
        <el-card class="preview-card">
          <div class="preview-toolbar">
            <el-button-group>
              <el-button size="small" @click="zoomLevel = Math.min(3, zoomLevel + 0.25)">
                <el-icon><ZoomIn /></el-icon>
              </el-button>
              <el-button size="small" @click="zoomLevel = Math.max(0.25, zoomLevel - 0.25)">
                <el-icon><ZoomOut /></el-icon>
              </el-button>
              <el-button size="small" @click="zoomLevel = 1">1:1</el-button>
              <el-button size="small" @click="fitWindow">适配</el-button>
            </el-button-group>
            <span class="zoom-label">{{ Math.round(zoomLevel * 100) }}%</span>
          </div>
          <div class="preview-container" ref="containerRef">
            <div class="preview-image" :style="{ transform: `scale(${zoomLevel})` }">
              <el-image
                v-if="currentImageUrl"
                :src="currentImageUrl"
                fit="contain"
                :preview-src-list="[currentImageUrl]"
              >
                <template #error>
                  <div class="img-placeholder">
                    <el-icon :size="48"><Picture /></el-icon>
                    <p>暂无图片</p>
                  </div>
                </template>
              </el-image>
              <div v-else class="img-placeholder">
                <el-icon :size="48"><Picture /></el-icon>
                <p>选择一个镜头查看图片</p>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 操作面板 -->
      <el-col :span="8">
        <el-card class="ops-card">
          <template #header><span>图片操作</span></template>
          <div class="ops-grid">
            <el-button @click="regenerate" :loading="operating" class="op-btn">
              <el-icon><RefreshRight /></el-icon> 重新画
            </el-button>
            <el-button @click="showInpaint = true" class="op-btn">
              <el-icon><Brush /></el-icon> 局部修改
            </el-button>
            <el-button @click="showPromptEdit = true" class="op-btn">
              <el-icon><Edit /></el-icon> 改描述词
            </el-button>
            <el-upload
              :show-file-list="false"
              :before-upload="handleUpload"
              accept="image/*"
            >
              <el-button class="op-btn"><el-icon><Upload /></el-icon> 上传替换</el-button>
            </el-upload>
            <el-button @click="showParamAdjust = true" class="op-btn">
              <el-icon><Setting /></el-icon> 调参数
            </el-button>
            <el-button @click="changeStyle" class="op-btn">
              <el-icon><MagicStick /></el-icon> 换风格
            </el-button>
            <el-button @click="enhanceQuality" :loading="enhancing" class="op-btn">
              <el-icon><FullScreen /></el-icon> 更清晰
            </el-button>
            <el-button @click="changeBackground" class="op-btn">
              <el-icon><Picture /></el-icon> 换背景
            </el-button>
          </div>
        </el-card>

        <!-- 历史版本 -->
        <el-card class="history-card">
          <template #header>
            <div class="history-header">
              <span>历史版本</span>
              <el-tag size="small">{{ versions.length }}个</el-tag>
            </div>
          </template>
          <div class="version-list">
            <div
              v-for="(v, idx) in versions"
              :key="v.id"
              class="version-item"
              :class="{ active: currentVersionId === v.id }"
              @click="switchVersion(v)"
            >
              <el-image :src="v.url" fit="cover" class="version-thumb">
                <template #error>
                  <div class="thumb-error"><el-icon><Picture /></el-icon></div>
                </template>
              </el-image>
              <div class="version-info">
                <span class="version-label">v{{ versions.length - idx }}</span>
                <span class="version-time">{{ v.time }}</span>
                <el-tag v-if="idx === 0" size="small" type="success">当前</el-tag>
              </div>
            </div>
            <div v-if="versions.length === 0" class="no-versions">暂无历史版本</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 局部修改弹窗 -->
    <el-dialog v-model="showInpaint" title="局部修改" width="600px">
      <el-alert title="在图片上涂抹需要修改的区域，然后描述修改内容" type="info" :closable="false" style="margin-bottom: 16px" />
      <div class="inpaint-canvas" style="height: 300px; background: #f5f5f5; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
        <span style="color: #999">画布区域（涂抹蒙版）</span>
      </div>
      <el-input v-model="inpaintPrompt" type="textarea" :rows="2" placeholder="描述修改内容…" style="margin-top: 12px" />
      <template #footer>
        <el-button @click="showInpaint = false">取消</el-button>
        <el-button type="primary" @click="doInpaint" :loading="operating">应用修改</el-button>
      </template>
    </el-dialog>

    <!-- 改描述词弹窗 -->
    <el-dialog v-model="showPromptEdit" title="修改描述词" width="500px">
      <el-input v-model="editPrompt" type="textarea" :rows="4" placeholder="输入新的图片描述词…" />
      <template #footer>
        <el-button @click="showPromptEdit = false">取消</el-button>
        <el-button type="primary" @click="applyPrompt" :loading="operating">重新生成</el-button>
      </template>
    </el-dialog>

    <!-- 调参数弹窗 -->
    <el-dialog v-model="showParamAdjust" title="调整参数" width="480px">
      <el-form label-width="80px">
        <el-form-item label="风格强度">
          <el-slider v-model="params.styleStrength" :min="0" :max="100" show-input />
        </el-form-item>
        <el-form-item label="细节程度">
          <el-slider v-model="params.detail" :min="0" :max="100" show-input />
        </el-form-item>
        <el-form-item label="色彩饱和度">
          <el-slider v-model="params.saturation" :min="0" :max="100" show-input />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showParamAdjust = false">取消</el-button>
        <el-button type="primary" @click="applyParams" :loading="operating">应用</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, ZoomIn, ZoomOut, Picture, RefreshRight, Brush,
  Edit, Upload, Setting, MagicStick, FullScreen,
} from '@element-plus/icons-vue'


const zoomLevel = ref(1)
const currentImageUrl = ref('')
const currentVersionId = ref('')
const operating = ref(false)
const enhancing = ref(false)
const containerRef = ref<HTMLElement>()

const showInpaint = ref(false)
const inpaintPrompt = ref('')
const showPromptEdit = ref(false)
const editPrompt = ref('')
const showParamAdjust = ref(false)
const params = reactive({ styleStrength: 50, detail: 60, saturation: 50 })

interface Version {
  id: string
  url: string
  time: string
}

const versions = ref<Version[]>([
  { id: 'v1', url: '', time: '2024-01-15 14:30' },
  { id: 'v2', url: '', time: '2024-01-15 14:25' },
])

function fitWindow() {
  zoomLevel.value = 0.75
}

function switchVersion(v: Version) {
  currentVersionId.value = v.id
  currentImageUrl.value = v.url
}

async function regenerate() {
  operating.value = true
  try {
    ElMessage.success('重新生成任务已提交')
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    operating.value = false
  }
}

async function doInpaint() {
  if (!inpaintPrompt.value.trim()) {
    ElMessage.warning('请输入修改描述')
    return
  }
  operating.value = true
  try {
    showInpaint.value = false
    ElMessage.success('局部修改任务已提交')
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    operating.value = false
  }
}

async function applyPrompt() {
  if (!editPrompt.value.trim()) {
    ElMessage.warning('请输入描述词')
    return
  }
  operating.value = true
  try {
    showPromptEdit.value = false
    ElMessage.success('描述词更新任务已提交')
  } finally {
    operating.value = false
  }
}

async function applyParams() {
  operating.value = true
  try {
    showParamAdjust.value = false
    ElMessage.success('参数调整任务已提交')
  } finally {
    operating.value = false
  }
}

async function handleUpload(_file: File) {
  operating.value = true
  try {
    ElMessage.success('图片上传成功')
  } catch (e: any) {
    ElMessage.error(e.message || '上传失败')
  } finally {
    operating.value = false
  }
  return false
}

function changeStyle() {
  ElMessageBox.prompt('输入目标风格', '换风格', {
    confirmButtonText: '应用',
    cancelButtonText: '取消',
    inputPlaceholder: '如：油画风格、水彩风格、赛博朋克',
  }).then(({ value }) => {
    ElMessage.success(`风格切换任务已提交: ${value}`)
  }).catch(() => {})
}

async function enhanceQuality() {
  enhancing.value = true
  try {
    ElMessage.success('画质增强任务已提交')
  } finally {
    enhancing.value = false
  }
}

function changeBackground() {
  ElMessageBox.prompt('描述新背景', '换背景', {
    confirmButtonText: '应用',
    cancelButtonText: '取消',
    inputPlaceholder: '如：夜晚城市天际线、樱花树下',
  }).then(({ value }) => {
    ElMessage.success(`背景替换任务已提交: ${value}`)
  }).catch(() => {})
}
</script>

<style scoped>
.image-adjust { padding: 24px; }
.page-header { display: flex; align-items: center; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.preview-card { margin-bottom: 0; }
.preview-toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.zoom-label { font-size: 13px; color: var(--el-text-color-secondary); }
.preview-container { overflow: auto; background: #1a1a2e; border-radius: 8px; min-height: 400px; display: flex; align-items: center; justify-content: center; }
.preview-image { transform-origin: center center; transition: transform 0.2s; }
.img-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 300px; color: #666; }
.ops-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.op-btn { width: 100%; }
.history-card { margin-top: 16px; }
.history-header { display: flex; justify-content: space-between; align-items: center; }
.version-list { display: flex; flex-direction: column; gap: 8px; max-height: 300px; overflow-y: auto; }
.version-item { display: flex; gap: 10px; padding: 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s; }
.version-item:hover { background: var(--el-fill-color-light); }
.version-item.active { background: var(--el-color-primary-light-9); }
.version-thumb { width: 60px; height: 40px; border-radius: 4px; flex-shrink: 0; }
.thumb-error { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: var(--el-fill-color-lighter); color: var(--el-text-color-placeholder); }
.version-info { display: flex; flex-direction: column; gap: 2px; }
.version-label { font-weight: 600; font-size: 13px; }
.version-time { font-size: 11px; color: var(--el-text-color-secondary); }
.no-versions { text-align: center; color: var(--el-text-color-secondary); font-size: 13px; padding: 20px 0; }
</style>
