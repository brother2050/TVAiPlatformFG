# TVAiPlatform 共享开发合约

## 一、项目根目录
```
/root/.openclaw/workspace/TVAiPlatform/
```
所有文件路径均以此为根。

---

## 二、数据库模型（SQLAlchemy 2.0 异步，PostgreSQL 17）

### 表名与字段严格定义

#### projects 表
```python
# api/models/project.py
class Project(Base):
    __tablename__ = "projects"
    id: str  # UUID, PK
    title: str  # VARCHAR(200)
    genre: str  # VARCHAR(50)
    style: str  # VARCHAR(50)
    total_episodes: int  # INTEGER, default=10
    episode_duration_sec: int  # INTEGER, default=120
    global_settings: dict  # JSONB
    status: str  # VARCHAR(20): draft/generating/completed
    created_at: datetime
    updated_at: datetime
```

#### episodes 表
```python
# api/models/project.py
class Episode(Base):
    __tablename__ = "episodes"
    id: str  # UUID, PK
    project_id: str  # FK -> projects.id
    episode_number: int  # INTEGER
    title: str  # VARCHAR(200)
    synopsis: str  # TEXT
    status: str  # VARCHAR(20): draft/generating/completed
    created_at: datetime
    updated_at: datetime
```

#### characters 表
```python
# api/models/character.py
class Character(Base):
    __tablename__ = "characters"
    id: str  # UUID, PK
    project_id: str  # FK -> projects.id
    name: str  # VARCHAR(100)
    gender: str  # VARCHAR(20): male/female/other
    appearance: dict  # JSONB {face_shape, eye_color, hair_style, hair_color, skin_tone, distinctive_features, expression_bias}
    body: dict  # JSONB {height_cm, weight_kg, body_type}
    voice: dict  # JSONB {tone, speed, pitch}
    wardrobe_default: dict  # JSONB {top, bottom, shoes, color_palette}
    reference_images: dict  # JSONB {view_name: image_path}
    consistency_seed: int  # INTEGER
    face_embedding: list  # JSONB (512-dim float array)
    created_at: datetime
    updated_at: datetime
```

#### scenes 表
```python
# api/models/script.py
class Scene(Base):
    __tablename__ = "scenes"
    id: str  # UUID, PK
    episode_id: str  # FK -> episodes.id
    scene_number: int  # INTEGER
    location: str  # VARCHAR(200)
    time_of_day: str  # VARCHAR(50)
    weather: str  # VARCHAR(50)
    atmosphere: str  # VARCHAR(100)
    characters_present: list  # JSONB (character_id array)
    background_music: str  # TEXT
    ambient_sound: str  # TEXT
    scene_overrides: dict  # JSONB (nullable)
```

#### shots 表
```python
# api/models/script.py
class Shot(Base):
    __tablename__ = "shots"
    id: str  # UUID, PK
    scene_id: str  # FK -> scenes.id
    shot_number: int  # INTEGER
    shot_type: str  # VARCHAR(20): closeup/medium/wide/overhead
    camera_movement: str  # VARCHAR(20): static/pan/tilt/zoom/tracking
    duration_sec: float  # FLOAT
    visual_description: str  # TEXT
    character_actions: dict  # JSONB {character_id: action_text}
    character_positions: dict  # JSONB {character_id: {x, y, depth, facing}}
    dialogues: list  # JSONB [{character_id, text, emotion, volume, pace, pause_after_sec, overlap_with_previous}]
    narration: str  # TEXT (nullable)
    emotion_tags: list  # JSONB
    character_emotions: dict  # JSONB {character_id: emotion_text}
```

#### templates 表
```python
# api/models/template.py
class JSONTemplate(Base):
    __tablename__ = "templates"
    id: str  # UUID, PK
    name: str  # VARCHAR(100)
    slug: str  # VARCHAR(50), UNIQUE
    category: str  # VARCHAR(50): script/character/storyboard/dialogue
    description: str  # TEXT
    schema: dict  # JSONB
    example: dict  # JSONB
    system_prompt_suffix: str  # TEXT
    version: int  # INTEGER, default=1
    is_builtin: bool  # BOOLEAN, default=True
    created_at: datetime
    updated_at: datetime
```

