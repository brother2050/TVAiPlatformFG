<template>
  <div class="video-adjust">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>剪视频</h1>
      </div>
    </header>

    <el-row :gutter="20">
      <!-- 视频预览 -->
      <el-col :span="16">
        <el-card class="preview-card">
          <div class="video-preview">
            <div class="preview-screen">
              <el-icon :size="64" color="#666"><VideoPlay /></el-icon>
              <p>视频预览</p>
            </div>
          </div>
          <div class="playback-controls">
            <el-button :icon="Back" size="small" @click="skipBackward" />
            <el-button :type="isPlaying ? 'warning' : 'primary'" size="small" @click="togglePlay">
              <el-icon><VideoPlay v-if="!isPlaying" /><VideoPause v-else /></el-icon>
            </el-button>
            <el-button :icon="Right" size="small" @click="skipForward" />
            <span class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
            <el-slider v-model="currentTime" :min="0" :max="duration" :step="0.1" style="flex: 1; margin: 0 16px" />
            <el-button size="small" @click="toggleMute">
              <el-icon><Microphone v-if="isMuted" /><Headset v-else /></el-icon>
            </el-button>
          </div>

          <!-- 裁剪 -->
          <el-card class="sub-card">
            <template #header><span>裁剪</span></template>
            <el-row :gutter="12">
              <el-col :span="8">
                <el-form-item label="起始">
                  <el-input-number v-model="trimStart" :min="0" :max="duration" :step="0.1" size="small" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="结束">
                  <el-input-number v-model="trimEnd" :min="0" :max="duration" :step="0.1" size="small" />
                </el-form-item>
              </el-col>
              <el-col :span="8" style="display: flex; align-items: flex-end">
                <el-button type="primary" size="small" @click="applyTrim">应用裁剪</el-button>
              </el-col>
            </el-row>
          </el-card>
        </el-card>
      </el-col>

      <!-- 操作面板 -->
      <el-col :span="8">
        <el-card class="ops-card">
          <template #header><span>视频操作</span></template>
          <div class="ops-list">
            <el-button class="op-item" @click="regenerateVideo" :loading="operating">
              <el-icon><RefreshRight /></el-icon> 重新生成
            </el-button>
            <el-button class="op-item" @click="showStartFrame = true">
              <el-icon><Picture /></el-icon> 换起始画面
            </el-button>
            <el-upload :show-file-list="false" :before-upload="handleUpload" accept="video/*">
              <el-button class="op-item" style="width: 100%"><el-icon><Upload /></el-icon> 上传替换</el-button>
            </el-upload>
            <el-button class="op-item" @click="showMotionDesc = true">
              <el-icon><Edit /></el-icon> 改运动描述
            </el-button>
            <el-button class="op-item" @click="changeSpeed">
              <el-icon><DArrowRight /></el-icon> 变速 ({{ playbackSpeed }}x)
            </el-button>
            <el-button class="op-item" @click="reverseVideo">
              <el-icon><Back /></el-icon> 倒放
            </el-button>
          </div>
        </el-card>

        <!-- 转场设置 -->
        <el-card class="sub-card">
          <template #header><span>镜头衔接（转场）</span></template>
          <el-form label-width="80px">
            <el-form-item label="转场类型">
              <el-select v-model="transition" placeholder="选择转场">
                <el-option label="无" value="none" />
                <el-option label="淡入淡出" value="fade" />
                <el-option label="交叉溶解" value="dissolve" />
                <el-option label="擦除" value="wipe" />
                <el-option label="推拉" value="push" />
                <el-option label="闪白" value="flash" />
                <el-option label="缩放" value="zoom" />
              </el-select>
            </el-form-item>
            <el-form-item label="时长(秒)">
              <el-input-number v-model="transitionDuration" :min="0.1" :max="3" :step="0.1" />
            </el-form-item>
          </el-form>
          <el-button type="primary" size="small" @click="applyTransition">应用转场</el-button>
        </el-card>

        <!-- 画面调色 -->
        <el-card class="sub-card">
          <template #header><span>画面调色</span></template>
          <div class="color-controls">
            <div class="color-item">
              <label>亮度 {{ colorParams.brightness }}</label>
              <el-slider v-model="colorParams.brightness" :min="-100" :max="100" />
            </div>
            <div class="color-item">
              <label>对比度 {{ colorParams.contrast }}</label>
              <el-slider v-model="colorParams.contrast" :min="-100" :max="100" />
            </div>
            <div class="color-item">
              <label>饱和度 {{ colorParams.saturation }}</label>
              <el-slider v-model="colorParams.saturation" :min="-100" :max="100" />
            </div>
            <div class="color-item">
              <label>色温 {{ colorParams.temperature }}</label>
              <el-slider v-model="colorParams.temperature" :min="-100" :max="100" />
            </div>
          </div>
          <div style="display: flex; gap: 8px; margin-top: 8px">
            <el-button size="small" @click="resetColor">重置</el-button>
            <el-button type="primary" size="small" @click="applyColor">应用调色</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 改运动描述弹窗 -->
    <el-dialog v-model="showMotionDesc" title="修改运动描述" width="500px">
      <el-input v-model="motionDescription" type="textarea" :rows="4" placeholder="描述镜头运动，如：缓慢向前推进，跟随主角移动…" />
      <template #footer>
        <el-button @click="showMotionDesc = false">取消</el-button>
        <el-button type="primary" @click="applyMotionDesc" :loading="operating">重新生成</el-button>
      </template>
    </el-dialog>

    <!-- 换起始画面弹窗 -->
    <el-dialog v-model="showStartFrame" title="更换起始画面" width="500px">
      <el-upload drag :show-file-list="false" :before-upload="handleStartFrame" accept="image/*">
        <el-icon :size="40"><Upload /></el-icon>
        <div>拖拽或点击上传起始画面</div>
      </el-upload>
      <el-divider>或</el-divider>
      <el-input v-model="startFramePrompt" type="textarea" :rows="2" placeholder="用文字描述新的起始画面…" />
      <template #footer>
        <el-button @click="showStartFrame = false">取消</el-button>
        <el-button type="primary" @click="applyStartFrame">应用</el-button>
      </template>
    </el-dialog>

    <!-- 变速弹窗 -->
    <el-dialog v-model="showSpeedDialog" title="变速设置" width="400px">
      <el-form label-width="60px">
        <el-form-item label="速度">
          <el-slider v-model="playbackSpeed" :min="0.25" :max="4" :step="0.25" show-input />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSpeedDialog = false">取消</el-button>
        <el-button type="primary" @click="applySpeed">应用</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, VideoPlay, VideoPause, Back, Right,
  RefreshRight, Picture, Upload, Edit, DArrowRight, Headset, Microphone,
} from '@element-plus/icons-vue'


