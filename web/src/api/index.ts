import axios from 'axios'

// ─── HTTP Client ────────────────────────────────────────────
const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.request.use(
  (config) => {
    // 可在此附加 token
    return config
  },
  (error) => Promise.reject(error),
)

http.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data.code !== undefined && data.code !== 0) {
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    return response
  },
  (error) => {
    const message = error.response?.data?.message || error.message || '网络错误'
    return Promise.reject(new Error(message))
  },
)

export default http

// ─── Shared Types ───────────────────────────────────────────

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface Project {
  id: string
  title: string
  genre: string
  style: string
  total_episodes: number
  episode_duration_sec: number
  global_settings: ProjectGlobalSettings
  status: 'draft' | 'generating' | 'completed'
  created_at: string
  updated_at: string
}

export interface CreateProjectDto {
  title: string
  genre: string
  style: string
  total_episodes?: number
  episode_duration_sec?: number
}

export interface ProjectGlobalSettings {
  art_style: string
  color_palette: string
  narrative_pace: string
  target_audience: string
  overall_mood: string
  music_style: string
  subtitle_style: string
  custom_dimensions: Record<string, string>
  global_prompt_prefix: string
}

export interface Character {
  id: string
  project_id: string
  name: string
  gender: 'male' | 'female' | 'other'
  appearance: AppearanceSpec
  body: BodySpec
  voice: VoiceSpec
  wardrobe_default: WardrobeSpec
  reference_images: Record<string, string>
  consistency_seed: number
  face_embedding: number[]
  created_at: string
  updated_at: string
}

export interface CreateCharacterDto {
  name: string
  gender: 'male' | 'female' | 'other'
  appearance?: Partial<AppearanceSpec>
  body?: Partial<BodySpec>
  voice?: Partial<VoiceSpec>
  wardrobe_default?: Partial<WardrobeSpec>
}

export interface AppearanceSpec {
  face_shape: string
  eye_color: string
  hair_style: string
  hair_color: string
  skin_tone: string
  distinctive_features: string[]
  expression_bias: string
}

export interface BodySpec {
  height_cm: number
  weight_kg: number
  body_type: string
}

export interface VoiceSpec {
  tone: string
  speed: string
  pitch: string
}

export interface WardrobeSpec {
  top: string
  bottom: string
  shoes: string
  color_palette: string[]
}

export interface Scene {
  id: string
  episode_id: string
  scene_number: number
  location: string
  time_of_day: string
  weather: string
  atmosphere: string
  characters_present: string[]
  shots: Shot[]
  background_music: string
  ambient_sound: string
  scene_overrides: SceneOverride | null
}

export interface Shot {
  id: string
  scene_id: string
  shot_number: number
  shot_type: 'closeup' | 'medium' | 'wide' | 'overhead'
  camera_movement: 'static' | 'pan' | 'tilt' | 'zoom' | 'tracking'
  duration_sec: number
  visual_description: string
  character_actions: Record<string, string>
  character_positions: Record<string, Position>
  dialogues: Dialogue[]
  narration: string | null
  emotion_tags: string[]
  character_emotions: Record<string, string>
}

export interface Position {
  x: number
  y: number
  depth: number
  facing: 'left' | 'right' | 'center' | 'front' | 'back'
}

export interface Dialogue {
  id: string
  character_id: string
  text: string
  emotion: 'happy' | 'sad' | 'angry' | 'fearful' | 'surprised' | 'calm' | 'whisper'
  volume: 'whisper' | 'normal' | 'loud' | 'shout'
  pace: 'slow' | 'normal' | 'fast'
  pause_after_sec: number
  overlap_with_previous: boolean
}

export interface DialogueDto {
  character_id: string
  text: string
  emotion?: string
  volume?: string
  pace?: string
}

export interface EmotionParams {
  emotion: string
  volume: string
  pace: string
  pause_after_sec?: number
}

export interface VoiceParams {
  emotion?: string
  speed: number | string
  pitch: number | string
  volume: number | string
}

export interface TimingDto {
  start_time: number
  end_time: number
}

export interface SceneOverride {
  scene_id: string
  color_palette?: string
  mood?: string
  extra_prompt?: string
  custom_overrides: Record<string, string>
}

export interface JSONTemplate {
  id: string
  name: string
  slug: string
  category: 'script' | 'character' | 'storyboard' | 'dialogue'
  description: string
  schema: Record<string, any>
  example: Record<string, any>
  system_prompt_suffix: string
  version: number
  is_builtin: boolean
  created_at: string
  updated_at: string
}

export interface CreateTemplateDto {
  name: string
  slug: string
  category: string
  description: string
  schema: Record<string, any>
  example: Record<string, any>
  system_prompt_suffix?: string
}

export interface ProductionTask {
  id: string
  episode_id: string
  stage: 'keyframes' | 'clips' | 'voices' | 'bgm' | 'subtitles' | 'timeline' | 'composite'
  status: 'pending' | 'processing' | 'review' | 'completed' | 'failed'
  assets: Record<string, any>
  review_notes: string
  created_at: string
  updated_at: string
}

export interface ProductionProgress {
  episode_id: string
  stages: { stage: string; status: string; progress: number }[]
  overall_progress: number
}

// 阶段类型
export type ProductionStage = 'keyframes' | 'clips' | 'voices' | 'bgm' | 'subtitles' | 'timeline' | 'composite'

export const PRODUCTION_STAGES: { key: ProductionStage; label: string }[] = [
  { key: 'keyframes', label: '关键帧' },
  { key: 'clips', label: '片段剪辑' },
  { key: 'voices', label: '语音合成' },
  { key: 'bgm', label: '背景音乐' },
  { key: 'subtitles', label: '字幕生成' },
  { key: 'timeline', label: '时间线组装' },
  { key: 'composite', label: '最终合成' },
]
