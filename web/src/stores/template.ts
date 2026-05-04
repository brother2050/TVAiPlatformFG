import { defineStore } from 'pinia'
import { ref } from 'vue'
import { templateApi } from '@/api/template'
import type { JSONTemplate, CreateTemplateDto } from '@/api/index'

export const useTemplateStore = defineStore('template', () => {
  const templates = ref<JSONTemplate[]>([])
  const currentTemplate = ref<JSONTemplate | null>(null)
  const loading = ref(false)

  async function fetchTemplates() {
    loading.value = true
    try {
      const res = await templateApi.list()
      templates.value = res.data.data
    } finally {
      loading.value = false
    }
  }

  async function fetchTemplate(slug: string) {
    loading.value = true
    try {
      const res = await templateApi.get(slug)
      currentTemplate.value = res.data.data
    } finally {
      loading.value = false
    }
  }

  async function updateTemplate(slug: string, data: Partial<JSONTemplate>) {
    const res = await templateApi.update(slug, data)
    const idx = templates.value.findIndex((t) => t.slug === slug)
    if (idx >= 0) templates.value[idx] = res.data.data
    if (currentTemplate.value?.slug === slug) currentTemplate.value = res.data.data
    return res.data.data
  }

  async function createTemplate(data: CreateTemplateDto) {
    const res = await templateApi.create(data)
    templates.value.push(res.data.data)
    return res.data.data
  }

  async function deleteTemplate(slug: string) {
    await templateApi.delete(slug)
    templates.value = templates.value.filter((t) => t.slug !== slug)
    if (currentTemplate.value?.slug === slug) currentTemplate.value = null
  }

  async function resetTemplate(slug: string) {
    await templateApi.reset(slug)
    await fetchTemplates()
  }

  async function previewTemplate(slug: string) {
    const res = await templateApi.preview(slug)
    return res.data.data
  }

  return {
    templates, currentTemplate, loading,
    fetchTemplates, fetchTemplate, updateTemplate, createTemplate, deleteTemplate,
    resetTemplate, previewTemplate,
  }
})
