import http, { type ApiResponse, type Project, type CreateProjectDto } from './index'

export interface Episode {
  id: string
  project_id: string
  episode_number: number
  title: string
  synopsis: string
  status: string
  duration_sec?: number
  created_at: string
  updated_at: string
}

export const projectApi = {
  list: () => http.get<ApiResponse<Project[]>>('/projects'),
  get: (id: string) => http.get<ApiResponse<Project>>(`/projects/${id}`),
  create: (data: CreateProjectDto) => http.post<ApiResponse<Project>>('/projects', data),
  update: (id: string, data: Partial<Project>) => http.put<ApiResponse<Project>>(`/projects/${id}`, data),
  delete: (id: string) => http.delete<ApiResponse<void>>(`/projects/${id}`),
  duplicate: (id: string) => http.post<ApiResponse<Project>>(`/projects/${id}/duplicate`),
  getEpisodes: (projectId: string) => http.get<ApiResponse<Episode[]>>(`/projects/${projectId}/episodes`),
}
