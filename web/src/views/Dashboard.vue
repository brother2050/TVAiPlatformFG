<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <h1>我的短剧</h1>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索项目名称…"
          prefix-icon="Search"
          clearable
          class="search-input"
        />
        <el-select v-model="filterStatus" placeholder="状态筛选" clearable class="filter-select">
          <el-option label="草稿" value="draft" />
          <el-option label="生成中" value="generating" />
          <el-option label="已完成" value="completed" />
        </el-select>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon> 创建项目
        </el-button>
      </div>
    </header>

    <div v-if="projectStore.loading" class="loading-container">
      <el-skeleton :rows="4" animated />
    </div>

    <div v-else-if="filteredProjects.length === 0" class="empty-state">
      <el-empty description="还没有项目，点击上方按钮创建第一个短剧吧！">
        <el-button type="primary" @click="showCreateDialog = true">创建项目</el-button>
      </el-empty>
    </div>

    <div v-else class="project-grid">
      <el-card
        v-for="project in filteredProjects"
        :key="project.id"
        class="project-card"
        shadow="hover"
        @click="openProject(project)"
      >
        <div class="card-cover">
          <div class="cover-placeholder">
            <el-icon :size="48"><Film /></el-icon>
          </div>
          <el-tag :type="statusTagType(project.status)" class="status-tag">
            {{ statusLabel(project.status) }}
          </el-tag>
        </div>
        <div class="card-body">
          <h3 class="project-title">{{ project.title }}</h3>
          <div class="project-meta">
            <span>{{ project.genre }}</span>
            <el-divider direction="vertical" />
            <span>{{ project.style }}</span>
            <el-divider direction="vertical" />
            <span>{{ project.total_episodes }}集</span>
          </div>
          <el-progress
            :percentage="computeProgress(project)"
            :status="project.status === 'completed' ? 'success' : undefined"
            :stroke-width="8"
          />
        </div>
        <div class="card-actions" @click.stop>
          <el-button text size="small" @click="editProject(project)">编辑</el-button>
          <el-button text size="small" @click="duplicateProject(project)">复制</el-button>
          <el-popconfirm title="确定删除该项目？" @confirm="deleteProject(project.id)">
            <template #reference>
              <el-button text size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑项目弹窗 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingProject ? '编辑项目' : '创建项目'"
      width="560px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="项目名称" prop="title">
          <el-input v-model="form.title" placeholder="输入短剧名称" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="题材" prop="genre">
          <el-select v-model="form.genre" placeholder="选择或自定义题材" filterable allow-create>
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
        <el-form-item label="画风" prop="style">
          <el-select v-model="form.style" placeholder="选择或自定义画风" filterable allow-create>
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
        <el-form-item label="集数" prop="total_episodes">
          <el-input-number v-model="form.total_episodes" :min="1" :max="200" />
        </el-form-item>
        <el-form-item label="时长(秒)" prop="episode_duration_sec">
          <el-input-number v-model="form.episode_duration_sec" :min="30" :max="600" :step="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ editingProject ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Film } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useProjectStore } from '@/stores/project'
import type { Project, CreateProjectDto } from '@/api'

const router = useRouter()
const projectStore = useProjectStore()

const searchQuery = ref('')
const filterStatus = ref('')
const showCreateDialog = ref(false)
const editingProject = ref<Project | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive<CreateProjectDto>({
  title: '',
  genre: '',
  style: '',
  total_episodes: 10,
  episode_duration_sec: 120,
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  genre: [{ required: true, message: '请选择题材', trigger: 'change' }],
  style: [{ required: true, message: '请选择画风', trigger: 'change' }],
}

const filteredProjects = computed(() => {
  let list = projectStore.projects
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(p => p.title.toLowerCase().includes(q))
  }
  if (filterStatus.value) {
    list = list.filter(p => p.status === filterStatus.value)
  }
  return list
})

function statusTagType(status: string) {
  const map: Record<string, string> = { draft: 'info', generating: 'warning', completed: 'success' }
  return map[status] || 'info'
}

function statusLabel(status: string) {
  const map: Record<string, string> = { draft: '草稿', generating: '生成中', completed: '已完成' }
  return map[status] || status
}

function computeProgress(project: Project): number {
  if (project.status === 'completed') return 100
  if (project.status === 'generating') return 50
  return 10
}

function openProject(project: Project) {
  router.push({ name: 'Characters', params: { id: project.id } })
}

function editProject(project: Project) {
  editingProject.value = project
  form.title = project.title
  form.genre = project.genre
  form.style = project.style
  form.total_episodes = project.total_episodes
  form.episode_duration_sec = project.episode_duration_sec
  showCreateDialog.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (editingProject.value) {
      await projectStore.updateProject(editingProject.value.id, { ...form })
      ElMessage.success('项目已更新')
    } else {
      await projectStore.createProject({ ...form })
      ElMessage.success('项目已创建')
    }
    showCreateDialog.value = false
    resetForm()
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function duplicateProject(project: Project) {
  try {
    await projectStore.duplicateProject(project.id)
    ElMessage.success('项目已复制')
  } catch (e: any) {
    ElMessage.error(e.message || '复制失败')
  }
}

async function deleteProject(id: string) {
  try {
    await projectStore.deleteProject(id)
    ElMessage.success('项目已删除')
  } catch (e: any) {
    ElMessage.error(e.message || '删除失败')
  }
}

function resetForm() {
  editingProject.value = null
  form.title = ''
  form.genre = ''
  form.style = ''
  form.total_episodes = 10
  form.episode_duration_sec = 120
}

// 加载数据
projectStore.fetchProjects()
</script>

<style scoped>
.dashboard {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}
.dashboard-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}
.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
.search-input {
  width: 240px;
}
.filter-select {
  width: 140px;
}
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}
.project-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.project-card:hover {
  transform: translateY(-2px);
}
.card-cover {
  position: relative;
  height: 160px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px 8px 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255,255,255,0.6);
}
.status-tag {
  position: absolute;
  top: 8px;
  right: 8px;
}
.card-body {
  padding: 16px 0 8px;
}
.project-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.project-meta {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}
.card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
}
.loading-container {
  padding: 40px;
}
.empty-state {
  padding: 80px 0;
}
</style>
