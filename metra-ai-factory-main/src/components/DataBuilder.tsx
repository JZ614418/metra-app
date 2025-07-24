import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Slider } from '@/components/ui/slider';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { 
  Play, 
  Pause, 
  Download, 
  Zap,
  Info,
  CheckCircle,
  Edit,
  Loader2,
  AlertCircle,
  Database,
  Brain,
  Sparkles,
  Clock,
  TrendingUp,
  Globe,
  Bot,
  Eye,
  ArrowRight,
  FileText,
  Settings
} from 'lucide-react';
import { dataBuilderAPI } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { EmptyState } from '@/components/ui/empty-state';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface TaskInfo {
  task: string;
  type: string;
  language: string;
  labels: string[];
  description?: string;
  domain?: string;
  data_volume?: number;
}

interface SelectedModel {
  id: string;
  name: string;
  provider: string;
  modelType: string;
  size?: string;
}

interface DataRecommendation {
  recommended_count: number;
  min_count: number;
  max_count: number;
  collection_strategy: { web: number; ai: number };
  estimated_time_minutes: number;
  quality_mode: string;
  reasoning: string;
  expected_performance: string;
  data_sources: string[];
}

interface CollectionTask {
  id: string;
  status: 'processing' | 'completed' | 'failed';
  progress: number;
  total: number;
  created_at: string;
  error?: string;
  results?: any[];
}