const isPlaying = ref(false)
const isMuted = ref(false)
const currentTime = ref(0)
const duration = ref(30)
const trimStart = ref(0)
const trimEnd = ref(30)
const operating = ref(false)
const transition = ref('fade')
const transitionDuration = ref(0.5)
const playbackSpeed = ref(1)
const showMotionDesc = ref(false)
const motionDescription = ref('')
const showStartFrame = ref(false)
const startFramePrompt = ref('')
const showSpeedDialog = ref(false)

const colorParams = reactive({
  brightness: 0,
  contrast: 0,
  saturation: 0,
  temperature: 0,
})

function formatTime(sec: number) {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

function togglePlay() {
  isPlaying.value = !isPlaying.value
}

function toggleMute() {
  isMuted.value = !isMuted.value
}

function skipBackward() {
  currentTime.value = Math.max(0, currentTime.value - 2)
}

function skipForward() {
  currentTime.value = Math.min(duration.value, currentTime.value + 2)
}

async function applyTrim() {
  ElMessage.success(`裁剪: ${formatTime(trimStart.value)} → ${formatTime(trimEnd.value)}`)
}

async function regenerateVideo() {
  operating.value = true
  try {
    ElMessage.success('视频重新生成任务已提交')
  } finally {
    operating.value = false
  }
}

function handleUpload(_file: File) {
  ElMessage.success('视频上传成功')
  return false
}

async function applyMotionDesc() {
  if (!motionDescription.value.trim()) {
    ElMessage.warning('请输入运动描述')
    return
  }
  operating.value = true
  try {
    showMotionDesc.value = false
    ElMessage.success('运动描述更新任务已提交')
  } finally {
    operating.value = false
  }
}

function changeSpeed() {
  showSpeedDialog.value = true
}

function applySpeed() {
  showSpeedDialog.value = false
  ElMessage.success(`播放速度已设为 ${playbackSpeed.value}x`)
}

async function reverseVideo() {
  try {
    await ElMessageBox.confirm('确定要倒放此视频？', '确认')
    ElMessage.success('倒放任务已提交')
  } catch { /* cancelled */ }
}

function handleStartFrame(_file: File) {
  ElMessage.success('起始画面已上传')
  showStartFrame.value = false
  return false
}

function applyStartFrame() {
  showStartFrame.value = false
  ElMessage.success('起始画面更新任务已提交')
}

function applyTransition() {
  ElMessage.success(`转场「${transition.value}」已应用`)
}

function resetColor() {
  colorParams.brightness = 0
  colorParams.contrast = 0
  colorParams.saturation = 0
  colorParams.temperature = 0
}

function applyColor() {
  ElMessage.success('调色参数已应用')
}
</script>

<style scoped>
.video-adjust { padding: 24px; }
.page-header { display: flex; align-items: center; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.preview-card { margin-bottom: 0; }
.video-preview { margin-bottom: 12px; }
.preview-screen { height: 360px; background: #1a1a2e; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #666; }
.playback-controls { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
.time-display { font-family: monospace; font-size: 13px; white-space: nowrap; }
.sub-card { margin-top: 16px; }
.ops-list { display: flex; flex-direction: column; gap: 8px; }
.op-item { width: 100%; }
.color-controls { display: flex; flex-direction: column; gap: 12px; }
.color-item label { display: block; font-size: 12px; color: var(--el-text-color-secondary); margin-bottom: 4px; }
</style>
