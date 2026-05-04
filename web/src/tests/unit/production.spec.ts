/**
 * Production API Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { productionApi } from '@/api/production'

// Mock axios
vi.mock('@/api/index', async () => {
  const actual = await vi.importActual('@/api/index')
  return {
    ...actual,
    default: {
      post: vi.fn(),
      get: vi.fn(),
    },
  }
})

describe('Production API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should have correct API endpoints', () => {
    expect(productionApi.produce).toBeDefined()
    expect(productionApi.batchProduce).toBeDefined()
    expect(productionApi.getProgress).toBeDefined()
    expect(productionApi.regenerateKeyframe).toBeDefined()
    expect(productionApi.regenerateVoice).toBeDefined()
  })

  it('should call produce endpoint with episode id', () => {
    const mockPost = vi.fn().mockResolvedValue({ data: { code: 0, data: {} } })
    vi.mocked(productionApi.produce).mockImplementation(mockPost)

    productionApi.produce('test-episode-id')
    expect(mockPost).toHaveBeenCalledWith('/api/episodes/test-episode-id/produce')
  })

  it('should call batch produce with stages', () => {
    const mockPost = vi.fn().mockResolvedValue({ data: { code: 0, data: {} } })
    vi.mocked(productionApi.batchProduce).mockImplementation(mockPost)

    const stages = ['keyframes', 'clips', 'voices'] as const
    productionApi.batchProduce('test-episode-id', stages)
    expect(mockPost).toHaveBeenCalledWith(
      '/api/episodes/test-episode-id/produce/batch',
      { stages }
    )
  })

  it('should call get progress endpoint', () => {
    const mockGet = vi.fn().mockResolvedValue({ data: { code: 0, data: {} } })
    vi.mocked(productionApi.getProgress).mockImplementation(mockGet)

    productionApi.getProgress('test-episode-id')
    expect(mockGet).toHaveBeenCalledWith('/api/episodes/test-episode-id/progress')
  })
})
