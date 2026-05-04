import http, { type ApiResponse, type ProductionProgress, type ProductionStage } from './index'

export { PRODUCTION_STAGES } from './index'
export type { ProductionStage } from './index'

export const productionApi = {
  // 单个生产
  produce: (episodeId: string) => http.post<ApiResponse<string>>(`/episodes/${episodeId}/produce`),
  // 批量生产（指定阶段）
  batchProduce: (episodeId: string, stages: ProductionStage[]) =>
    http.post<ApiResponse<{ status: string; stages: ProductionStage[]; episode_id: string }>>(
      `/episodes/${episodeId}/produce/batch`,
      { stages }
    ),
  // 获取进度
  getProgress: (episodeId: string) => http.get<ApiResponse<ProductionProgress>>(`/episodes/${episodeId}/progress`),
  // 重新生成关键帧
  regenerateKeyframe: (shotId: string) => http.post<ApiResponse<string>>(`/shots/${shotId}/regenerate-keyframe`),
  // 重新生成语音
  regenerateVoice: (dialogueId: string) => http.post<ApiResponse<string>>(`/dialogues/${dialogueId}/regenerate-voice`),
}
