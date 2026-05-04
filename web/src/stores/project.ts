import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectApi } from '@/api/project'
import type { Project, CreateProjectDto } from '@/api/index'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const loading = ref(false)

  async function fetchProjects() {
    loading.value = true
    try {
      const res = await projectApi.list()
      projects.value = res.data.data
    } finally {
      loading.value = false
    }
  }

  async function fetchProject(id: string) {
    loading.value = true
    try {
      const res = await projectApi.get(id)
      currentProject.value = res.data.data
      return res.data.data
    } finally {
      loading.value = false
    }
  }

  async function createProject(data: CreateProjectDto) {
    const res = await projectApi.create(data)
    projects.value.push(res.data.data)
    return res.data.data
  }

  async function updateProject(id: string, data: Partial<Project>) {
    const res = await projectApi.update(id, data)
    const idx = projects.value.findIndex((p) => p.id === id)
    if (idx >= 0) projects.value[idx] = res.data.data
    if (currentProject.value?.id === id) currentProject.value = res.data.data
    return res.data.data
  }

  async function deleteProject(id: string) {
    await projectApi.delete(id)
    projects.value = projects.value.filter((p) => p.id !== id)
    if (currentProject.value?.id === id) currentProject.value = null
  }

  async function duplicateProject(id: string) {
    const res = await projectApi.duplicate(id)
    projects.value.push(res.data.data)
    return res.data.data
  }

  return { projects, currentProject, loading, fetchProjects, fetchProject, createProject, updateProject, deleteProject, duplicateProject }
})
