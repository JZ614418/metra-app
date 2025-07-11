import { create } from 'zustand'

export interface ModelRecommendation {
  model_id: string
  model_name: string
  description?: string
  tags: string[]
  downloads: number
  likes: number
  author?: string
}

interface ModelStore {
  // State
  recommendedModels: ModelRecommendation[]
  selectedModel: ModelRecommendation | null
  isLoading: boolean
  error: string | null
  searchKeywords: string
  
  // Actions
  setRecommendedModels: (models: ModelRecommendation[]) => void
  setSelectedModel: (model: ModelRecommendation | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setSearchKeywords: (keywords: string) => void
  clearRecommendations: () => void
}

export const useModelStore = create<ModelStore>((set) => ({
  // Initial state
  recommendedModels: [],
  selectedModel: null,
  isLoading: false,
  error: null,
  searchKeywords: '',
  
  // Actions
  setRecommendedModels: (models) => set({ recommendedModels: models }),
  setSelectedModel: (model) => set({ selectedModel: model }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  setSearchKeywords: (keywords) => set({ searchKeywords: keywords }),
  clearRecommendations: () => set({ 
    recommendedModels: [], 
    selectedModel: null, 
    error: null,
    searchKeywords: ''
  }),
})) 