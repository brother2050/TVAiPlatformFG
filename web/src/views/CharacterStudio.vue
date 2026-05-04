<template>
  <div class="character-studio">
    <header class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <h1>角色设计</h1>
      </div>
      <el-button type="primary" @click="startCreate">
        <el-icon><Plus /></el-icon> 创建角色
      </el-button>
    </header>

    <el-row :gutter="24">
      <!-- 角色列表 -->
      <el-col :span="8">
        <el-card class="character-list-card">
          <template #header>
            <span>角色列表 ({{ characterStore.characters.length }})</span>
          </template>
          <div v-if="characterStore.loading" v-loading="true" style="min-height: 200px" />
          <div v-else-if="characterStore.characters.length === 0" class="empty-hint">
            <el-empty description="暂无角色" :image-size="80" />
          </div>
          <div v-else class="character-items">
            <div
              v-for="char in characterStore.characters"
              :key="char.id"
              class="character-item"
              :class="{ active: characterStore.currentCharacter?.id === char.id }"
              @click="selectCharacter(char)"
            >
              <el-avatar :size="40" class="char-avatar">
                {{ char.name.charAt(0) }}
              </el-avatar>
              <div class="char-info">
                <span class="char-name">{{ char.name }}</span>
                <span class="char-meta">{{ genderLabel(char.gender) }} · {{ char.body.body_type }}</span>
              </div>
              <el-dropdown trigger="click" @click.stop>
                <el-icon><MoreFilled /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="editCharacter(char)">编辑</el-dropdown-item>
                    <el-dropdown-item @click="generateRef(char)">生成参考图</el-dropdown-item>
                    <el-dropdown-item divided @click="deleteCharacter(char.id)" style="color: var(--el-color-danger)">
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 角色详情 / 创建表单 -->
      <el-col :span="16">
        <!-- 创建/编辑引导流程 -->
        <el-card v-if="isEditing" class="edit-card">
          <template #header>
            <div class="edit-header">
              <span>{{ isCreating ? '创建角色' : '编辑角色' }}</span>
              <el-steps :active="currentStep" finish-status="success" simple>
                <el-step title="基本信息" />
                <el-step title="外貌" />
                <el-step title="体型" />
                <el-step title="服装" />
                <el-step title="音色" />
              </el-steps>
            </div>
          </template>

          <!-- Step 0: 基本信息 -->
          <div v-show="currentStep === 0" class="step-content">
            <el-form label-width="80px">
              <el-form-item label="角色名" required>
                <el-input v-model="editForm.name" placeholder="输入角色名称" />
              </el-form-item>
              <el-form-item label="性别" required>
                <el-radio-group v-model="editForm.gender">
                  <el-radio value="male">男</el-radio>
                  <el-radio value="female">女</el-radio>
                  <el-radio value="other">其他</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-form>
          </div>

          <!-- Step 1: 外貌 -->
          <div v-show="currentStep === 1" class="step-content">
            <el-form label-width="90px">
              <el-form-item label="脸型">
                <el-select v-model="editForm.appearance.face_shape" filterable allow-create>
                  <el-option label="鹅蛋脸" value="oval" />
                  <el-option label="圆脸" value="round" />
                  <el-option label="方脸" value="square" />
                  <el-option label="瓜子脸" value="heart" />
                  <el-option label="长脸" value="long" />
                </el-select>
              </el-form-item>
              <el-form-item label="瞳色">
                <el-input v-model="editForm.appearance.eye_color" placeholder="如：深棕色" />
              </el-form-item>
              <el-form-item label="发型">
                <el-input v-model="editForm.appearance.hair_style" placeholder="如：长直发、短卷发" />
              </el-form-item>
              <el-form-item label="发色">
                <el-input v-model="editForm.appearance.hair_color" placeholder="如：黑色、金色" />
              </el-form-item>
              <el-form-item label="肤色">
                <el-input v-model="editForm.appearance.skin_tone" placeholder="如：白皙、小麦色" />
              </el-form-item>
              <el-form-item label="特征">
                <el-select
                  v-model="editForm.appearance.distinctive_features"
                  multiple
                  filterable
                  allow-create
                  placeholder="添加特征标记"
                >
                  <el-option label="泪痣" value="泪痣" />
                  <el-option label="虎牙" value="虎牙" />
                  <el-option label="酒窝" value="酒窝" />
                  <el-option label="疤痕" value="疤痕" />
                </el-select>
              </el-form-item>
              <el-form-item label="表情倾向">
                <el-input v-model="editForm.appearance.expression_bias" placeholder="如：冷峻、温柔、活泼" />
              </el-form-item>
            </el-form>
          </div>

          <!-- Step 2: 体型 -->
          <div v-show="currentStep === 2" class="step-content">
            <el-form label-width="80px">
              <el-form-item label="身高(cm)">
                <el-slider v-model="editForm.body.height_cm" :min="140" :max="210" show-input />
              </el-form-item>
              <el-form-item label="体重(kg)">
                <el-slider v-model="editForm.body.weight_kg" :min="35" :max="120" show-input />
              </el-form-item>
              <el-form-item label="体型">
                <el-radio-group v-model="editForm.body.body_type">
                  <el-radio-button value="slim">纤细</el-radio-button>
                  <el-radio-button value="athletic">健美</el-radio-button>
                  <el-radio-button value="average">标准</el-radio-button>
                  <el-radio-button value="stocky">壮实</el-radio-button>
                  <el-radio-button value="curvy">丰满</el-radio-button>
                </el-radio-group>
              </el-form-item>
            </el-form>
          </div>

          <!-- Step 3: 服装 -->
          <div v-show="currentStep === 3" class="step-content">
            <el-form label-width="80px">
              <el-form-item label="上装">
                <el-input v-model="editForm.wardrobe_default.top" placeholder="如：白色衬衫、黑色卫衣" />
              </el-form-item>
              <el-form-item label="下装">
                <el-input v-model="editForm.wardrobe_default.bottom" placeholder="如：牛仔裤、长裙" />
              </el-form-item>
              <el-form-item label="鞋子">
                <el-input v-model="editForm.wardrobe_default.shoes" placeholder="如：白色运动鞋" />
              </el-form-item>
              <el-form-item label="配色">
                <el-select
                  v-model="editForm.wardrobe_default.color_palette"
                  multiple
                  filterable
                  allow-create
                  placeholder="添加颜色"
                >
                  <el-option label="白色" value="white" />
                  <el-option label="黑色" value="black" />
                  <el-option label="红色" value="red" />
                  <el-option label="蓝色" value="blue" />
                  <el-option label="灰色" value="gray" />
                  <el-option label="米色" value="beige" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>

          <!-- Step 4: 音色 -->
          <div v-show="currentStep === 4" class="step-content">
            <el-form label-width="80px">
              <el-form-item label="音色">
                <el-select v-model="editForm.voice.tone" filterable allow-create>
                  <el-option label="温柔" value="gentle" />
                  <el-option label="磁性" value="magnetic" />
                  <el-option label="清亮" value="bright" />
                  <el-option label="沙哑" value="husky" />
                  <el-option label="甜美" value="sweet" />
                  <el-option label="低沉" value="deep" />
                </el-select>
              </el-form-item>
              <el-form-item label="语速">
                <el-radio-group v-model="editForm.voice.speed">
                  <el-radio value="slow">慢</el-radio>
                  <el-radio value="normal">正常</el-radio>
                  <el-radio value="fast">快</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="音调">
                <el-select v-model="editForm.voice.pitch" filterable allow-create>
                  <el-option label="低音" value="low" />
                  <el-option label="中音" value="medium" />
                  <el-option label="高音" value="high" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>

          <div class="step-actions">
            <el-button v-if="currentStep > 0" @click="currentStep--">上一步</el-button>
            <el-button v-if="currentStep < 4" type="primary" @click="currentStep++">下一步</el-button>
            <el-button v-if="currentStep === 4" type="primary" :loading="saving" @click="saveCharacter">
              {{ isCreating ? '创建角色' : '保存修改' }}
            </el-button>
            <el-button @click="cancelEdit">取消</el-button>
          </div>
        </el-card>

        <!-- 角色详情展示 -->
        <el-card v-else-if="characterStore.currentCharacter" class="detail-card">
          <template #header>
            <div class="detail-header">
              <span>角色详情</span>
              <div>
                <el-button size="small" @click="editCharacter(characterStore.currentCharacter!)">编辑</el-button>
                <el-button size="small" type="primary" @click="generateRef(characterStore.currentCharacter!)">
                  生成参考图
                </el-button>
              </div>
            </div>
          </template>
          <div class="profile-card">
            <div class="profile-avatar">
              <el-avatar :size="80">{{ characterStore.currentCharacter.name.charAt(0) }}</el-avatar>
            </div>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="姓名">{{ characterStore.currentCharacter.name }}</el-descriptions-item>
              <el-descriptions-item label="性别">{{ genderLabel(characterStore.currentCharacter.gender) }}</el-descriptions-item>
              <el-descriptions-item label="脸型">{{ characterStore.currentCharacter.appearance.face_shape }}</el-descriptions-item>
              <el-descriptions-item label="瞳色">{{ characterStore.currentCharacter.appearance.eye_color }}</el-descriptions-item>
              <el-descriptions-item label="发型">{{ characterStore.currentCharacter.appearance.hair_style }}</el-descriptions-item>
              <el-descriptions-item label="发色">{{ characterStore.currentCharacter.appearance.hair_color }}</el-descriptions-item>
              <el-descriptions-item label="肤色">{{ characterStore.currentCharacter.appearance.skin_tone }}</el-descriptions-item>
              <el-descriptions-item label="表情倾向">{{ characterStore.currentCharacter.appearance.expression_bias }}</el-descriptions-item>
              <el-descriptions-item label="特征" :span="2">
                <el-tag v-for="f in characterStore.currentCharacter.appearance.distinctive_features" :key="f" class="mr-1">{{ f }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="身高">{{ characterStore.currentCharacter.body.height_cm }}cm</el-descriptions-item>
              <el-descriptions-item label="体重">{{ characterStore.currentCharacter.body.weight_kg }}kg</el-descriptions-item>
              <el-descriptions-item label="体型">{{ characterStore.currentCharacter.body.body_type }}</el-descriptions-item>
              <el-descriptions-item label="音色">{{ characterStore.currentCharacter.voice.tone }}</el-descriptions-item>
              <el-descriptions-item label="上装">{{ characterStore.currentCharacter.wardrobe_default.top }}</el-descriptions-item>
              <el-descriptions-item label="下装">{{ characterStore.currentCharacter.wardrobe_default.bottom }}</el-descriptions-item>
              <el-descriptions-item label="鞋子">{{ characterStore.currentCharacter.wardrobe_default.shoes }}</el-descriptions-item>
              <el-descriptions-item label="配色" :span="2">
                <el-tag v-for="c in characterStore.currentCharacter.wardrobe_default.color_palette" :key="c" class="mr-1">{{ c }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>

            <!-- 参考图展示 -->
            <div v-if="Object.keys(characterStore.currentCharacter.reference_images).length > 0" class="ref-images">
              <h4>参考图</h4>
              <div class="ref-grid">
                <el-image
                  v-for="(path, view) in characterStore.currentCharacter.reference_images"
                  :key="view"
                  :src="path"
                  :preview-src-list="Object.values(characterStore.currentCharacter.reference_images)"
                  fit="cover"
                  class="ref-img"
                >
                  <template #error>
                    <div class="img-error"><el-icon><Picture /></el-icon></div>
                  </template>
                </el-image>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 无选中状态 -->
        <el-card v-else class="detail-card">
          <el-empty description="选择左侧角色查看详情" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus, MoreFilled, Picture } from '@element-plus/icons-vue'
import { useCharacterStore } from '@/stores/character'
import type { Character, AppearanceSpec, BodySpec, VoiceSpec, WardrobeSpec } from '@/api'

interface CharacterForm {
  name: string
  gender: 'male' | 'female' | 'other'
  appearance: AppearanceSpec
  body: BodySpec
  voice: VoiceSpec
  wardrobe_default: WardrobeSpec
}

const route = useRoute()
const projectId = route.params.id as string
const characterStore = useCharacterStore()

const isEditing = ref(false)
const isCreating = ref(false)
const currentStep = ref(0)
const saving = ref(false)
const editingId = ref<string | null>(null)

const editForm = reactive<CharacterForm>({
  name: '',
  gender: 'female',
  appearance: {
    face_shape: '',
    eye_color: '',
    hair_style: '',
    hair_color: '',
    skin_tone: '',
    distinctive_features: [],
    expression_bias: '',
  },
  body: { height_cm: 170, weight_kg: 60, body_type: 'average' },
  voice: { tone: '', speed: 'normal', pitch: 'medium' },
  wardrobe_default: { top: '', bottom: '', shoes: '', color_palette: [] },
})

function genderLabel(g: string) {
  const map: Record<string, string> = { male: '男', female: '女', other: '其他' }
  return map[g] || g
}

function selectCharacter(char: Character) {
  characterStore.currentCharacter = char
}

function startCreate() {
  isCreating.value = true
  isEditing.value = true
  currentStep.value = 0
  editingId.value = null
  resetForm()
}

function editCharacter(char: Character) {
  isCreating.value = false
  isEditing.value = true
  currentStep.value = 0
  editingId.value = char.id
  editForm.name = char.name
  editForm.gender = char.gender
  editForm.appearance = { ...char.appearance, distinctive_features: [...char.appearance.distinctive_features] }
  editForm.body = { ...char.body }
  editForm.voice = { ...char.voice }
  editForm.wardrobe_default = { ...char.wardrobe_default, color_palette: [...char.wardrobe_default.color_palette] }
}

function cancelEdit() {
  isEditing.value = false
  isCreating.value = false
  editingId.value = null
}

function resetForm() {
  editForm.name = ''
  editForm.gender = 'female'
  editForm.appearance = {
    face_shape: '', eye_color: '', hair_style: '', hair_color: '',
    skin_tone: '', distinctive_features: [], expression_bias: '',
  }
  editForm.body = { height_cm: 170, weight_kg: 60, body_type: 'average' }
  editForm.voice = { tone: '', speed: 'normal', pitch: 'medium' }
  editForm.wardrobe_default = { top: '', bottom: '', shoes: '', color_palette: [] }
}

async function saveCharacter() {
  if (!editForm.name.trim()) {
    ElMessage.warning('请输入角色名称')
    currentStep.value = 0
    return
  }
  saving.value = true
  try {
    if (isCreating.value) {
      await characterStore.createCharacter(projectId, { ...editForm })
      ElMessage.success('角色创建成功')
    } else if (editingId.value) {
      await characterStore.updateCharacter(editingId.value, { ...editForm })
      ElMessage.success('角色已更新')
    }
    isEditing.value = false
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function deleteCharacter(id: string) {
  try {
    await ElMessageBox.confirm('确定删除此角色？', '提示', { type: 'warning' })
    await characterStore.deleteCharacter(id)
    ElMessage.success('角色已删除')
  } catch { /* cancelled */ }
}

async function generateRef(char: Character) {
  try {
    await characterStore.generateReferenceSheet(char.id)
    ElMessage.success('参考图生成任务已提交')
  } catch (e: any) {
    ElMessage.error(e.message || '生成失败')
  }
}

characterStore.fetchCharacters(projectId)
</script>

<style scoped>
.character-studio { padding: 24px; max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-left h1 { margin: 0; font-size: 22px; }
.character-list-card { height: calc(100vh - 160px); overflow-y: auto; }
.character-items { display: flex; flex-direction: column; gap: 8px; }
.character-item { display: flex; align-items: center; gap: 12px; padding: 10px; border-radius: 8px; cursor: pointer; transition: background 0.2s; }
.character-item:hover { background: var(--el-fill-color-light); }
.character-item.active { background: var(--el-color-primary-light-9); border: 1px solid var(--el-color-primary-light-5); }
.char-avatar { flex-shrink: 0; background: var(--el-color-primary); color: #fff; }
.char-info { flex: 1; min-width: 0; }
.char-name { display: block; font-weight: 600; font-size: 14px; }
.char-meta { font-size: 12px; color: var(--el-text-color-secondary); }
.edit-header { display: flex; flex-direction: column; gap: 12px; }
.step-content { min-height: 300px; padding: 16px 0; }
.step-actions { display: flex; gap: 8px; padding-top: 16px; border-top: 1px solid var(--el-border-color-lighter); }
.detail-header { display: flex; justify-content: space-between; align-items: center; }
.profile-card { display: flex; flex-direction: column; gap: 20px; }
.profile-avatar { display: flex; justify-content: center; }
.profile-avatar .el-avatar { font-size: 32px; background: var(--el-color-primary); color: #fff; }
.ref-images h4 { margin: 16px 0 8px; }
.ref-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 8px; }
.ref-img { width: 100%; height: 120px; border-radius: 8px; }
.img-error { display: flex; align-items: center; justify-content: center; height: 100%; background: var(--el-fill-color-light); color: var(--el-text-color-placeholder); }
.mr-1 { margin-right: 4px; margin-bottom: 4px; }
</style>
