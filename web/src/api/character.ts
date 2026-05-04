import http, { type ApiResponse, type Character, type CreateCharacterDto } from './index'

export const characterApi = {
  list: (projectId: string) => http.get<ApiResponse<Character[]>>(`/projects/${projectId}/characters`),
  get: (id: string) => http.get<ApiResponse<Character>>(`/characters/${id}`),
  create: (projectId: string, data: CreateCharacterDto) => http.post<ApiResponse<Character>>(`/projects/${projectId}/characters`, data),
  update: (id: string, data: Partial<Character>) => http.put<ApiResponse<Character>>(`/characters/${id}`, data),
  delete: (id: string) => http.delete<ApiResponse<void>>(`/characters/${id}`),
  generateReferenceSheet: (id: string) => http.post<ApiResponse<string>>(`/characters/${id}/reference-sheet`),
}
