import { create } from 'zustand';

interface ModelStore {
  selectedModelId: string | null;
  recommendations: any[]; // You can define a proper type later
  setSelectedModelId: (modelId: string) => void;
  setRecommendations: (recommendations: any[]) => void;
}

export const useModelStore = create<ModelStore>((set) => ({
  selectedModelId: null,
  recommendations: [],
  setSelectedModelId: (modelId) => set({ selectedModelId: modelId }),
  setRecommendations: (recommendations) => set({ recommendations }),
})); 