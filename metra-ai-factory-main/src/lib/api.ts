import { useAuthStore } from '@/stores/authStore'

// Dynamic API URL based on environment
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

interface User {
  id: string
  email: string
  full_name?: string
  is_active: boolean
  created_at: string
}

class ApiClient {
  private getHeaders(): HeadersInit {
    const token = useAuthStore.getState().token
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return headers
  }

  async request<T>(
    endpoint: string, 
    options: RequestInit = {},
    isStream: boolean = false
  ): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    })

    if (response.status === 401) {
      // Token expired or invalid
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Something went wrong')
    }

    if (isStream) {
      return response.body as T;
    }

    return response.json()
  }

  async post<T>(endpoint: string, data: any, isStream = false) {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    }, isStream);
  }

  // Auth endpoints
  async register(email: string, password: string, fullName?: string, invitationCode?: string) {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        username: email.split('@')[0],
        full_name: fullName,
        invitation_code: invitationCode,
      }),
    })
  }

  async login(email: string, password: string) {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        password: password,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    return response.json()
  }

  async getMe() {
    return this.request<User>('/auth/me')
  }

  async updateMe(data: { email?: string; full_name?: string; password?: string }) {
    return this.request<User>('/auth/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async getUsageStats() {
    return this.request('/auth/me/usage')
  }

  async forgotPassword(email: string) {
    return this.request('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
  }

  // Model Recommendation endpoints
  async fetchRecommendations(taskDefinition: any) {
    return this.request('/recommendations/recommend', {
      method: 'POST',
      body: JSON.stringify({ task_definition: taskDefinition }),
    })
  }

  // DataBuilder V3 integration
}

export const api = new ApiClient()

// Data Collection APIs
export const dataCollectionAPI = {
  // Start web scraping job
  startWebScraping: async (data: {
    query?: string;
    urls?: string[];
    max_results?: number;
    include_full_content?: boolean;
    sources?: string[];
  }) => {
    const response = await fetch(`${API_URL}/data-collection/web-scraping`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start web scraping');
    }

    return response.json();
  },

  // Get job progress (unified endpoint)
  getJobProgress: async (jobId: string) => {
    const response = await fetch(`${API_URL}/data-collection/job/${jobId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get job progress');
    }

    return response.json();
  },

  // Start AI data generation
  startAIGeneration: async (data: {
    task_type: string;
    task_description: string;
    count?: number;
    labels?: string[];
    examples?: any[];
    style?: string;
  }) => {
    const response = await fetch(`${API_URL}/data-collection/ai-generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start AI generation');
    }

    return response.json();
  },

  // Use the unified getJobProgress for AI generation too
  getGenerationProgress: async (jobId: string) => {
    return dataCollectionAPI.getJobProgress(jobId);
  },

  // Upload data file
  uploadFile: async (file: File, taskType: string, hasLabels: boolean = false, labelColumn?: string, contentColumn?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('task_type', taskType);
    formData.append('has_labels', hasLabels.toString());
    if (labelColumn) formData.append('label_column', labelColumn);
    if (contentColumn) formData.append('content_column', contentColumn);

    const response = await fetch(`${API_URL}/data-collection/file-upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload file');
    }

    return response.json();
  },

  // Get job data (unified endpoint)
  getJobData: async (jobId: string, skip: number = 0, limit: number = 100) => {
    const response = await fetch(`${API_URL}/data-collection/job/${jobId}/data?skip=${skip}&limit=${limit}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get job data');
    }

    return response.json();
  },

  // Alias for backward compatibility
  getScrapingData: async (jobId: string) => {
    return dataCollectionAPI.getJobData(jobId);
  },

  // Alias for backward compatibility
  getGeneratedData: async (jobId: string) => {
    return dataCollectionAPI.getJobData(jobId);
  },

  // Get available data sources
  getAvailableSources: async () => {
    const response = await fetch(`${API_URL}/data-collection/sources`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get available sources');
    }

    return response.json();
  },
};

// Data Builder API
export const dataBuilderAPI = {
  // V3 Data Collection Methods
  startDataCollection: async (taskDefinition: any) => {
    return dataEngineApi.startDataCollection(taskDefinition, taskDefinition.data_volume || 1000);
  },

  getTaskProgress: async (taskId: string) => {
    return dataEngineApi.getTaskProgress(taskId);
  },

  getTaskResult: async (taskId: string, limit: number = 10) => {
    return dataEngineApi.getTaskResult(taskId, limit);
  },

  async getRecommendation(data: {
    task_info: any;
    selected_model: any;
    user_data_volume?: number | null;
  }) {
    const response = await fetch(`${API_URL}/data-builder/recommend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${useAuthStore.getState().token}`,
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) throw new Error('Failed to get recommendation');
    return response.json();
  },
  
  // V2 API - 修复版本，解决硬编码和性能问题
  async startCollectionV2(data: {
    task_info: any;
    selected_model: any;
    data_count: number;
    quality_mode: string;
    enhanced_mode?: boolean;
    task_name?: string;
  }) {
    const response = await fetch(`${API_URL}/data-builder/collect-v2`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${useAuthStore.getState().token}`,
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start collection');
    }
    return response.json();
  },
  
  async getTaskStatusV2(jobId: string) {
    const response = await fetch(`${API_URL}/data-builder/task/${jobId}/status`, {
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`,
      },
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get task status');
    }
    return response.json();
  },
  
  async getTaskDataV2(jobId: string, limit = 100, offset = 0) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    
    const response = await fetch(`${API_URL}/data-builder/task/${jobId}/data?${params}`, {
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`,
      },
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get task data');
    }
    return response.json();
  },
  
  async getUserTasks(skip = 0, limit = 20, status?: string) {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    
    if (status) {
      params.append('status', status);
    }
    
    const response = await fetch(`${API_URL}/data-builder/my-tasks?${params}`, {
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`,
      },
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get user tasks');
    }
    return response.json();
  },
  
  // Legacy V1 API - 保持兼容性
  async startCollection(data: {
    task_info: any;
    selected_model: any;
    data_count: number;
    quality_mode: string;
    use_recommendation: boolean;
  }) {
    const response = await fetch(`${API_URL}/data-builder/collect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${useAuthStore.getState().token}`,
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) throw new Error('Failed to start collection');
    return response.json();
  },
  
  async getJobProgress(jobId: string) {
    const response = await fetch(`${API_URL}/data-builder/job/${jobId}/progress`, {
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`,
      },
    });
    
    if (!response.ok) throw new Error('Failed to get progress');
    return response.json();
  },
  
  async getCollectedData(
    jobId: string,
    skip = 0,
    limit = 100,
    label?: string,
    source?: string
  ) {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    if (label) params.append('label', label);
    if (source) params.append('source', source);
    
    const response = await fetch(`${API_URL}/data-builder/job/${jobId}/data?${params}`, {
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`,
      },
    });
    
    if (!response.ok) throw new Error('Failed to get data');
    return response.json();
  },
  
  async analyzeData(jobId: string, data: { query: string }) {
    const response = await fetch(`${API_URL}/data-builder/job/${jobId}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${useAuthStore.getState().token}`,
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) throw new Error('Failed to analyze data');
    return response.json();
  },
  
  async modifyDataset(jobId: string, data: {
    action: string;
    parameters: any;
  }) {
    const response = await fetch(`${API_URL}/data-builder/job/${jobId}/modify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${useAuthStore.getState().token}`,
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) throw new Error('Failed to modify dataset');
    return response.json();
  },
}; 

