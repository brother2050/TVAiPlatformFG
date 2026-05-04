import http, { type ApiResponse, type ProjectGlobalSettings, type SceneOverride } from './index'

export const settingsApi = {
  get: (projectId: string) =>
    http.get<ApiResponse<ProjectGlobalSettings>>(`/projects/${projectId}/settings`),
  update: (projectId: string, data: ProjectGlobalSettings) =>
    http.put<ApiResponse<ProjectGlobalSettings>>(`/projects/${projectId}/settings`, data),
  addDimension: (projectId: string, key: string, value: string) =>
    http.post<ApiResponse<void>>(`/projects/${projectId}/settings/dimensions`, { key, value }),
  removeDimension: (projectId: string, key: string) =>
    http.delete<ApiResponse<void>>(`/projects/${projectId}/settings/dimensions/${key}`),
  getSceneOverrides: (projectId: string, sceneId: string) =>
    http.get<ApiResponse<SceneOverride>>(`/projects/${projectId}/scenes/${sceneId}/overrides`),
  updateSceneOverrides: (projectId: string, sceneId: string, data: SceneOverride) =>
    http.put<ApiResponse<SceneOverride>>(`/projects/${projectId}/scenes/${sceneId}/overrides`, data),
}
