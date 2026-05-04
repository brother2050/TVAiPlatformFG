<template>
  <div class="text-editor">
    <div class="editor-toolbar">
      <el-select v-model="selectedEmotion" size="small" placeholder="情绪" style="width: 100px">
        <el-option label="开心" value="happy" />
        <el-option label="悲伤" value="sad" />
        <el-option label="愤怒" value="angry" />
        <el-option label="恐惧" value="fearful" />
        <el-option label="惊讶" value="surprised" />
        <el-option label="平静" value="calm" />
        <el-option label="低语" value="whisper" />
      </el-select>
      <el-select v-model="selectedVolume" size="small" placeholder="音量" style="width: 90px">
        <el-option label="低语" value="whisper" />
        <el-option label="正常" value="normal" />
        <el-option label="大声" value="loud" />
        <el-option label="喊叫" value="shout" />
      </el-select>
      <el-select v-model="selectedPace" size="small" placeholder="语速" style="width: 80px">
        <el-option label="慢" value="slow" />
        <el-option label="正常" value="normal" />
        <el-option label="快" value="fast" />
      </el-select>
    </div>
    <el-input
      v-model="localText"
      type="textarea"
      :rows="4"
      placeholder="输入台词..."
      @blur="handleSave"
    />
    <div class="editor-footer">
      <el-button size="small" type="primary" @click="handleSave">保存</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  text: string
  emotion?: string
  volume?: string
  pace?: string
}>()

const emit = defineEmits<{
  (e: 'save', data: { text: string; emotion: string; volume: string; pace: string }): void
}>()

const localText = ref(props.text)
const selectedEmotion = ref(props.emotion || 'calm')
const selectedVolume = ref(props.volume || 'normal')
const selectedPace = ref(props.pace || 'normal')

watch(() => props.text, (v) => { localText.value = v })

function handleSave() {
  emit('save', {
    text: localText.value,
    emotion: selectedEmotion.value,
    volume: selectedVolume.value,
    pace: selectedPace.value,
  })
}
</script>

<style lang="scss" scoped>
.text-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.editor-toolbar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.editor-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
