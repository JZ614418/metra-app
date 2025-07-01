import { create } from 'zustand';

interface Model {
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
  recommendations: Model[];
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
      // We will use the generic 'api.post' from our api client
      const response = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskDefinition),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch recommendations');
      }
      const data = await response.json();
      set({ recommendations: data, isLoading: false, selectedModelId: data[0]?.modelId || null });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },
  selectModel: (modelId: string) => {
    set({ selectedModelId: modelId });
  },
})); 