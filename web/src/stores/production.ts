import { defineStore } from 'pinia'
import { ref } from 'vue'
import { productionApi, type ProductionStage } from '@/api/production'
import type { ProductionTask, ProductionProgress } from '@/api/index'

export const useProductionStore = defineStore('production', () => {
  const tasks = ref<ProductionTask[]>([])
  const progress = ref<Record<string, number>>({})
  const currentStage = ref('')

  async function fetchTasks(episodeId: string) {
    const res = await productionApi.getProgress(episodeId)
    const data = res.data.data as ProductionProgress
    tasks.value = data.stages.map((s) => ({
      id: `${episodeId}-${s.stage}`,
      episode_id: episodeId,
      stage: s.stage as any,
      status: s.status as any,
      assets: {},
      review_notes: '',
      created_at: '',
      updated_at: '',
    }))
    data.stages.forEach((s) => {
      progress.value[s.stage] = s.progress
    })
  }

  async function startProduction(episodeId: string) {
    currentStage.value = 'keyframes'
    await productionApi.produce(episodeId)
  }

  // 批量生产指定阶段
  async function batchProduceStages(episodeId: string, stages: ProductionStage[]) {
    const res = await productionApi.batchProduce(episodeId, stages)
    return res.data
  }

  async function getProgress(episodeId: string) {
    const res = await productionApi.getProgress(episodeId)
    const data = res.data.data
    data.stages.forEach((s) => {
      progress.value[s.stage] = s.progress
    })
    return data
  }

  return { tasks, progress, currentStage, fetchTasks, startProduction, batchProduceStages, getProgress }
})
