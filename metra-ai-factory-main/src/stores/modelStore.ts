import { create } from 'zustand';

interface ModelRecommendation {
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
      // Assuming 'api' is a pre-configured axios or fetch client
      // We will need to import it in the actual component.
      const response = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskDefinition),
      });
      if (!response.ok) {
        throw new Error('Failed to fetch recommendations');
      }
      const data = await response.json();
      set({ recommendations: data, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },
  selectModel: (modelId) => set({ selectedModelId: modelId }),
})); 