const DataBuilder = () => {
  const { toast } = useToast();
  const navigate = useNavigate();
  
  // Get task and model info from localStorage
  const [taskInfo, setTaskInfo] = useState<TaskInfo | null>(() => {
    // Try to get from currentTask (saved by ModelRecommend) first
    const savedTask = localStorage.getItem('currentTask');
    if (savedTask) {
      try {
        const task = JSON.parse(savedTask);
        // Check if this is real task data, not just defaults
        if (task.task && task.task !== 'AI Task' && task.task !== 'Your Custom Task') {
          return {
            task: task.task,
            type: task.type || 'text-generation',
            language: task.language || 'chinese',
            labels: task.labels || [],
            description: task.description || '',
            domain: task.domain || 'general',
            data_volume: task.data_volume || task.dataVolume || 20000
          };
        }
      } catch (e) {
        console.error('Failed to parse currentTask:', e);
      }
    }
    
    // Try to get from conversationStore persistence
    const conversationState = localStorage.getItem('conversation-storage');
    if (conversationState) {
      try {
        const state = JSON.parse(conversationState);
        const finalizedTask = state?.state?.lastFinalizedTask;
        if (finalizedTask && finalizedTask.name && finalizedTask.name !== 'AI Task') {
          return {
            task: finalizedTask.name || finalizedTask.task,
            type: finalizedTask.taskType || 'text-generation',
            language: finalizedTask.language || 'chinese',
            labels: finalizedTask.labels || [],
            description: finalizedTask.description || finalizedTask.features || '',
            domain: finalizedTask.domain || 'general',
            data_volume: finalizedTask.data_volume || finalizedTask.dataVolume || 20000
          };
        }
      } catch (e) {
        console.error('Failed to parse conversation state:', e);
      }
    }
    
    // Return null if no valid task data found
    return null;
  });
  
  const [selectedModel, setSelectedModel] = useState<SelectedModel | null>(() => {
    // Try to get from modelStore first
    const modelState = localStorage.getItem('model-storage');
    if (modelState) {
      try {
        const state = JSON.parse(modelState);
        const selected = state?.state?.selectedModel;
        if (selected && selected.id && selected.id !== 'default-model') {
          return {
            id: selected.id,
            name: selected.name || 'ChatGLM2-6B',
            provider: selected.provider || 'THUDM',
            modelType: selected.modelType || 'General',
            size: selected.size || '6B'
          };
        }
      } catch (e) {
        console.error('Failed to parse model state:', e);
      }
    }
    
    const saved = localStorage.getItem('selectedModel');
    if (saved) {
      try {
        const model = JSON.parse(saved);
        // Check if this is a real selected model, not a default
        if (model.id && model.id !== 'default-model' && model.name !== 'Select a Model') {
          return model;
        }
      } catch (e) {
        console.error('Failed to parse selectedModel:', e);
      }
    }
    
    // Return null if no valid model found
    return null;
  });
  
  // State
  const [recommendation, setRecommendation] = useState<DataRecommendation | null>(null);
  const [loadingRecommendation, setLoadingRecommendation] = useState(false);
  const [useRecommendation, setUseRecommendation] = useState(true);
  
  // Collection settings - Use task definition data volume if available
  const [dataCount, setDataCount] = useState<number[]>(() => {
    const defaultCount = taskInfo?.data_volume || 10000;
    return [defaultCount];
  });
  const [qualityMode, setQualityMode] = useState('balanced');
  const [enhancedMode, setEnhancedMode] = useState(false); // 增强模式：全文处理，无上限
  
  // Collection progress
  const [isCollecting, setIsCollecting] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null); // Real task ID from API
  const [progress, setProgress] = useState(0);
  const [collectedCount, setCollectedCount] = useState(0);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [sourcesProgress, setSourcesProgress] = useState<Record<string, number>>({});

  const [selectedTask, setSelectedTask] = useState<CollectionTask | null>(null);
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());
  const [isJsonDialogOpen, setIsJsonDialogOpen] = useState(false);
  const [jsonData, setJsonData] = useState<string>('');
  
  // Data preview states
  const [showDataPreview, setShowDataPreview] = useState(false);
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [previewJobId, setPreviewJobId] = useState<string | null>(null);
  
  // Get AI recommendation on mount only if we have task and model info
  useEffect(() => {
    if (taskInfo && selectedModel) {
      getRecommendation();
    }
  }, [taskInfo, selectedModel]);
  
  const getRecommendation = async () => {
    if (!taskInfo || !selectedModel) return;
    
    setLoadingRecommendation(true);
    try {
      const rec = await dataBuilderAPI.getRecommendation({
        task_info: taskInfo,
        selected_model: selectedModel,
        user_data_volume: taskInfo?.data_volume || null
      });
      setRecommendation(rec);
      
      // Apply recommendation only if user wants to use AI recommendation
      // Don't automatically override user's task definition settings
      if (rec && useRecommendation) {
        // Only apply if AI recommendation differs significantly from task definition
        const taskDataVolume = taskInfo?.data_volume;
        if (!taskDataVolume || Math.abs(rec.recommended_count - taskDataVolume) / taskDataVolume > 0.1) {
          setDataCount([rec.recommended_count]);
        }
        setQualityMode(rec.quality_mode);
      }
    } catch (error) {
      console.error('Failed to get recommendation:', error);
      
      let errorMessage = "Using default settings instead";
      
      if (error instanceof Error) {
        if (error.message.includes('401') || error.message.includes('unauthorized')) {
          errorMessage = "Authentication required to get AI recommendations. Using default settings.";
        } else if (error.message.includes('500') || error.message.includes('server')) {
          errorMessage = "AI service temporarily unavailable. Using default settings.";
        } else if (error.message.includes('network') || error.message.includes('fetch')) {
          errorMessage = "Network error. Using default settings for now.";
        }
      }
      
      toast({
        title: "AI recommendation unavailable",
        description: errorMessage,
        variant: "default", // Use default instead of destructive for less critical errors
      });
    } finally {
      setLoadingRecommendation(false);
    }
  };
  
  const startCollection = async () => {
    if (!taskInfo || !selectedModel) return;
    
    setIsCollecting(true);
    setProgress(0);
    setCollectedCount(0);
    
    try {
      // 生成任务名称
      const taskName = `${taskInfo.description || 'Data Collection'} - ${new Date().toLocaleDateString()}`;
      
      // 使用V3 API - 修复版本，解决硬编码和性能问题
      const response = await dataBuilderAPI.startDataCollection({
        task: taskInfo.task,
        type: taskInfo.type,
        language: taskInfo.language,
        domain: taskInfo.domain || 'general',
        description: taskInfo.description || taskInfo.task,
        labels: taskInfo.labels,
        data_volume: dataCount[0]
      });
      
      if (response.success) {
        setJobId(response.data.task_id);
      } else {
        throw new Error(response.error || 'Failed to start data collection');
      }
      
      toast({
        title: "🚀 Fast data collection started",
        description: response.data?.message || `Estimated ${dataCount[0]} samples will be collected quickly`,
      });
      
      // 使用V3的进度轮询
      if (response.success) {
        pollProgressV3(response.data.task_id);
      }
      
    } catch (error) {
      console.error('Failed to start collection:', error);
      setIsCollecting(false);
      
      let errorMessage = "Unknown error occurred";
      let errorTitle = "Failed to start data collection";
      
      if (error instanceof Error) {
        errorMessage = error.message;
        
        // Provide more specific error messages based on common failure scenarios
        if (error.message.includes('401') || error.message.includes('unauthorized')) {
          errorTitle = "Authentication Required";
          errorMessage = "Please log in again to start data collection.";
        } else if (error.message.includes('403') || error.message.includes('forbidden')) {
          errorTitle = "Access Denied";
          errorMessage = "You don't have permission to start data collection.";
        } else if (error.message.includes('500') || error.message.includes('server')) {
          errorTitle = "Server Error";
          errorMessage = "Server is temporarily unavailable. Please try again in a few minutes.";
        } else if (error.message.includes('network') || error.message.includes('fetch')) {
          errorTitle = "Connection Error";
          errorMessage = "Unable to connect to server. Please check your internet connection.";
        }
      }
      
      toast({
        title: errorTitle,
        description: errorMessage,
        variant: "destructive",
      });
    }
  };
  
  // V3 进度轮询 - 修复版本
  const pollProgressV3 = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const result = await dataBuilderAPI.getTaskProgress(jobId);
        if (!result.success) {
          throw new Error(result.error || 'Failed to get progress');
        }
        const status = result.data;
        
        setProgress(status.progress_percentage || 0);
        setCollectedCount(status.samples_collected || status.collected_count || 0);
        
        // Update current step for better user feedback
        if (status.current_step) {
          setCurrentStep(status.current_step);
        }
        
        if (status.status === 'completed') {
          clearInterval(interval);
          setIsCollecting(false);
          
          toast({
            title: "🎉 Data collection completed!",
            description: `Successfully collected ${status.samples_collected || status.collected_count || 0} high-quality samples`,
          });
        } else if (status.status === 'failed') {
          clearInterval(interval);
          setIsCollecting(false);
          
          // Provide more helpful error message for failed collection
          const errorDescription = status.error || "Collection failed. Please try again with different settings.";
          
          toast({
            title: "Data collection failed",
            description: errorDescription,
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error('Failed to get status:', error);
        
        // Handle network errors during polling
        if (error instanceof Error) {
          if (error.message.includes('401') || error.message.includes('unauthorized')) {
            clearInterval(interval);
            setIsCollecting(false);
            toast({
              title: "Session expired",
              description: "Please log in again to continue monitoring collection progress.",
              variant: "destructive",
            });
          }
          // For other errors, continue polling but log the issue
        }
      }
    }, 2000); // 每2秒检查一次
    
    // 10分钟后停止轮询（防止无限轮询）
    setTimeout(() => {
      clearInterval(interval);
      if (isCollecting) {
        setIsCollecting(false);
        toast({
          title: "Collection timeout",
          description: "Collection is taking longer than expected. Please check the status manually or try again.",
          variant: "default", // Use default variant for timeout (less severe than error)
        });
      }
    }, 600000);
  };

  // Legacy V1 进度轮询 (fallback)
  const pollProgress = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const result = await dataBuilderAPI.getTaskProgress(jobId);
        if (!result.success) {
          throw new Error(result.error || 'Failed to get progress');
        }
        const status = result.data;
        
        setProgress(status.progress_percentage || status.progress || 0);
        setCollectedCount(status.samples_collected || status.collected_count || 0);
        setSourcesProgress(status.sources_progress || {});
        
        if (status.status === 'completed') {
          clearInterval(interval);
          setIsCollecting(false);
          
          toast({
            title: "Data collection completed!",
            description: `Successfully collected ${status.total_count} samples`,
          });
          
          // Auto navigate to view data
          setTimeout(() => {
            navigate(`/data-viewer/${jobId}`);
          }, 2000);
          
        } else if (status.status === 'failed') {
          clearInterval(interval);
          setIsCollecting(false);
          
          toast({
            title: "Data collection failed",
            description: status.errors?.join(', ') || "Unknown error",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error('Failed to get progress:', error);
      }
    }, 2000);
  };
  
  const getEstimatedTime = () => {
    if (recommendation && useRecommendation) {
      return recommendation.estimated_time_minutes;
    }
    
    // Enhanced estimation based on count, mode, and task complexity
    const count = dataCount[0];
    let baseRate = 250; // samples per minute for balanced mode
    
    // Adjust base rate based on task complexity
    if (taskInfo?.type === 'text-generation' || taskInfo?.type === 'translation') {
      baseRate = 180; // Slower for complex text tasks
    } else if (taskInfo?.type === 'classification') {
      baseRate = 350; // Faster for simpler classification tasks
    }
    
    // Apply quality mode multipliers
    const modeMultiplier = {
      'speed': 0.4,    // Much faster but lower quality
      'balanced': 1.0, // Standard rate
      'quality': 2.2   // Slower but higher quality
    }[qualityMode] || 1;
    
    // Add overhead for setup and processing
    const baseTime = count / baseRate;
    const totalTime = (baseTime * modeMultiplier) + 2; // Add 2 minutes setup time
    
    return Math.round(Math.max(totalTime, 3)); // Minimum 3 minutes
  };
  
  const getRemainingTime = () => {
    if (!isCollecting || progress === 0) return null;
    
    const elapsedMinutes = Date.now() / 60000; // Rough elapsed time
    const estimatedTotal = getEstimatedTime();
    const remaining = Math.round(estimatedTotal * (100 - progress) / 100);
    
    return Math.max(remaining, 1); // At least 1 minute remaining
  };
  
  const formatTime = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes} minutes`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours} hours`;
  };

  // Data preview function with enhanced error handling
  const viewTaskData = async (taskJobId: string) => {
    setLoadingPreview(true);
    setPreviewJobId(taskJobId);
    setShowDataPreview(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication required. Please log in again.');
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/data-builder/job/${taskJobId}/data`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;
        
        if (response.status === 401) {
          errorMessage = 'Authentication expired. Please log in again.';
        } else if (response.status === 403) {
          errorMessage = 'Access denied. You may not have permission to view this data.';
        } else if (response.status === 404) {
          errorMessage = 'Data not found. The collection task may not exist or may have been deleted.';
        } else if (response.status === 500) {
          errorMessage = 'Server error. Please try again later.';
        } else if (response.status >= 400 && response.status < 500) {
          errorMessage = 'Invalid request. Please check your settings and try again.';
        }
        
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      const samples = data.data || [];
      setPreviewData(samples);
      
      if (samples.length === 0) {
        toast({
          title: "No data available",
          description: "This task doesn't have any collected data yet. Try starting a new collection.",
          variant: "default"
        });
      } else {
        toast({
          title: "Data loaded successfully",
          description: `Found ${data.total || samples.length} samples`,
        });
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      setPreviewData([]);
      
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
      
      toast({
        title: "Failed to load data",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setLoadingPreview(false);
    }
  };

  // Show empty state if no task or model is selected
  if (!taskInfo || !selectedModel) {
    return (
      <div className="p-8 space-y-6 max-w-6xl mx-auto">
          
          <EmptyState
            icon={FileText}
            title="No Task Defined"
            description="Please define your AI task and select a model first to proceed with data collection. Start by creating a task in the Task Builder."
            badge={{
              text: "Step 1 & 2 Required",
              variant: "outline"
            }}
            action={{
              label: "Go to Task Builder",
              onClick: () => navigate('/dashboard?section=chat'),
              variant: "default"
            }}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
              <div className="p-4 bg-white rounded-lg border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="h-4 w-4 text-gray-500" />
                  <span className="text-sm font-medium text-gray-700">Step 1: Define Task</span>
                </div>
                <p className="text-xs text-gray-600">Describe what you want your AI to do</p>
              </div>
              <div className="p-4 bg-white rounded-lg border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <Settings className="h-4 w-4 text-gray-500" />
                  <span className="text-sm font-medium text-gray-700">Step 2: Select Model</span>
                </div>
                <p className="text-xs text-gray-600">Choose the right model for your task</p>
              </div>
            </div>
          </EmptyState>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">

      {/* Task & Model Info */}
      <Card className="border-0 shadow-sm bg-gray-50/30">
        <CardContent className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <FileText className="h-5 w-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Task & Model Summary</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Task Name</p>
              <p className="font-medium">{taskInfo.task}</p>
            </div>
            <div>
              <p className="text-gray-500">Task Type</p>
              <p className="font-medium capitalize">{taskInfo.type}</p>
            </div>
            <div>
              <p className="text-gray-500">Language</p>
              <p className="font-medium capitalize">{taskInfo.language}</p>
            </div>
            <div>
              <p className="text-gray-500">Selected Model</p>
              <p className="font-medium">{selectedModel.name}</p>
            </div>
          </div>
          
          {taskInfo.description && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-sm font-medium text-gray-700 mb-2">Task Description:</p>
              <p className="text-sm text-gray-600">{taskInfo.description}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* AI Recommendation */}
      {recommendation && (
        <Card className="border-gray-200 bg-gray-50/30">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-gray-600" />
              AI Recommendation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert className="border-gray-200 bg-white">
              <Info className="h-4 w-4 text-gray-600" />
              <AlertDescription className="text-gray-700">
                {recommendation.reasoning}
              </AlertDescription>
            </Alert>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-500">Recommended Data</p>
                <p className="text-lg font-semibold">{recommendation.recommended_count.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Collection Time</p>
                <p className="text-lg font-semibold">{formatTime(recommendation.estimated_time_minutes)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Data Sources</p>
                <p className="text-lg font-semibold">
                  {Math.round(recommendation.collection_strategy.web * 100)}% Web
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Expected Result</p>
                <p className="text-lg font-semibold">{recommendation.expected_performance}</p>
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t">
              <p className="text-sm text-gray-600">
                Would you like to use these settings?
              </p>
              <div className="flex gap-3">
                <Button
                  variant={useRecommendation ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    setUseRecommendation(true);
                    setDataCount([recommendation.recommended_count]);
                    setQualityMode(recommendation.quality_mode);
                  }}
                  className="flex items-center gap-2"
                >
                  <CheckCircle className="h-4 w-4" />
                  Use Recommendation
                </Button>
                <Button
                  variant={!useRecommendation ? "default" : "outline"}
                  size="sm"
                  onClick={() => setUseRecommendation(false)}
                  className="flex items-center gap-2"
                >
                  <Edit className="h-4 w-4" />
                  Customize Settings
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Collection Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Collection Settings</CardTitle>
            {useRecommendation && recommendation && (
              <Badge variant="secondary" className="flex items-center gap-1">
                <CheckCircle className="h-3 w-3" />
                Using AI Recommendation
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          
          {/* Data Count Slider */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <Label>Training Data Amount</Label>
              <span className="text-lg font-semibold text-gray-900">
                {dataCount[0].toLocaleString()} samples
              </span>
            </div>
            <Slider
              value={dataCount}
              onValueChange={(value) => {
                setDataCount(value);
                if (useRecommendation && recommendation) {
                  setUseRecommendation(false);
                }
              }}
              min={1000}
              max={100000}
              step={1000}
              disabled={isCollecting}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>1K</span>
              <span>25K</span>
              <span>50K</span>
              <span>75K</span>
              <span>100K</span>
            </div>
          </div>

          {/* Quality Mode */}
          <div className="space-y-3">
            <Label>Quality Preference</Label>
            <RadioGroup
              value={qualityMode}
              onValueChange={(value) => {
                setQualityMode(value);
                if (useRecommendation && recommendation) {
                  setUseRecommendation(false);
                }
              }}
              disabled={isCollecting}
            >
              <div className="flex items-center space-x-3 p-3 rounded-lg border hover:bg-gray-50 cursor-pointer">
                <RadioGroupItem value="speed" id="speed" />
                <Label htmlFor="speed" className="flex-1 cursor-pointer">
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-gray-600" />
                    <span className="font-medium">Speed Priority</span>
                    <Badge variant="outline" className="ml-auto">5-20 min</Badge>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    Quick collection, mostly from web sources
                  </p>
                </Label>
              </div>

              <div className="flex items-center space-x-3 p-3 rounded-lg border hover:bg-gray-50 cursor-pointer">
                <RadioGroupItem value="balanced" id="balanced" />
                <Label htmlFor="balanced" className="flex-1 cursor-pointer">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-gray-600" />
                    <span className="font-medium">Balanced Mode</span>
                    <Badge variant="outline" className="ml-auto">30-60 min</Badge>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    Mix of web scraping and AI generation
                  </p>
                </Label>
              </div>

              <div className="flex items-center space-x-3 p-3 rounded-lg border hover:bg-gray-50 cursor-pointer">
                <RadioGroupItem value="quality" id="quality" />
                <Label htmlFor="quality" className="flex-1 cursor-pointer">
                  <div className="flex items-center gap-2">
                    <Brain className="h-4 w-4 text-gray-600" />
                    <span className="font-medium">Quality Priority</span>
                    <Badge variant="outline" className="ml-auto">1-3 hours</Badge>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    High-quality AI-generated data with careful curation
                  </p>
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* Enhanced Mode Toggle */}
          <div className="space-y-3">
            <div className="flex items-center justify-between p-4 rounded-lg border bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
              <div className="flex-1 space-y-1">
                <Label htmlFor="enhanced-mode" className="flex items-center gap-2 cursor-pointer">
                  <Sparkles className="h-4 w-4 text-purple-600" />
                  <span className="font-medium">Enhanced Collection Mode</span>
                  <Badge variant="secondary" className="ml-2">NEW</Badge>
                </Label>
                <p className="text-sm text-gray-600">
                  Process full articles without limits. Extract all relevant samples (may find 50+ samples per article).
                </p>
              </div>
              <Switch
                id="enhanced-mode"
                checked={enhancedMode}
                onCheckedChange={setEnhancedMode}
                disabled={isCollecting}
              />
            </div>
            {enhancedMode && (
              <Alert className="border-purple-200 bg-purple-50">
                <Sparkles className="h-4 w-4 text-purple-600" />
                <AlertDescription className="text-sm">
                  <strong>Enhanced mode active:</strong> Articles will be processed in full without truncation. 
                  This may take longer but ensures no valuable data is missed. Perfect for FAQ pages, documentation, and content-rich sources.
                </AlertDescription>
              </Alert>
            )}
          </div>

          {/* Estimated Time */}
          <div className="p-4 bg-gray-50 rounded-lg space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-gray-600" />
                <span className="font-medium">Estimated Time:</span>
              </div>
              <span className="text-lg font-semibold text-gray-900">
                {formatTime(getEstimatedTime())}
              </span>
            </div>
            
            {/* Time breakdown */}
            <div className="grid grid-cols-3 gap-4 text-xs text-gray-600 pt-2 border-t border-gray-200">
              <div>
                <p className="font-medium">Task Type</p>
                <p className="capitalize">{taskInfo?.type || 'Unknown'}</p>
              </div>
              <div>
                <p className="font-medium">Quality Mode</p>
                <p className="capitalize">{qualityMode}</p>
              </div>
              <div>
                <p className="font-medium">Sample Rate</p>
                <p>
                  {qualityMode === 'speed' ? '~400/min' : 
                   qualityMode === 'quality' ? '~150/min' : '~250/min'}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Collection Progress */}
      {isCollecting && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-lg">Collection Progress</CardTitle>
              {getRemainingTime() && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatTime(getRemainingTime()!)} remaining
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Overall Progress</span>
                <span className="font-medium">{progress}%</span>
              </div>
              <Progress value={progress} className="h-3" />
              <div className="flex justify-between text-xs text-gray-500">
                <span>{collectedCount.toLocaleString()} collected</span>
                <span>{dataCount[0].toLocaleString()} target</span>
              </div>
              {currentStep && (
                <div className="text-xs text-blue-600 mt-1">
                  Current step: {currentStep}
                </div>
              )}
              
              {/* Collection rate indicator */}
              <div className="flex justify-between text-xs text-gray-500 pt-1">
                <span>Collection rate:</span>
                <span>
                  {progress > 5 ? 
                    `~${Math.round(collectedCount / Math.max(progress / 100 * getEstimatedTime(), 1))} samples/min` : 
                    'Calculating...'
                  }
                </span>
              </div>
            </div>

            {/* Source Progress */}
            <div className="space-y-3">
              <p className="text-sm font-medium text-gray-700">Data Sources:</p>
              
              {Object.entries(sourcesProgress).map(([source, prog]) => (
                <div key={source} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      {source.includes('web') ? (
                        <Globe className="h-4 w-4 text-gray-600" />
                      ) : (
                        <Bot className="h-4 w-4 text-gray-600" />
                      )}
                      <span className="capitalize">{source}</span>
                    </div>
                    <span className="text-xs text-gray-500">{prog}%</span>
                  </div>
                  <Progress value={prog} className="h-2" />
                </div>
              ))}
            </div>

            <Alert>
              <AlertDescription>
                Data is being collected and processed. You can safely leave this page - collection will continue in the background.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4">
        {!isCollecting ? (
          <>
            <Button
              size="lg"
              onClick={startCollection}
              disabled={loadingRecommendation}
              className="flex-1 bg-gray-900 hover:bg-gray-800"
            >
              <Database className="h-5 w-5 mr-2" />
              Start Intelligent Collection
            </Button>
            
            {jobId && (
              <>
                <Button
                  size="lg"
                  variant="outline"
                  disabled={isCollecting}
                  onClick={() => {
                    if (!isCollecting && jobId) {
                      viewTaskData(jobId);
                    }
                  }}
                  title={isCollecting ? "Cannot view data while collection is in progress" : "View previous data"}
                >
                  <Eye className="h-5 w-5 mr-2" />
                  {isCollecting ? "Collection Active" : "View Previous Data"}
                </Button>
              </>
            )}
          </>
        ) : (
          <Button
            size="lg"
            variant="outline"
            className="flex-1"
            disabled={progress < 100}
            onClick={() => {
              if (progress >= 100 && jobId) {
                viewTaskData(jobId);
              }
            }}
            title={progress < 100 ? "Data collection must complete before viewing" : "View collected data"}
          >
            <Eye className="h-5 w-5 mr-2" />
            {progress < 100 ? "Collection in Progress..." : "View Collected Data"}
          </Button>
        )}
      </div>

      {/* Next Steps */}
      {jobId && (
        <Card className="mt-6 border border-gray-200">
          <CardHeader>
            <CardTitle className="text-lg">Next: Model Training</CardTitle>
            <CardDescription>
              Your data is ready for training. Select your model and start training your custom AI.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="space-y-1">
                <h4 className="font-semibold">Your Training Data is Ready</h4>
                <p className="text-sm text-gray-600">
                  Your collected data is structured and ready for model training. Proceed to select your model.
                </p>
              </div>
              <Button
                size="lg"
                disabled={isCollecting || progress < 100}
                onClick={() => {
                  if (progress >= 100 && !isCollecting) {
                    // Navigate directly to Training with collected data
                    navigate(`/dashboard?section=model-training&data_task=${jobId}`);
                  }
                }}
                className="bg-gray-900 hover:bg-gray-800 disabled:bg-gray-400"
                title={isCollecting || progress < 100 ? "Complete data collection before training" : "Start model training"}
              >
                <ArrowRight className="h-5 w-5 mr-2" />
                {isCollecting || progress < 100 ? "Collection Required" : "Start Training"}
              </Button>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <h5 className="font-medium text-gray-900">Ready for Training:</h5>
                <ul className="space-y-1 text-gray-600">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-gray-600" />
                    Clean and structure raw data
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-gray-600" />
                    Remove duplicates and noise
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-gray-600" />
                    Standardize data format
                  </li>
                </ul>
              </div>
              <div className="space-y-2">
                <h5 className="font-medium text-gray-900">Expected results:</h5>
                <ul className="space-y-1 text-gray-600">
                  <li className="flex items-center gap-2">
                    <TrendingUp className="h-3 w-3 text-gray-600" />
                    95%+ data quality score
                  </li>
                  <li className="flex items-center gap-2">
                    <TrendingUp className="h-3 w-3 text-gray-600" />
                    Training-ready format
                  </li>
                  <li className="flex items-center gap-2">
                    <TrendingUp className="h-3 w-3 text-gray-600" />
                    Optimized for your model
                  </li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data Preview Dialog */}
      <Dialog open={showDataPreview} onOpenChange={setShowDataPreview}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Collected Data Preview</DialogTitle>
            <DialogDescription>
              {previewJobId ? `Viewing data for task: ${previewJobId}` : "Preview of collected data"}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {loadingPreview ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                <span>Loading data...</span>
              </div>
            ) : previewData.length > 0 ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    {previewData.length} samples loaded
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const jsonData = JSON.stringify(previewData, null, 2);
                      navigator.clipboard.writeText(jsonData);
                      toast({
                        title: "Copied",
                        description: "Data copied to clipboard",
                      });
                    }}
                  >
                    Copy JSON
                  </Button>
                </div>
                
                <div className="max-h-96 overflow-auto space-y-3">
                  {previewData.slice(0, 10).map((item, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg border">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-gray-500">
                          Sample #{index + 1}
                        </span>
                        {item.source && (
                          <Badge variant="outline" className="text-xs">
                            {item.source}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-3">
                        {item.content || item.text || JSON.stringify(item)}
                      </p>
                      {item.url && (
                        <p className="text-xs text-gray-500 mt-1 truncate">
                          Source: {item.url}
                        </p>
                      )}
                    </div>
                  ))}
                  
                  {previewData.length > 10 && (
                    <div className="text-center py-2">
                      <p className="text-sm text-gray-500">
                        ... and {previewData.length - 10} more samples
                      </p>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <Database className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-500">No data found for this task</p>
              </div>
            )}
          </div>
          
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setShowDataPreview(false)}
            >
              Close
            </Button>
            {previewData.length > 0 && (
              <Button
                onClick={() => {
                  const jsonData = JSON.stringify(previewData, null, 2);
                  const blob = new Blob([jsonData], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `collected-data-${previewJobId || Date.now()}.json`;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  URL.revokeObjectURL(url);
                  
                  toast({
                    title: "Downloaded",
                    description: "Data saved to downloads folder",
                  });
                }}
              >
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* JSON Dialog */}
      <Dialog open={isJsonDialogOpen} onOpenChange={setIsJsonDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Data Results</DialogTitle>
            <DialogDescription>
              Collected or processed data results (JSON format)
            </DialogDescription>
          </DialogHeader>
          <div className="overflow-auto">
            <pre className="bg-muted p-4 rounded-lg text-sm">
              <code>{jsonData}</code>
            </pre>
          </div>
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => {
                navigator.clipboard.writeText(jsonData);
                toast({
                  title: "Copied",
                  description: "JSON data copied to clipboard",
                });
              }}
            >
              Copy
            </Button>
            <Button
              onClick={() => {
                const blob = new Blob([jsonData], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `data-${Date.now()}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
              }}
            >
              Download
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DataBuilder;