#### production_tasks 表
```python
# api/models/production.py
class ProductionTask(Base):
    __tablename__ = "production_tasks"
    id: str  # UUID, PK
    episode_id: str  # FK -> episodes.id
    stage: str  # VARCHAR(30): keyframes/clips/voices/bgm/subtitles/timeline/composite
    status: str  # VARCHAR(20): pending/processing/review/completed/failed
    assets: dict  # JSONB (asset paths/metadata)
    review_notes: str  # TEXT
    created_at: datetime
    updated_at: datetime
```

#### summaries 表
```python
# api/models/summary.py
class Summary(Base):
    __tablename__ = "summaries"
    id: str  # UUID, PK
    project_id: str  # FK -> projects.id
    summary_type: str  # VARCHAR(20): project/arc/episode
    episode_number: int  # INTEGER (nullable, for episode summaries)
    arc_name: str  # VARCHAR(100) (nullable)
    content: str  # TEXT
    metadata: dict  # JSONB (key_events, character_changes, etc.)
    generated_at: datetime
```

---

## 三、API 路由前缀与响应格式

### 统一响应格式
```python
# 所有API返回统一格式
class ApiResponse(BaseModel):
    code: int = 0  # 0=success, non-zero=error
    message: str = "success"
    data: Any = None
```

