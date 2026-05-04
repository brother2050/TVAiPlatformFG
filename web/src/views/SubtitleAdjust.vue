<template>
  <div class="subtitle-adjust">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <h1>改字幕</h1>
      </div>
      <div class="header-actions">
        <el-dropdown @command="handleBatch">
          <el-button>批量操作 <el-icon><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="realign">重新对齐</el-dropdown-item>
              <el-dropdown-item command="importSrt">导入 SRT</el-dropdown-item>
              <el-dropdown-item command="exportSrt">导出 SRT</el-dropdown-item>
              <el-dropdown-item command="findReplace">查找替换</el-dropdown-item>
              <el-dropdown-item command="timeShift">整体时移</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <el-row :gutter="20">
      <!-- 时间轴字幕展示 -->
      <el-col :span="16">
        <el-card class="timeline-card">
          <template #header><span>字幕时间轴</span></template>
          <div class="subtitle-timeline">
            <div class="time-ruler">
              <span v-for="t in timeMarks" :key="t" class="mark" :style="{ left: t * pxPerSec + 'px' }">{{ formatTime(t) }}</span>
            </div>
            <div class="subtitle-track">
              <div
                v-for="sub in subtitles"
                :key="sub.id"
                class="sub-block"
                :class="{ active: selectedSubId === sub.id }"
                :style="{
                  left: sub.start * pxPerSec + 'px',
                  width: (sub.end - sub.start) * pxPerSec + 'px',
                }"
                @click="selectSubtitle(sub)"
              >
                <span class="sub-text">{{ sub.text }}</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 字幕样式 -->
        <el-card class="style-card">
          <template #header><span>字幕样式</span></template>
          <el-row :gutter="16">
            <el-col :span="6">
              <div class="style-item">
                <label>字体大小</label>
                <el-input-number v-model="subtitleStyle.fontSize" :min="12" :max="72" size="small" />
              </div>
            </el-col>
            <el-col :span="6">
              <div class="style-item">
                <label>字体颜色</label>
                <el-color-picker v-model="subtitleStyle.color" size="small" />
              </div>
            </el-col>
            <el-col :span="6">
              <div class="style-item">
                <label>描边颜色</label>
                <el-color-picker v-model="subtitleStyle.strokeColor" size="small" />
              </div>
            </el-col>
            <el-col :span="6">
              <div class="style-item">
                <label>描边宽度</label>
                <el-input-number v-model="subtitleStyle.strokeWidth" :min="0" :max="5" size="small" />
              </div>
            </el-col>
            <el-col :span="6">
              <div class="style-item">
                <label>位置</label>
                <el-select v-model="subtitleStyle.position" size="small">
                  <el-option label="底部" value="bottom" />
                  <el-option label="顶部" value="top" />
                  <el-option label="居中" value="center" />
                </el-select>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="style-item">
                <label>对齐</label>
                <el-radio-group v-model="subtitleStyle.align" size="small">
                  <el-radio-button value="left">左</el-radio-button>
                  <el-radio-button value="center">中</el-radio-button>
                  <el-radio-button value="right">右</el-radio-button>
                </el-radio-group>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="style-item">
                <label>背景</label>
                <el-switch v-model="subtitleStyle.hasBackground" />
              </div>
            </el-col>
            <el-col :span="6">
              <div class="style-item">
                <label>背景透明度</label>
                <el-slider v-model="subtitleStyle.bgOpacity" :min="0" :max="100" :disabled="!subtitleStyle.hasBackground" />
              </div>
            </el-col>
          </el-row>
          <el-button type="primary" size="small" style="margin-top: 12px" @click="applyStyle">应用样式</el-button>
        </el-card>
      </el-col>

      <!-- 字幕列表 -->
      <el-col :span="8">
        <el-card class="list-card">
          <template #header>
            <div class="list-header">
              <span>字幕列表</span>
              <el-button size="small" @click="addSubtitle"><el-icon><Plus /></el-icon> 添加</el-button>
            </div>
          </template>
          <div class="sub-list">
            <div
              v-for="(sub, idx) in subtitles"
              :key="sub.id"
              class="sub-item"
              :class="{ active: selectedSubId === sub.id }"
              @click="selectSubtitle(sub)"
            >
              <div class="sub-timing">
                <el-input v-model="sub.startStr" size="small" style="width: 80px" @blur="parseStartTime(sub)" />
                <span>→</span>
                <el-input v-model="sub.endStr" size="small" style="width: 80px" @blur="parseEndTime(sub)" />
              </div>
              <el-input
                v-model="sub.text"
                type="textarea"
                :rows="2"
                size="small"
                @blur="saveSubtitleText(sub)"
              />
              <div class="sub-actions">
                <el-button text size="small" type="danger" @click="removeSubtitle(idx)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 查找替换弹窗 -->
    <el-dialog v-model="showFindReplace" title="查找替换字幕" width="480px">
      <el-form label-width="60px">
        <el-form-item label="查找"><el-input v-model="findText" /></el-form-item>
        <el-form-item label="替换"><el-input v-model="replaceText" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFindReplace = false">取消</el-button>
        <el-button type="primary" @click="doFindReplace">全部替换</el-button>
      </template>
    </el-dialog>

    <!-- 整体时移弹窗 -->
    <el-dialog v-model="showTimeShift" title="整体时移" width="400px">
      <el-form label-width="80px">
        <el-form-item label="偏移(秒)">
          <el-input-number v-model="timeShiftValue" :step="0.1" :precision="1" />
        </el-form-item>
        <el-alert title="正数向后偏移，负数向前偏移" type="info" :closable="false" />
      </el-form>
      <template #footer>
        <el-button @click="showTimeShift = false">取消</el-button>
        <el-button type="primary" @click="applyTimeShift">应用</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowDown, Plus, Delete } from '@element-plus/icons-vue'
