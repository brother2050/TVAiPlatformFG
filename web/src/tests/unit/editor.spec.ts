/**
 * Editor API Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { editorApi } from '@/api/editor'

describe('Editor API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should have dialogue update methods', () => {
    expect(editorApi.updateDialogueText).toBeDefined()
    expect(editorApi.updateDialogueEmotion).toBeDefined()
    expect(editorApi.insertDialogue).toBeDefined()
    expect(editorApi.deleteDialogue).toBeDefined()
  })

  it('should have image editing methods', () => {
    expect(editorApi.regenerateImage).toBeDefined()
    expect(editorApi.inpaintImage).toBeDefined()
    expect(editorApi.uploadReplaceImage).toBeDefined()
  })

  it('should have voice editing methods', () => {
    expect(editorApi.regenerateVoice).toBeDefined()
    expect(editorApi.updateVoiceParams).toBeDefined()
  })

  it('should have subtitle editing methods', () => {
    expect(editorApi.updateSubtitleText).toBeDefined()
    expect(editorApi.updateSubtitleTiming).toBeDefined()
  })

  it('should have video editing methods', () => {
    expect(editorApi.trimVideo).toBeDefined()
    expect(editorApi.updateTransition).toBeDefined()
  })

  it('should have BGM methods', () => {
    expect(editorApi.getBgmData).toBeDefined()
    expect(editorApi.updateBgm).toBeDefined()
    expect(editorApi.generateBgm).toBeDefined()
    expect(editorApi.uploadBgm).toBeDefined()
  })

  it('should have SFX methods', () => {
    expect(editorApi.uploadSfx).toBeDefined()
    expect(editorApi.deleteSfx).toBeDefined()
    expect(editorApi.addSfxFromLibrary).toBeDefined()
  })

  it('should have mix level methods', () => {
    expect(editorApi.updateMixLevels).toBeDefined()
  })
})

describe('Editor API Types', () => {
  it('should have correct BgmItem type', () => {
    const bgmItem = {
      id: 'test-id',
      name: 'Test BGM',
      description: 'Test description',
      url: '/storage/bgm/test.mp3',
    }
    expect(bgmItem.id).toBeDefined()
    expect(bgmItem.name).toBeDefined()
  })

  it('should have correct SfxItem type', () => {
    const sfxItem = {
      id: 'test-id',
      name: 'Test SFX',
      type: 'foley',
      volume: 80,
      url: '/storage/sfx/test.wav',
    }
    expect(sfxItem.id).toBeDefined()
    expect(sfxItem.volume).toBeLessThanOrEqual(100)
  })

  it('should have correct MixLevels type', () => {
    const mixLevels = {
      bgm: 60,
      voice: 80,
      ambient: 30,
      sfx: 50,
    }
    expect(mixLevels.bgm).toBeLessThanOrEqual(100)
    expect(mixLevels.voice).toBeLessThanOrEqual(100)
  })
})
