import http, {
  type ApiResponse,
  type Dialogue,
  type DialogueDto,
  type EmotionParams,
  type VoiceParams,
  type TimingDto,
} from './index'

// BGM 相关类型
export interface BgmItem {
  id: string
  name: string
  description: string
  url: string
}

export interface SfxItem {
  id: string
  name: string
  type: string
  volume: number
  url: string
}

export interface MixLevels {
  bgm: number
  voice: number
  ambient: number
  sfx: number
}

export interface BgmData {
  bgm: BgmItem | null
  sfx: SfxItem[]
  mixLevels: MixLevels
}

export const editorApi = {
  // 文本编辑
  updateDialogueText: (id: string, text: string) =>
    http.put<ApiResponse<void>>(`/editor/dialogues/${id}/text`, { text }),
  updateDialogueEmotion: (id: string, data: EmotionParams) =>
    http.put<ApiResponse<void>>(`/editor/dialogues/${id}/emotion`, data),
  insertDialogue: (sceneId: string, data: DialogueDto) =>
    http.post<ApiResponse<Dialogue>>(`/editor/dialogues`, { scene_id: sceneId, ...data }),
  deleteDialogue: (id: string) =>
    http.delete<ApiResponse<void>>(`/editor/dialogues/${id}`),

  // 图片编辑
  regenerateImage: (id: string) =>
    http.post<ApiResponse<string>>(`/editor/images/${id}/regenerate`),
  inpaintImage: (id: string, mask: File, prompt: string) => {
    const form = new FormData()
    form.append('mask', mask)
    form.append('prompt', prompt)
    return http.post<ApiResponse<string>>(`/editor/images/${id}/inpaint`, form)
  },
  uploadReplaceImage: (id: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return http.post<ApiResponse<string>>(`/editor/images/${id}/upload-replace`, form)
  },

  // 语音编辑
  regenerateVoice: (id: string) =>
    http.post<ApiResponse<string>>(`/editor/voices/${id}/regenerate`),
  updateVoiceParams: (id: string, params: VoiceParams) =>
    http.put<ApiResponse<void>>(`/editor/voices/${id}/params`, params),

  // 字幕编辑
  updateSubtitleText: (id: string, text: string) =>
    http.put<ApiResponse<void>>(`/editor/subtitles/${id}/text`, { text }),
  updateSubtitleTiming: (id: string, timing: TimingDto) =>
    http.put<ApiResponse<void>>(`/editor/subtitles/${id}/timing`, timing),

  // 视频编辑
  trimVideo: (id: string, start: number, end: number) =>
    http.put<ApiResponse<void>>(`/editor/videos/${id}/trim`, { start, end }),
  updateTransition: (id: string, transition: string) =>
    http.put<ApiResponse<void>>(`/editor/videos/${id}/transition`, { transition }),

  // BGM / 环境音
  getBgmData: (episodeId: string) =>
    http.get<ApiResponse<BgmData>>(`/editor/episodes/${episodeId}/bgm`),
  updateBgm: (episodeId: string, data: Record<string, any>) =>
    http.put<ApiResponse<void>>(`/editor/episodes/${episodeId}/bgm`, data),
  generateBgm: (episodeId: string, data: { description: string }) =>
    http.post<ApiResponse<{ status: string; bgm: BgmItem }>>(`/editor/episodes/${episodeId}/bgm/generate`, data),
  uploadBgm: (episodeId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return http.post<ApiResponse<{ id: string; url: string }>>(`/editor/episodes/${episodeId}/bgm/upload`, form)
  },

  // 环境音/音效
  uploadSfx: (episodeId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return http.post<ApiResponse<{ id: string; url: string }>>(`/editor/episodes/${episodeId}/sfx/upload`, form)
  },
  deleteSfx: (episodeId: string, sfxId: string) =>
    http.delete<ApiResponse<void>>(`/editor/episodes/${episodeId}/sfx/${sfxId}`),
  addSfxFromLibrary: (episodeId: string, data: { name: string; category: string }) =>
    http.post<ApiResponse<{ id: string; url: string }>>(`/editor/episodes/${episodeId}/sfx/library`, data),

  // 混音设置
  updateMixLevels: (episodeId: string, levels: MixLevels) =>
    http.put<ApiResponse<void>>(`/editor/episodes/${episodeId}/mix`, levels),
}