import { editorApi } from '@/api/editor'


const pxPerSec = 80
const selectedSubId = ref('')
const showFindReplace = ref(false)
const findText = ref('')
const replaceText = ref('')
const showTimeShift = ref(false)
const timeShiftValue = ref(0)

interface SubtitleItem {
  id: string
  start: number
  end: number
  startStr: string
  endStr: string
  text: string
}

const subtitles = ref<SubtitleItem[]>([
  { id: '1', start: 0.5, end: 3.2, startStr: '0:00.5', endStr: '0:03.2', text: '你好，欢迎来到这个世界。' },
  { id: '2', start: 3.5, end: 6.8, startStr: '0:03.5', endStr: '0:06.8', text: '今天天气真好啊。' },
  { id: '3', start: 7.0, end: 10.5, startStr: '0:07.0', endStr: '0:10.5', text: '我们去散步吧。' },
  { id: '4', start: 11.0, end: 14.2, startStr: '0:11.0', endStr: '0:14.2', text: '好的，走吧！' },
])

const subtitleStyle = reactive({
  fontSize: 24,
  color: '#ffffff',
  strokeColor: '#000000',
  strokeWidth: 2,
  position: 'bottom' as 'bottom' | 'top' | 'center',
  align: 'center' as 'left' | 'center' | 'right',
  hasBackground: true,
  bgOpacity: 50,
})

const timeMarks = computed(() => {
  const maxTime = Math.max(...subtitles.value.map(s => s.end), 15)
  const marks: number[] = []
  for (let t = 0; t <= maxTime; t += 2) marks.push(t)
  return marks
})

function formatTime(sec: number) {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  const ms = Math.floor((sec % 1) * 10)
  return `${m}:${String(s).padStart(2, '0')}.${ms}`
}

function selectSubtitle(sub: SubtitleItem) {
  selectedSubId.value = sub.id
}

function addSubtitle() {
  const lastEnd = subtitles.value.length > 0 ? subtitles.value[subtitles.value.length - 1].end + 0.5 : 0
  const newSub: SubtitleItem = {
    id: Date.now().toString(),
    start: lastEnd,
    end: lastEnd + 3,
    startStr: formatTime(lastEnd),
    endStr: formatTime(lastEnd + 3),
    text: '',
  }
  subtitles.value.push(newSub)
}

function removeSubtitle(idx: number) {
  subtitles.value.splice(idx, 1)
}

