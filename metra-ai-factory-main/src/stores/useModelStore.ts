import { create } from 'zustand';
import { api } from '@/lib/api'; // Assuming you have a shared api client

export interface ModelRecommendation {
  modelId: string;
  name: string;
  provider: string;
  architecture: string;
  parameters: string;
  description: string;
  strengths: string[];
  weaknesses: string[];
  trainCost: string;
  trainTime: string;
  accuracy: string;
  recommended: boolean;
  expertOpinion: string;
  icon: string;
}

interface ModelStore {
  recommendations: ModelRecommendation[];
  selectedModelId: string | null;
  isLoading: boolean;
  error: string | null;
  fetchRecommendations: (taskDefinition: any) => Promise<void>;
  selectModel: (modelId: string) => void;
}

export const useModelStore = create<ModelStore>((set) => ({
  recommendations: [],
  selectedModelId: null,
  isLoading: false,
  error: null,
  fetchRecommendations: async (taskDefinition) => {
    set({ isLoading: true, error: null });
    try {
      const data = await api.post<ModelRecommendation[]>('/recommend', taskDefinition);
      set({ recommendations: data, isLoading: false, selectedModelId: data[0]?.modelId || null });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch recommendations';
      set({ error: errorMessage, isLoading: false });
    }
  },
  selectModel: (modelId: string) => {
    set({ selectedModelId: modelId });
  },
})); 