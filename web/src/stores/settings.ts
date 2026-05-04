import { defineStore } from 'pinia'
import { ref } from 'vue'
import { settingsApi } from '@/api/settings'
import type { ProjectGlobalSettings, SceneOverride } from '@/api/index'

export const useSettingsStore = defineStore('settings', () => {
  const globalSettings = ref<ProjectGlobalSettings | null>(null)
  const sceneOverrides = ref<Record<string, SceneOverride>>({})

  async function fetchSettings(projectId: string) {
    const res = await settingsApi.get(projectId)
    globalSettings.value = res.data.data
    return res.data.data
  }

  async function updateSettings(projectId: string, data: ProjectGlobalSettings) {
    const res = await settingsApi.update(projectId, data)
    globalSettings.value = res.data.data
    return res.data.data
  }

  async function addDimension(projectId: string, key: string, value: string) {
    await settingsApi.addDimension(projectId, key, value)
    if (globalSettings.value) {
      globalSettings.value.custom_dimensions[key] = value
    }
  }

  async function removeDimension(projectId: string, key: string) {
    await settingsApi.removeDimension(projectId, key)
    if (globalSettings.value) {
      delete globalSettings.value.custom_dimensions[key]
    }
  }

  async function fetchSceneOverrides(projectId: string, sceneId: string) {
    const res = await settingsApi.getSceneOverrides(projectId, sceneId)
    sceneOverrides.value[sceneId] = res.data.data
  }

  async function updateSceneOverrides(projectId: string, sceneId: string, data: SceneOverride) {
    const res = await settingsApi.updateSceneOverrides(projectId, sceneId, data)
    sceneOverrides.value[sceneId] = res.data.data
    return res.data.data
  }

  return {
    globalSettings,
    sceneOverrides,
    fetchSettings,
    updateSettings,
    addDimension,
    removeDimension,
    fetchSceneOverrides,
    updateSceneOverrides,
  }
})
