/**
 * Timeline Store Unit Tests
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTimelineStore } from '@/stores/timeline'

describe('Timeline Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should have initial state', () => {
    const store = useTimelineStore()
    expect(store.scenes).toEqual([])
    expect(store.currentScene).toBeNull()
    expect(store.currentShot).toBeNull()
    expect(store.playheadTime).toBe(0)
    expect(store.playing).toBe(false)
  })

  it('should set playhead time', () => {
    const store = useTimelineStore()
    store.setPlayheadTime(5.5)
    expect(store.playheadTime).toBe(5.5)
  })

  it('should toggle playing state', () => {
    const store = useTimelineStore()
    expect(store.playing).toBe(false)
    store.togglePlaying()
    expect(store.playing).toBe(true)
    store.togglePlaying()
    expect(store.playing).toBe(false)
  })

  it('should set current scene', () => {
    const store = useTimelineStore()
    const mockScene = { id: 'scene1', scene_number: 1 }
    store.setCurrentScene(mockScene as any)
    expect(store.currentScene).toEqual(mockScene)
    expect(store.currentShot).toBeNull()
  })

  it('should set current shot', () => {
    const store = useTimelineStore()
    const mockShot = { id: 'shot1', shot_number: 1 }
    store.setCurrentShot(mockShot as any)
    expect(store.currentShot).toEqual(mockShot)
  })
})
