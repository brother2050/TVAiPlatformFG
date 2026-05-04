import { defineStore } from 'pinia'
import { ref } from 'vue'
import http, { type ApiResponse, type Scene, type Shot } from '@/api/index'

export const useTimelineStore = defineStore('timeline', () => {
  const scenes = ref<Scene[]>([])
  const currentScene = ref<Scene | null>(null)
  const currentShot = ref<Shot | null>(null)
  const playheadTime = ref(0)
  const playing = ref(false)

  async function fetchScenes(episodeId: string) {
    const res = await http.get<ApiResponse<Scene[]>>(`/episodes/${episodeId}/script`)
    scenes.value = res.data.data
  }

  function setCurrentScene(scene: Scene | null) {
    currentScene.value = scene
    currentShot.value = null
  }

  function setCurrentShot(shot: Shot | null) {
    currentShot.value = shot
  }

  function setPlayheadTime(time: number) {
    playheadTime.value = time
  }

  function togglePlaying() {
    playing.value = !playing.value
  }

  return { scenes, currentScene, currentShot, playheadTime, playing, fetchScenes, setCurrentScene, setCurrentShot, setPlayheadTime, togglePlaying }
})