// DFE API
export const dfeApi = {
  // ... existing code ...
};

// Training API  
export const trainingApi = {
  // Get all training jobs
  getJobs: async (): Promise<any[]> => {
    const response = await fetch(`${API_URL}/training/jobs`, {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch training jobs');
    }
    
    return response.json();
  },

  // Get training job status
  getStatus: async (jobId: string): Promise<any> => {
    const response = await fetch(`${API_URL}/training/status/${jobId}`, {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch training status');
    }
    
    return response.json();
  },

  // Get training result
  getResult: async (jobId: string): Promise<any> => {
    const response = await fetch(`${API_URL}/training/result/${jobId}`, {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch training result');
    }
    
    return response.json();
  },

  // Start training
  start: async (payload: any): Promise<any> => {
    const response = await fetch(`${API_URL}/training/start`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      throw new Error('Failed to start training');
    }
    
    return response.json();
  },

  // Test model
  test: async (jobId: string, testInput: string): Promise<any> => {
    const response = await fetch(`${API_URL}/training/test/${jobId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ test_input: testInput }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to test model');
    }
    
    return response.json();
  },
};

// Deployment API
export const deploymentApi = {
  // Get trained models available for deployment
  getTrainedModels: async (): Promise<TrainedModel[]> => {
    const response = await fetch(`${API_URL}/deployment/models/trained`, {
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
    });
    if (!response.ok) throw new Error('Failed to fetch trained models');
    return response.json();
  },

  // Deploy a model
  deployModel: async (data: {
    model_id: string;
    type: 'api' | 'widget' | 'export';
    config?: any;
  }): Promise<Deployment> => {
    const response = await fetch(`${API_URL}/deployment/deploy`, {
      method: 'POST',
      headers: {
        ...useAuthStore.getState().token ? {
          'Authorization': `Bearer ${useAuthStore.getState().token}`,
          'Content-Type': 'application/json',
        } : {},
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to deploy model');
    return response.json();
  },

  // Get all deployments
  getDeployments: async (): Promise<Deployment[]> => {
    const response = await fetch(`${API_URL}/deployment/`, {
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
    });
    if (!response.ok) throw new Error('Failed to fetch deployments');
    return response.json();
  },

  // Get specific deployment
  getDeployment: async (deploymentId: string): Promise<Deployment> => {
    const response = await fetch(`${API_URL}/deployment/${deploymentId}`, {
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
    });
    if (!response.ok) throw new Error('Failed to fetch deployment');
    return response.json();
  },

  // Update deployment
  updateDeployment: async (deploymentId: string, updates: any): Promise<Deployment> => {
    const response = await fetch(`${API_URL}/deployment/${deploymentId}`, {
      method: 'PUT',
      headers: {
        ...useAuthStore.getState().token ? {
          'Authorization': `Bearer ${useAuthStore.getState().token}`,
          'Content-Type': 'application/json',
        } : {},
      },
      body: JSON.stringify(updates),
    });
    if (!response.ok) throw new Error('Failed to update deployment');
    return response.json();
  },

  // Delete deployment
  deleteDeployment: async (deploymentId: string): Promise<void> => {
    const response = await fetch(`${API_URL}/deployment/${deploymentId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
    });
    if (!response.ok) throw new Error('Failed to delete deployment');
  },

  // Start deployment
  startDeployment: async (deploymentId: string): Promise<void> => {
    const response = await fetch(`${API_URL}/deployment/${deploymentId}/start`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
    });
    if (!response.ok) throw new Error('Failed to start deployment');
  },

  // Stop deployment
  stopDeployment: async (deploymentId: string): Promise<void> => {
    const response = await fetch(`${API_URL}/deployment/${deploymentId}/stop`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
    });
    if (!response.ok) throw new Error('Failed to stop deployment');
  },

  // Test deployment
  testDeployment: async (deploymentId: string, testInput: any): Promise<any> => {
    const response = await fetch(`${API_URL}/deployment/${deploymentId}/test`, {
      method: 'POST',
      headers: {
        ...useAuthStore.getState().token ? {
          'Authorization': `Bearer ${useAuthStore.getState().token}`,
          'Content-Type': 'application/json',
        } : {},
      },
      body: JSON.stringify({ test_input: testInput }),
    });
    if (!response.ok) throw new Error('Failed to test deployment');
    return response.json();
  },

  // Get deployment metrics
  getDeploymentMetrics: async (deploymentId: string): Promise<any> => {
    const response = await fetch(`${API_URL}/deployment/${deploymentId}/metrics`, {
      headers: {
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
    });
    if (!response.ok) throw new Error('Failed to fetch deployment metrics');
    return response.json();
  },
};

// Data Engine API - V3 Quality-Driven Data Pipeline
export const dataEngineApi = {
  // Start DataBuilder V3 collection task
  startDataCollection: async (taskDefinition: {
    task: string;
    type: string;
    language: string;
    domain: string;
    description: string;
    labels: string[];
    data_volume: number;
  }, target_samples: number = 1000): Promise<{success: boolean, data?: any, error?: string}> => {
    try {
      const response = await fetch(`${API_URL}/data-builder-v3/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task: taskDefinition.task,
          type: taskDefinition.type,
          language: taskDefinition.language,
          domain: taskDefinition.domain,
          description: taskDefinition.description,
          labels: taskDefinition.labels,
          data_volume: taskDefinition.data_volume || target_samples
        }),
      });
      
      if (!response.ok) {
        return { success: false, error: 'Failed to start data collection' };
      }
      
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: (error as Error).message };
    }
  },

  // Get task progress
  getTaskProgress: async (taskId: string): Promise<{success: boolean, data?: any, error?: string}> => {
    try {
      const response = await fetch(`${API_URL}/data-builder-v3/task/${taskId}/progress`, {
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        return { success: false, error: 'Failed to get task progress' };
      }
      
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: (error as Error).message };
    }
  },

  // Get all tasks status
  getAllTasks: async (): Promise<{success: boolean, data?: any, error?: string}> => {
    try {
      const response = await fetch(`${API_URL}/data-builder-v3/tasks`, {
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        return { success: false, error: 'Failed to get tasks' };
      }
      
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: (error as Error).message };
    }
  },

  // Stop a task
  stopTask: async (taskId: string): Promise<{success: boolean, data?: any, error?: string}> => {
    try {
      const response = await fetch(`${API_URL}/data-builder-v3/task/${taskId}/stop`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        return { success: false, error: 'Failed to stop task' };
      }
      
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: (error as Error).message };
    }
  },

  // Get system stats
  getSystemStats: async (): Promise<{success: boolean, data?: any, error?: string}> => {
    try {
      const response = await fetch(`${API_URL}/data-builder-v3/stats`, {
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        return { success: false, error: 'Failed to get system stats' };
      }
      
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: (error as Error).message };
    }
  },

  // Get monitoring status
  getMonitoringStatus: async (): Promise<{success: boolean, data?: any, error?: string}> => {
    try {
      const response = await fetch(`${API_URL}/data-builder-v3/monitoring`, {
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        return { success: false, error: 'Failed to get monitoring status' };
      }
      
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: (error as Error).message };
    }
  },

  // Get task result data - fetch real samples from completed task
  getTaskResult: async (taskId: string, limit: number = 10): Promise<{success: boolean, data?: any, error?: string}> => {
    try {
      const response = await fetch(`${API_URL}/data-builder-v3/task/${taskId}/result?limit=${limit}`, {
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        return { success: false, error: 'Failed to get task result' };
      }
      
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: (error as Error).message };
    }
  },

  // Legacy support - automatically convert old task format to new format
  getDataBuilderTasks: async (): Promise<{success: boolean, data?: any, error?: string}> => {
    // This is now handled by getAllTasks but maintains backward compatibility
    return dataEngineApi.getAllTasks();
  },

};


// Types
export interface ModelRecommendation {
  model_id: string;
  model_name: string;
  description: string;
  tags: string[];
  downloads: number;
  likes: number;
  author?: string;
  pipeline_tag?: string;
  library_name?: string;
}

export interface ModelRecommendationResponse {
  recommendations: ModelRecommendation[];
  total_count: number;
  search_strategy: string;
  debug_info?: any;
}

export interface TrainedModel {
  id: string;
  name: string;
  task_type: string;
  base_model: string;
  accuracy: number;
  trained_at: string;
  status: string;
  size: string;
}

export interface Deployment {
  id: string;
  user_id: string;
  model_id: string;
  type: 'api' | 'widget' | 'export';
  status: 'deploying' | 'active' | 'stopped' | 'failed' | 'completed';
  api_key?: string;
  endpoint?: string;
  widget_code?: string;
  export_url?: string;
  created_at: string;
  config: any;
  api_documentation?: any;
  model_version?: string;
  metrics: {
    api_calls: number;
    total_requests: number;
    errors: number;
    avg_response_time: number;
    uptime: number;
    last_used?: string;
    health?: number;
  };
} 