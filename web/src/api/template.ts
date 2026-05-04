import http, { type ApiResponse, type JSONTemplate, type CreateTemplateDto } from './index'

export const templateApi = {
  list: () => http.get<ApiResponse<JSONTemplate[]>>('/templates'),
  get: (slug: string) => http.get<ApiResponse<JSONTemplate>>(`/templates/${slug}`),
  update: (slug: string, data: Partial<JSONTemplate>) => http.put<ApiResponse<JSONTemplate>>(`/templates/${slug}`, data),
  create: (data: CreateTemplateDto) => http.post<ApiResponse<JSONTemplate>>('/templates', data),
  delete: (slug: string) => http.delete<ApiResponse<void>>(`/templates/${slug}`),
  reset: (slug: string) => http.post<ApiResponse<void>>(`/templates/${slug}/reset`),
  preview: (slug: string) => http.post<ApiResponse<any>>(`/templates/${slug}/preview`),
}