### 路由分组（每个router文件只负责自己的前缀）
| Router文件 | 前缀 | 负责范围 |
|---|---|---|
| routers/projects.py | /api/projects | 项目CRUD + 集数管理 |
| routers/characters.py | /api/characters | 角色CRUD + 参考图 |
| routers/scripts.py | /api/episodes/{id}/script, /api/shots | 剧本+分镜 |
| routers/templates.py | /api/templates | 模板CRUD |
| routers/settings.py | /api/projects/{id}/settings | 全局设定 |
| routers/production.py | /api/episodes/{id}/produce | 生产管线 |
| routers/editor.py | /api/editor/* | 所有手工编辑 |
| routers/media.py | /api/media | 媒体预览 |
| routers/health.py | /api/health | 健康检查 |

---

## 四、前端路由定义

```typescript
// web/src/router/index.ts
const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '我的短剧' } },
  { path: '/project/:id/characters', name: 'Characters', component: () => import('@/views/CharacterStudio.vue'), meta: { title: '角色设计' } },
  { path: '/project/:id/script', name: 'Script', component: () => import('@/views/ScriptEditor.vue'), meta: { title: '写剧本' } },
  { path: '/project/:id/storyboard', name: 'Storyboard', component: () => import('@/views/Storyboard.vue'), meta: { title: '分镜板' } },
  { path: '/project/:id/production', name: 'Production', component: () => import('@/views/Production.vue'), meta: { title: '开始制作' } },
  { path: '/project/:id/timeline', name: 'Timeline', component: () => import('@/views/TimelineEditor.vue'), meta: { title: '时间轴' } },
  { path: '/project/:id/adjust/text', name: 'TextAdjust', component: () => import('@/views/TextAdjust.vue'), meta: { title: '改台词' } },
  { path: '/project/:id/adjust/image', name: 'ImageAdjust', component: () => import('@/views/ImageAdjust.vue'), meta: { title: '修图片' } },
  { path: '/project/:id/adjust/voice', name: 'VoiceAdjust', component: () => import('@/views/VoiceAdjust.vue'), meta: { title: '调配音' } },
  { path: '/project/:id/adjust/bgm', name: 'BgmAdjust', component: () => import('@/views/BgmAdjust.vue'), meta: { title: '配音乐' } },
  { path: '/project/:id/adjust/subtitle', name: 'SubtitleAdjust', component: () => import('@/views/SubtitleAdjust.vue'), meta: { title: '改字幕' } },
  { path: '/project/:id/adjust/video', name: 'VideoAdjust', component: () => import('@/views/VideoAdjust.vue'), meta: { title: '剪视频' } },
  { path: '/templates', name: 'Templates', component: () => import('@/views/TemplateWorkshop.vue'), meta: { title: '调模板' } },
  { path: '/project/:id/settings', name: 'Settings', component: () => import('@/views/GlobalSettings.vue'), meta: { title: '全局设定' } },
  { path: '/project/:id/export', name: 'Export', component: () => import('@/views/Export.vue'), meta: { title: '导出作品' } },
]
```

---

## 五、前端 API 函数签名

```typescript
// web/src/api/project.ts
export const projectApi = {
  list: () => http.get<ApiResponse<Project[]>>('/api/projects'),
  get: (id: string) => http.get<ApiResponse<Project>>(`/api/projects/${id}`),
  create: (data: CreateProjectDto) => http.post<ApiResponse<Project>>('/api/projects', data),
  update: (id: string, data: Partial<Project>) => http.put<ApiResponse<Project>>(`/api/projects/${id}`, data),
  delete: (id: string) => http.delete<ApiResponse<void>>(`/api/projects/${id}`),
  duplicate: (id: string) => http.post<ApiResponse<Project>>(`/api/projects/${id}/duplicate`),
  getSettings: (id: string) => http.get<ApiResponse<ProjectGlobalSettings>>(`/api/projects/${id}/settings`),
  updateSettings: (id: string, data: ProjectGlobalSettings) => http.put<ApiResponse<ProjectGlobalSettings>>(`/api/projects/${id}/settings`, data),
  addDimension: (id: string, key: string, value: string) => http.post<ApiResponse<void>>(`/api/projects/${id}/settings/dimensions`, { key, value }),
  removeDimension: (id: string, key: string) => http.delete<ApiResponse<void>>(`/api/projects/${id}/settings/dimensions/${key}`),
}

// web/src/api/character.ts
export const characterApi = {
  list: (projectId: string) => http.get<ApiResponse<Character[]>>(`/api/projects/${projectId}/characters`),
  get: (id: string) => http.get<ApiResponse<Character>>(`/api/characters/${id}`),
  create: (projectId: string, data: CreateCharacterDto) => http.post<ApiResponse<Character>>(`/api/projects/${projectId}/characters`, data),
  update: (id: string, data: Partial<Character>) => http.put<ApiResponse<Character>>(`/api/characters/${id}`, data),
  delete: (id: string) => http.delete<ApiResponse<void>>(`/api/characters/${id}`),
  generateReferenceSheet: (id: string) => http.post<ApiResponse<string>>(`/api/characters/${id}/reference-sheet`),
}

// web/src/api/template.ts
export const templateApi = {
  list: () => http.get<ApiResponse<JSONTemplate[]>>('/api/templates'),
  get: (slug: string) => http.get<ApiResponse<JSONTemplate>>(`/api/templates/${slug}`),
  update: (slug: string, data: Partial<JSONTemplate>) => http.put<ApiResponse<JSONTemplate>>(`/api/templates/${slug}`, data),
  create: (data: CreateTemplateDto) => http.post<ApiResponse<JSONTemplate>>('/api/templates', data),
  delete: (slug: string) => http.delete<ApiResponse<void>>(`/api/templates/${slug}`),
  reset: (slug: string) => http.post<ApiResponse<void>>(`/api/templates/${slug}/reset`),
  preview: (slug: string) => http.post<ApiResponse<any>>(`/api/templates/${slug}/preview`),
}

// web/src/api/production.ts
export const productionApi = {
  produce: (episodeId: string) => http.post<ApiResponse<string>>(`/api/episodes/${episodeId}/produce`),
  getProgress: (episodeId: string) => http.get<ApiResponse<ProductionProgress>>(`/api/episodes/${episodeId}/progress`),
  regenerateKeyframe: (shotId: string) => http.post<ApiResponse<string>>(`/api/shots/${shotId}/regenerate-keyframe`),
  regenerateVoice: (dialogueId: string) => http.post<ApiResponse<string>>(`/api/dialogues/${dialogueId}/regenerate-voice`),
}

// web/src/api/editor.ts
export const editorApi = {
  // 文本编辑
  updateDialogueText: (id: string, text: string) => http.put<ApiResponse<void>>(`/api/editor/dialogues/${id}/text`, { text }),
  updateDialogueEmotion: (id: string, data: EmotionParams) => http.put<ApiResponse<void>>(`/api/editor/dialogues/${id}/emotion`, data),
  insertDialogue: (sceneId: string, data: DialogueDto) => http.post<ApiResponse<Dialogue>>(`/api/editor/dialogues`, { scene_id: sceneId, ...data }),
  deleteDialogue: (id: string) => http.delete<ApiResponse<void>>(`/api/editor/dialogues/${id}`),
  // 图片编辑
  regenerateImage: (id: string) => http.post<ApiResponse<string>>(`/api/editor/images/${id}/regenerate`),
  inpaintImage: (id: string, mask: File, prompt: string) => http.post<ApiResponse<string>>(`/api/editor/images/${id}/inpaint`, { mask, prompt }),
  uploadReplaceImage: (id: string, file: File) => http.post<ApiResponse<string>>(`/api/editor/images/${id}/upload-replace`, { file }),
  // 语音编辑
  regenerateVoice: (id: string) => http.post<ApiResponse<string>>(`/api/editor/voices/${id}/regenerate`),
  updateVoiceParams: (id: string, params: VoiceParams) => http.put<ApiResponse<void>>(`/api/editor/voices/${id}/params`, params),
  // 字幕编辑
  updateSubtitleText: (id: string, text: string) => http.put<ApiResponse<void>>(`/api/editor/subtitles/${id}/text`, { text }),
  updateSubtitleTiming: (id: string, timing: TimingDto) => http.put<ApiResponse<void>>(`/api/editor/subtitles/${id}/timing`, timing),
  // 视频编辑
  trimVideo: (id: string, start: number, end: number) => http.put<ApiResponse<void>>(`/api/editor/videos/${id}/trim`, { start, end }),
  updateTransition: (id: string, transition: string) => http.put<ApiResponse<void>>(`/api/editor/videos/${id}/transition`, { transition }),
}
```

---

## 六、前端 Store 签名（Pinia）

```typescript
// web/src/stores/project.ts
interface ProjectState {
  projects: Project[]
  currentProject: Project | null
  loading: boolean
}
// Actions: fetchProjects, fetchProject, createProject, updateProject, deleteProject

// web/src/stores/character.ts
interface CharacterState {
  characters: Character[]
  currentCharacter: Character | null
  loading: boolean
}
// Actions: fetchCharacters, fetchCharacter, createCharacter, updateCharacter, deleteCharacter

// web/src/stores/timeline.ts
interface TimelineState {
  scenes: Scene[]
  currentScene: Scene | null
  currentShot: Shot | null
  playheadTime: number
  playing: boolean
}
// Actions: fetchScenes, setCurrentScene, setCurrentShot, setPlayheadTime

// web/src/stores/production.ts
interface ProductionState {
  tasks: ProductionTask[]
  progress: Record<string, number>
  currentStage: string
}
// Actions: fetchTasks, startProduction, getProgress

// web/src/stores/template.ts
interface TemplateState {
  templates: JSONTemplate[]
  currentTemplate: JSONTemplate | null
  loading: boolean
}
// Actions: fetchTemplates, fetchTemplate, updateTemplate, createTemplate, deleteTemplate

// web/src/stores/settings.ts
interface SettingsState {
  globalSettings: ProjectGlobalSettings | null
  sceneOverrides: Record<string, SceneOverride>
}
// Actions: fetchSettings, updateSettings, addDimension, removeDimension, fetchSceneOverrides, updateSceneOverrides
```

---

## 七、config.yaml 结构（后端读取）

```python
# api/config.py 使用 pydantic-settings
class AppConfig(BaseSettings):
    server: ServerConfig  # host, api_port, web_port
    comfyui: ComfyUIConfig  # base_url, timeout, upload_timeout, ssl_verify
    dify: DifyConfig  # api_url, api_key
    tts: TTSConfig  # engine, engines dict
    database: DatabaseConfig  # type, postgres_url, pool_size, max_overflow
    redis: RedisConfig  # url
    storage: StorageConfig  # type, local_path, image_format, image_quality, etc.
```

---

## 八、Agent 边界约束

| Agent | 只能创建/修改的目录 | 不能碰的目录 |
|---|---|---|
| Agent-1 (后端基础) | api/models/, api/config.py, api/main.py, api/routers/, api/json_templates/, .env, config.yaml | api/services/, web/, tts/, scripts/ |
| Agent-2 (后端服务) | api/services/, api/workflows/, api/dify_apps/ | api/models/, api/routers/, web/, tts/, scripts/ |
| Agent-3 (前端基础) | web/src/stores/, web/src/api/, web/src/components/, web/src/router, web/package.json, web/vite.config.ts, web/tsconfig.json | api/, tts/, scripts/ |
| Agent-4 (前端页面) | web/src/views/ | api/, web/src/stores/, web/src/api/, tts/, scripts/ |
| Agent-5 (管线+脚本) | api/services/production_pipeline.py, api/services/sync_engine.py, api/services/ffmpeg_service.py, api/services/storage_optimizer.py, api/services/context_compressor.py, api/services/summary_service.py, api/services/*_editor.py, tts/, scripts/, supervisord.conf | api/models/, api/routers/, web/ |

---

## 九、共享类型（TypeScript）

```typescript
// web/src/api/index.ts
interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

interface Project {
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

interface ProjectGlobalSettings {
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

interface Character {
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

interface AppearanceSpec {
  face_shape: string
  eye_color: string
  hair_style: string
  hair_color: string
  skin_tone: string
  distinctive_features: string[]
  expression_bias: string
}

interface BodySpec {
  height_cm: number
  weight_kg: number
  body_type: string
}

interface VoiceSpec {
  tone: string
  speed: string
  pitch: string
}

interface WardrobeSpec {
  top: string
  bottom: string
  shoes: string
  color_palette: string[]
}

interface Scene {
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

interface Shot {
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

interface Position {
  x: number
  y: number
  depth: number
  facing: 'left' | 'right' | 'center' | 'front' | 'back'
}

interface Dialogue {
  id: string
  character_id: string
  text: string
  emotion: 'happy' | 'sad' | 'angry' | 'fearful' | 'surprised' | 'calm' | 'whisper'
  volume: 'whisper' | 'normal' | 'loud' | 'shout'
  pace: 'slow' | 'normal' | 'fast'
  pause_after_sec: number
  overlap_with_previous: boolean
}

interface SceneOverride {
  scene_id: string
  color_palette?: string
  mood?: string
  extra_prompt?: string
  custom_overrides: Record<string, string>
}

interface JSONTemplate {
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

interface ProductionTask {
  id: string
  episode_id: string
  stage: 'keyframes' | 'clips' | 'voices' | 'bgm' | 'subtitles' | 'timeline' | 'composite'
  status: 'pending' | 'processing' | 'review' | 'completed' | 'failed'
  assets: Record<string, any>
  review_notes: string
  created_at: string
  updated_at: string
}

interface ProductionProgress {
  episode_id: string
  stages: { stage: string; status: string; progress: number }[]
  overall_progress: number
}
```