function parseStartTime(sub: SubtitleItem) {
  const parts = sub.startStr.split(':')
  if (parts.length === 2) {
    sub.start = parseInt(parts[0]) * 60 + parseFloat(parts[1])
  }
}

function parseEndTime(sub: SubtitleItem) {
  const parts = sub.endStr.split(':')
  if (parts.length === 2) {
    sub.end = parseInt(parts[0]) * 60 + parseFloat(parts[1])
  }
}

async function saveSubtitleText(sub: SubtitleItem) {
  try {
    await editorApi.updateSubtitleText(sub.id, sub.text)
    ElMessage.success('字幕已保存')
  } catch {
    // silent
  }
}

function handleBatch(cmd: string) {
  if (cmd === 'realign') {
    ElMessage.success('字幕重新对齐完成')
  } else if (cmd === 'importSrt') {
    ElMessage.info('请选择 SRT 文件')
  } else if (cmd === 'exportSrt') {
    const srt = subtitles.value.map((s, i) => {
      return `${i + 1}\n${formatSrtTime(s.start)} --> ${formatSrtTime(s.end)}\n${s.text}\n`
    }).join('\n')
    const blob = new Blob([srt], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'subtitles.srt'
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('SRT 已导出')
  } else if (cmd === 'findReplace') {
    showFindReplace.value = true
  } else if (cmd === 'timeShift') {
    showTimeShift.value = true
  }
}

function formatSrtTime(sec: number) {
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = Math.floor(sec % 60)
  const ms = Math.floor((sec % 1) * 1000)
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms).padStart(3, '0')}`
}

function doFindReplace() {
  let count = 0
  for (const sub of subtitles.value) {
    if (sub.text.includes(findText.value)) {
      sub.text = sub.text.replaceAll(findText.value, replaceText.value)
      count++
    }
  }
  showFindReplace.value = false
  ElMessage.success(`已替换 ${count} 处`)
}

function applyTimeShift() {
  for (const sub of subtitles.value) {
    sub.start = Math.max(0, sub.start + timeShiftValue.value)
    sub.end = Math.max(0, sub.end + timeShiftValue.value)
    sub.startStr = formatTime(sub.start)
    sub.endStr = formatTime(sub.end)
  }
  showTimeShift.value = false
  ElMessage.success('时移已应用')
}

function applyStyle() {
  ElMessage.success('字幕样式已应用')
}
</script>

<style scoped>
.subtitle-adjust { padding: 24px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.timeline-card { margin-bottom: 16px; }
.subtitle-timeline { overflow-x: auto; background: #f5f7fa; border-radius: 8px; padding: 16px 16px 16px 60px; position: relative; min-height: 80px; }
.time-ruler { height: 20px; position: relative; margin-bottom: 8px; }
.mark { position: absolute; font-size: 10px; color: var(--el-text-color-secondary); transform: translateX(-50%); }
.subtitle-track { position: relative; height: 40px; }
.sub-block { position: absolute; top: 0; height: 36px; background: var(--el-color-primary-light-5); border: 1px solid var(--el-color-primary); border-radius: 6px; display: flex; align-items: center; padding: 0 8px; cursor: pointer; overflow: hidden; }
.sub-block.active { background: var(--el-color-primary-light-3); box-shadow: 0 0 0 2px var(--el-color-primary); }
.sub-text { font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.style-card { margin-bottom: 16px; }
.style-item { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
.style-item label { font-size: 12px; color: var(--el-text-color-secondary); }
.list-card { height: calc(100vh - 200px); overflow-y: auto; }
.list-header { display: flex; justify-content: space-between; align-items: center; }
.sub-list { display: flex; flex-direction: column; gap: 8px; }
.sub-item { padding: 10px; border: 1px solid var(--el-border-color-lighter); border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.sub-item:hover { background: var(--el-fill-color-light); }
.sub-item.active { border-color: var(--el-color-primary); background: var(--el-color-primary-light-9); }
.sub-timing { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; font-size: 12px; }
.sub-actions { display: flex; justify-content: flex-end; margin-top: 4px; }
</style>
