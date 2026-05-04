import { defineStore } from 'pinia'
import { ref } from 'vue'
import { characterApi } from '@/api/character'
import type { Character, CreateCharacterDto } from '@/api/index'

export const useCharacterStore = defineStore('character', () => {
  const characters = ref<Character[]>([])
  const currentCharacter = ref<Character | null>(null)
  const loading = ref(false)

  async function fetchCharacters(projectId: string) {
    loading.value = true
    try {
      const res = await characterApi.list(projectId)
      characters.value = res.data.data
    } finally {
      loading.value = false
    }
  }

  async function fetchCharacter(id: string) {
    loading.value = true
    try {
      const res = await characterApi.get(id)
      currentCharacter.value = res.data.data
    } finally {
      loading.value = false
    }
  }

  async function createCharacter(projectId: string, data: CreateCharacterDto) {
    const res = await characterApi.create(projectId, data)
    characters.value.push(res.data.data)
    return res.data.data
  }

  async function updateCharacter(id: string, data: Partial<Character>) {
    const res = await characterApi.update(id, data)
    const idx = characters.value.findIndex((c) => c.id === id)
    if (idx >= 0) characters.value[idx] = res.data.data
    if (currentCharacter.value?.id === id) currentCharacter.value = res.data.data
    return res.data.data
  }

  async function deleteCharacter(id: string) {
    await characterApi.delete(id)
    characters.value = characters.value.filter((c) => c.id !== id)
    if (currentCharacter.value?.id === id) currentCharacter.value = null
  }

  async function generateReferenceSheet(id: string) {
    const res = await characterApi.generateReferenceSheet(id)
    return res.data.data
  }

  return { characters, currentCharacter, loading, fetchCharacters, fetchCharacter, createCharacter, updateCharacter, deleteCharacter, generateReferenceSheet }
})
