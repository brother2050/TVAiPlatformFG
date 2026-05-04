<template>
  <el-card class="scene-override-panel" shadow="hover">
    <template #header>
      <span>场景覆盖设置</span>
    </template>

    <el-form :model="form" label-width="80px" size="small">
      <el-form-item label="色调">
        <el-input v-model="form.color_palette" placeholder="覆盖全局色调" />
      </el-form-item>
      <el-form-item label="氛围">
        <el-input v-model="form.mood" placeholder="覆盖场景氛围" />
      </el-form-item>
      <el-form-item label="额外提示">
        <el-input
          v-model="form.extra_prompt"
          type="textarea"
          :rows="2"
          placeholder="添加到此场景的额外 AI 提示词"
        />
      </el-form-item>

      <el-divider>自定义覆盖</el-divider>
      <div v-for="(val, key) in form.custom_overrides" :key="key" class="override-row">
        <span class="override-key">{{ key }}</span>
        <el-input :model-value="val" size="small" @update:model-value="(v: string) => updateOverride(key as string, v)" />
        <el-button size="small" type="danger" plain @click="removeOverride(key as string)">删</el-button>
      </div>

      <div class="add-override-row">
        <el-input v-model="newOverrideKey" size="small" placeholder="键" style="width: 100px" />
        <el-input v-model="newOverrideValue" size="small" placeholder="值" style="width: 150px" />
        <el-button size="small" :disabled="!newOverrideKey" @click="addOverride">添加</el-button>
      </div>
    </el-form>

    <div class="panel-footer">
      <el-button size="small" type="primary" @click="handleSave">保存覆盖</el-button>
      <el-button size="small" @click="handleReset">恢复默认</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import type { SceneOverride } from '@/api/index'

const props = defineProps<{
  override: SceneOverride
}>()

const emit = defineEmits<{
  (e: 'save', data: SceneOverride): void
  (e: 'reset'): void
}>()

const form = reactive<SceneOverride>({
  scene_id: '',
  color_palette: '',
  mood: '',
  extra_prompt: '',
  custom_overrides: {},
})

const newOverrideKey = ref('')
const newOverrideValue = ref('')

watch(() => props.override, (o) => {
  if (!o) return
  Object.assign(form, o)
}, { immediate: true })

function updateOverride(key: string, value: string) {
  form.custom_overrides[key] = value
}

function removeOverride(key: string) {
  delete form.custom_overrides[key]
}

function addOverride() {
  form.custom_overrides[newOverrideKey.value] = newOverrideValue.value
  newOverrideKey.value = ''
  newOverrideValue.value = ''
}

function handleSave() {
  emit('save', { ...form, custom_overrides: { ...form.custom_overrides } })
}

function handleReset() {
  emit('reset')
}
</script>

<style lang="scss" scoped>
.scene-override-panel {
  max-width: 400px;
}

.override-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.override-key {
  min-width: 80px;
  font-size: 13px;
  color: #606266;
}

.add-override-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
}

.panel-footer {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}
</style>
