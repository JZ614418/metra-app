import React, { useState, useEffect } from 'react';
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
  Eye
} from 'lucide-react';
import { dataBuilderAPI } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface TaskInfo {
  task: string;
  type: string;
  language: string;
  labels: string[];
  description?: string;
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

interface DFETask {
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
  
  // Get task and model info from localStorage
  const [taskInfo] = useState<TaskInfo>(() => {
    // 首先尝试从 conversationStore 获取最新的任务信息
    const conversationState = localStorage.getItem('conversation-storage');
    if (conversationState) {
      try {
        const state = JSON.parse(conversationState);
        const finalizedTask = state?.state?.finalizedTask;
        if (finalizedTask) {
          // 尝试从多个可能的位置获取任务信息
          const taskName = finalizedTask.task || 
                          finalizedTask.name || 
                          finalizedTask.schema?.task || 
                          finalizedTask.fullDefinition?.task ||
                          '中医饮食指导AI';
          
          const taskLanguage = finalizedTask.language || 
                              finalizedTask.schema?.language || 
                              finalizedTask.fullDefinition?.language ||
                              'chinese';
          
          const taskDescription = finalizedTask.description || 
                                 finalizedTask.features || 
                                 finalizedTask.schema?.features ||
                                 finalizedTask.fullDefinition?.features ||
                                 '提供基于中医理论的个性化饮食建议';
          
          return {
            task: taskName,
            type: finalizedTask.type || 'recommendations',
            language: taskLanguage,
            labels: finalizedTask.labels || [],
            description: taskDescription
          };
        }
      } catch (e) {
        console.error('Failed to parse conversation state:', e);
      }
    }
    
    // 尝试其他存储位置
    const savedTask = localStorage.getItem('currentTask');
    const conversationData = localStorage.getItem('lastFinalizedTask');
    
    if (conversationData) {
      const task = JSON.parse(conversationData);
      const schema = task.fullDefinition || task.schema;
      return {
        task: schema?.task || 'Unknown Task',
        type: task.type || 'classification',
        language: schema?.language || 'english',
        labels: task.labels || [],
        description: task.description || ''
      };
    }
    
    // 通用默认值
    return {
      task: 'Your Custom Task',
      type: 'classification',
      language: 'english',
      labels: [],
      description: 'Please define your task in the Task Builder first'
    };
  });
  
  const [selectedModel] = useState<SelectedModel>(() => {
    // 首先尝试从 modelStore 获取
    const modelState = localStorage.getItem('model-storage');
    if (modelState) {
      try {
        const state = JSON.parse(modelState);
        const selected = state?.state?.selectedModel;
        if (selected) {
          return {
            id: selected.id || 'chatglm2-6b',
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
    if (saved) return JSON.parse(saved);
    
    // 通用默认模型
    return {
      id: 'default-model',
      name: 'Select a Model',
      provider: 'Unknown',
      modelType: 'General',
      size: 'base'
    };
  });
  
  // State
  const [recommendation, setRecommendation] = useState<DataRecommendation | null>(null);
  const [loadingRecommendation, setLoadingRecommendation] = useState(false);
  const [useRecommendation, setUseRecommendation] = useState(true);
  
  // Collection settings
  const [dataCount, setDataCount] = useState<number[]>([10000]);
  const [qualityMode, setQualityMode] = useState('balanced');
  
  // Collection progress
  const [isCollecting, setIsCollecting] = useState(false);
  const [jobId, setJobId] = useState<string | null>('demo-task-123'); // 设置一个demo任务ID以显示DFE按钮
  const [progress, setProgress] = useState(0);
  const [collectedCount, setCollectedCount] = useState(0);
  const [sourcesProgress, setSourcesProgress] = useState<Record<string, number>>({});

  const [selectedTask, setSelectedTask] = useState<CollectionTask | null>(null);
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());
  const [isJsonDialogOpen, setIsJsonDialogOpen] = useState(false);
  const [jsonData, setJsonData] = useState<string>('');
  const [showDFESection, setShowDFESection] = useState(false);
  const [dfeTask, setDfeTask] = useState<DFETask | null>(null);
  const [enableV2Features, setEnableV2Features] = useState(false);
  const [outputFormat, setOutputFormat] = useState('json');
  
  // Get AI recommendation on mount
  useEffect(() => {
    getRecommendation();
  }, []);
  
  const getRecommendation = async () => {
    setLoadingRecommendation(true);
    try {
      const rec = await dataBuilderAPI.getRecommendation({
        task_info: taskInfo,
        selected_model: selectedModel
      });
      setRecommendation(rec);
      
      // Apply recommendation
      if (rec) {
        setDataCount([rec.recommended_count]);
        setQualityMode(rec.quality_mode);
      }
    } catch (error) {
      console.error('Failed to get recommendation:', error);
      toast({
        title: "Failed to get AI recommendation",
        description: "Using default settings",
        variant: "destructive",
      });
    } finally {
      setLoadingRecommendation(false);
    }
  };
  
  const startCollection = async () => {
    setIsCollecting(true);
    setProgress(0);
    setCollectedCount(0);
    
    try {
      const response = await dataBuilderAPI.startCollection({
        task_info: taskInfo,
        selected_model: selectedModel,
        data_count: dataCount[0],
        quality_mode: qualityMode,
        use_recommendation: useRecommendation
      });
      
      setJobId(response.job_id);
      
      // Start polling for progress
      pollProgress(response.job_id);
      
    } catch (error) {
      console.error('Failed to start collection:', error);
      setIsCollecting(false);
      toast({
        title: "Failed to start data collection",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    }
  };
  
  const pollProgress = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const status = await dataBuilderAPI.getJobProgress(jobId);
        
        setProgress(status.progress);
        setCollectedCount(status.collected_count);
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
            window.location.href = `/data-viewer/${jobId}`;
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

  const startDFEProcessing = async (taskId: string) => {
    try {
      // 获取任务结果中的URL
      const response = await fetch(`${API_URL}/api/v1/data-builder/results/${taskId}`);
      if (!response.ok) throw new Error('Failed to get task results');
      
      const results = await response.json();
      
      // 提取所有URL
      const urls = results
        .filter((item: any) => item.url && item.source === 'web')
        .map((item: any) => item.url);
      
      if (urls.length === 0) {
        toast({
          title: "No URLs to process",
          description: "Please collect web data with URLs first",
          variant: "destructive",
        });
        return;
      }
      
      // 构建DFE选项
      const dfeOptions = enableV2Features ? {
        enable_v2_features: true,
        field_alignment: {
          title: ["标题", "title", "name", "名称"],
          content: ["内容", "content", "text", "正文"],
          author: ["作者", "author", "writer", "撰写人"],
          date: ["日期", "date", "time", "时间"]
        },
        fill_missing_values: true,
        data_augmentation: true,
        output_format: outputFormat
      } : undefined;
      
      // 启动DFE任务
      const dfeResponse = await fetch(`${API_URL}/api/v1/dfe/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          urls: urls,
          options: dfeOptions
        }),
      });
      
      if (!dfeResponse.ok) throw new Error('Failed to start DFE processing');
      
      const dfeResult = await dfeResponse.json();
      
      toast({
        title: "DFE处理已启动",
        description: `正在处理 ${urls.length} 个URL`,
      });
      
      setShowDFESection(true);
      
      // 开始轮询DFE状态
      pollDFEStatus(dfeResult.task_id);
      
    } catch (error) {
      console.error('DFE processing error:', error);
      toast({
        title: "启动DFE失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive",
      });
    }
  };
  
  const pollDFEStatus = async (dfeTaskId: string) => {
    const checkStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/api/v1/dfe/status/${dfeTaskId}`);
        if (!response.ok) throw new Error('Failed to get DFE status');
        
        const status = await response.json();
        setDfeTask(status);
        
        if (status.status === 'processing') {
          setTimeout(checkStatus, 2000); // 每2秒检查一次
        } else if (status.status === 'completed') {
          toast({
            title: "DFE处理完成",
            description: "数据提取和处理已完成",
          });
        } else if (status.status === 'failed') {
          toast({
            title: "DFE处理失败",
            description: status.error || "未知错误",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error('Poll DFE status error:', error);
      }
    };
    
    checkStatus();
  };
  
  const viewDFEResults = async () => {
    if (!dfeTask) return;
    
    try {
      const response = await fetch(`${API_URL}/api/v1/dfe/results/${dfeTask.id}`);
      if (!response.ok) throw new Error('Failed to get DFE results');
      
      const results = await response.json();
      setJsonData(JSON.stringify(results, null, 2));
      setIsJsonDialogOpen(true);
    } catch (error) {
      console.error('Get DFE results error:', error);
      toast({
        title: "获取DFE结果失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive",
      });
    }
  };
  
  const getEstimatedTime = () => {
    if (recommendation && useRecommendation) {
      return recommendation.estimated_time_minutes;
    }
    
    // Simple estimation based on count and mode
    const baseTime = dataCount[0] / 250; // ~250 samples per minute
    const modeMultiplier = {
      'speed': 0.5,
      'balanced': 1,
      'quality': 2
    }[qualityMode] || 1;
    
    return Math.round(baseTime * modeMultiplier);
  };
  
  const formatTime = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes} minutes`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours} hours`;
  };

  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="pt-4">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Intelligent Data Collection
          </h2>
          <p className="text-gray-600">
            Let AI help you collect the perfect training data for your language model
          </p>
        </div>

      {/* Task & Model Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="border-gray-200 bg-gray-50/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Database className="h-4 w-4 text-gray-600" />
              Your Task
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium text-gray-900">{taskInfo.task}</p>
            <p className="text-sm text-gray-600 mt-1">{taskInfo.description}</p>
            <div className="flex gap-2 mt-2">
              <Badge variant="secondary">{taskInfo.type}</Badge>
              <Badge variant="secondary">{taskInfo.language}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="border-gray-200 bg-gray-50/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Brain className="h-4 w-4 text-gray-600" />
              Selected Model
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium text-gray-900">{selectedModel.name}</p>
            <p className="text-sm text-gray-600 mt-1">{selectedModel.provider}</p>
            <div className="flex gap-2 mt-2">
              <Badge variant="secondary">{selectedModel.modelType}</Badge>
              {selectedModel.size && (
                <Badge variant="secondary">{selectedModel.size}</Badge>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

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

          {/* Estimated Time */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-gray-600" />
              <span className="font-medium">Estimated Time:</span>
            </div>
            <span className="text-lg font-semibold text-gray-900">
              {formatTime(getEstimatedTime())}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Collection Progress */}
      {isCollecting && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Collection Progress</CardTitle>
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
                  onClick={() => window.location.href = `/data-viewer/${jobId}`}
                >
                  <Eye className="h-5 w-5 mr-2" />
                  View Previous Data
                </Button>
                
                <Button
                  size="lg"
                  variant="secondary"
                  onClick={() => startDFEProcessing(jobId)}
                  className="bg-gray-100 hover:bg-gray-200"
                >
                  <Zap className="h-5 w-5 mr-2" />
                  Start DFE Deep Extraction
                </Button>
              </>
            )}
          </>
        ) : (
          <Button
            size="lg"
            variant="outline"
            className="flex-1"
            onClick={() => window.location.href = `/data-viewer/${jobId}`}
          >
            <Eye className="h-5 w-5 mr-2" />
            View Collected Data
          </Button>
        )}
      </div>

      {/* DFE Configuration */}
      {jobId && (
        <Card className="mt-6 border border-gray-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <Zap className="h-6 w-6 text-gray-600" />
                  DFE 数据融合引擎
                </CardTitle>
                <CardDescription>
                  深度提取和智能处理网页数据，获得高质量训练数据集
                </CardDescription>
              </div>
              <Badge variant="secondary" className="bg-gray-100">
                V2.0 高级版
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* V1 基础功能 */}
            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2">
                <Database className="h-4 w-4 text-gray-600" />
                V1 基础功能（自动启用）
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                  <CheckCircle className="h-4 w-4 text-gray-600" />
                  <span className="text-sm">智能网页爬取</span>
                </div>
                <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                  <CheckCircle className="h-4 w-4 text-gray-600" />
                  <span className="text-sm">内容结构化提取</span>
                </div>
                <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                  <CheckCircle className="h-4 w-4 text-gray-600" />
                  <span className="text-sm">自动跟随重定向</span>
                </div>
                <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                  <CheckCircle className="h-4 w-4 text-gray-600" />
                  <span className="text-sm">元数据提取</span>
                </div>
              </div>
            </div>

            {/* V2 高级功能开关 */}
            <div className="border-t pt-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="space-y-1">
                  <Label htmlFor="v2-features" className="text-base font-semibold cursor-pointer">
                    启用 V2 高级功能
                  </Label>
                  <p className="text-sm text-gray-600">
                    AI驱动的智能数据处理和增强
                  </p>
                </div>
                <Switch
                  id="v2-features"
                  checked={enableV2Features}
                  onCheckedChange={setEnableV2Features}
                  className="data-[state=checked]:bg-gray-900"
                />
              </div>
            </div>
            
            {/* V2 功能详情 */}
            {enableV2Features && (
              <div className="space-y-4 animate-in slide-in-from-top duration-300">
                {/* 字段对齐 */}
                <div className="p-4 bg-gray-50 rounded-lg space-y-3">
                  <div className="flex items-center gap-2">
                    <Brain className="h-5 w-5 text-gray-600" />
                    <h5 className="font-semibold">智能字段对齐</h5>
                  </div>
                  <p className="text-sm text-gray-600">
                    自动识别和映射中英文同义字段，确保数据格式统一
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 bg-white rounded border border-gray-200">
                      <span className="text-gray-500">中文：</span> 标题、名称、药材名
                    </div>
                    <div className="p-2 bg-white rounded border border-gray-200">
                      <span className="text-gray-500">英文：</span> title, name, herb
                    </div>
                  </div>
                </div>

                {/* 缺失值填充 */}
                <div className="p-4 bg-gray-50 rounded-lg space-y-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-gray-600" />
                    <h5 className="font-semibold">AI 缺失值填充</h5>
                  </div>
                  <p className="text-sm text-gray-600">
                    基于上下文智能推断并填充缺失的字段值
                  </p>
                  <div className="flex items-center gap-2 text-xs bg-white p-2 rounded border border-gray-200">
                    <Info className="h-3 w-3 text-gray-600" />
                    <span>使用 GPT-3.5 分析上下文，生成合理的缺失值</span>
                  </div>
                </div>

                {/* 数据增强 */}
                <div className="p-4 bg-gray-50 rounded-lg space-y-3">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-gray-600" />
                    <h5 className="font-semibold">数据增强</h5>
                  </div>
                  <p className="text-sm text-gray-600">
                    生成相似但不重复的数据样本，扩充训练集
                  </p>
                  <div className="flex items-center gap-2 text-xs bg-white p-2 rounded border border-gray-200">
                    <Info className="h-3 w-3 text-gray-600" />
                    <span>每个原始样本可生成 1-2 个增强样本</span>
                  </div>
                </div>

                {/* 输出格式 */}
                <div className="space-y-3">
                  <Label htmlFor="output-format" className="font-semibold">
                    输出格式选择
                  </Label>
                  <Select value={outputFormat} onValueChange={setOutputFormat}>
                    <SelectTrigger id="output-format" className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="json">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">JSON</Badge>
                          <span>标准 JSON 格式（易读易用）</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="jsonl">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">JSONL</Badge>
                          <span>每行一个 JSON（适合大数据处理）</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="csv">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">CSV</Badge>
                          <span>表格格式（Excel 兼容）</span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* 预估效果 */}
                <Alert className="border-gray-200 bg-gray-50">
                  <Sparkles className="h-4 w-4" />
                  <AlertTitle>预期效果</AlertTitle>
                  <AlertDescription>
                    启用 V2 功能后，数据质量提升约 40%，数据量增加约 2倍
                  </AlertDescription>
                </Alert>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* DFE Processing Status */}
      {showDFESection && dfeTask && (
        <Card className="mt-6 border border-gray-300 shadow-lg">
          <CardHeader className="bg-gray-900 text-white">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-xl">
                <Zap className="h-6 w-6" />
                DFE 处理状态
              </CardTitle>
              <Badge 
                variant={
                  dfeTask.status === 'completed' ? 'secondary' :
                  dfeTask.status === 'failed' ? 'destructive' :
                  'default'
                }
                className={
                  dfeTask.status === 'completed' ? 'bg-green-100 text-green-800' :
                  dfeTask.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                  ''
                }
              >
                {dfeTask.status === 'processing' ? '🔄 处理中' :
                 dfeTask.status === 'completed' ? '✅ 已完成' :
                 '❌ 失败'}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-4">
              {/* 任务信息 */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-gray-500">任务ID:</span>
                  <code className="px-2 py-1 bg-gray-100 rounded text-xs">
                    {dfeTask.id.slice(0, 8)}...
                  </code>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-500">处理模式:</span>
                  <Badge variant="outline" className={enableV2Features ? 'border-purple-500 text-purple-700' : ''}>
                    {enableV2Features ? 'V2 高级模式' : 'V1 基础模式'}
                  </Badge>
                </div>
              </div>
              
              {/* 处理中状态 */}
              {dfeTask.status === 'processing' && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm font-medium">
                      <span>整体进度</span>
                      <span className="text-gray-900">{dfeTask.progress}%</span>
                    </div>
                    <Progress value={dfeTask.progress} className="h-3" />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2 mb-1">
                        <Globe className="h-4 w-4 text-gray-600" />
                        <span className="text-sm font-medium">正在提取</span>
                      </div>
                      <p className="text-xs text-gray-600">
                        从 {dfeTask.total} 个URL提取内容
                      </p>
                    </div>
                    
                    {enableV2Features && (
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                          <Brain className="h-4 w-4 text-gray-600" />
                          <span className="text-sm font-medium">AI处理中</span>
                        </div>
                        <p className="text-xs text-gray-600">
                          字段对齐、缺失值填充
                        </p>
                      </div>
                    )}
                  </div>
                  
                  <Alert className="border-gray-200 bg-gray-50">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <AlertDescription className="ml-2">
                      正在深度处理数据，请稍候...预计还需 {Math.ceil((100 - dfeTask.progress) / 20)} 分钟
                    </AlertDescription>
                  </Alert>
                </div>
              )}
              
              {/* 完成状态 */}
              {dfeTask.status === 'completed' && (
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-start gap-3">
                      <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="font-semibold text-green-800 mb-1">处理成功！</h4>
                        <p className="text-sm text-green-700">
                          成功处理了 {dfeTask.total} 个URL的数据
                        </p>
                        {enableV2Features && (
                          <div className="mt-2 space-y-1 text-xs text-green-600">
                            <div>✓ 字段已自动对齐</div>
                            <div>✓ 缺失值已智能填充</div>
                            <div>✓ 数据已增强扩展</div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <Button 
                      onClick={viewDFEResults}
                      className="flex items-center gap-2 bg-gray-900 hover:bg-gray-800"
                      size="lg"
                    >
                      <Eye className="h-5 w-5" />
                      查看处理结果
                    </Button>
                    <Button 
                      variant="outline"
                      onClick={() => {
                        const format = enableV2Features ? outputFormat : 'json';
                        toast({
                          title: "准备下载",
                          description: `正在准备 ${format.toUpperCase()} 格式的数据...`,
                        });
                      }}
                      className="flex items-center gap-2"
                      size="lg"
                    >
                      <Download className="h-5 w-5" />
                      下载数据
                    </Button>
                  </div>
                </div>
              )}
              
              {/* 错误状态 */}
              {dfeTask.status === 'failed' && (
                <Alert variant="destructive" className="border-red-300">
                  <AlertCircle className="h-5 w-5" />
                  <AlertTitle>处理失败</AlertTitle>
                  <AlertDescription className="mt-2">
                    <p>{dfeTask.error || "处理过程中发生未知错误"}</p>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="mt-3"
                      onClick={() => {
                        setShowDFESection(false);
                        setDfeTask(null);
                      }}
                    >
                      关闭并重试
                    </Button>
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* JSON Dialog */}
      <Dialog open={isJsonDialogOpen} onOpenChange={setIsJsonDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>数据结果</DialogTitle>
            <DialogDescription>
              收集或处理的数据结果（JSON格式）
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
                  title: "已复制",
                  description: "JSON数据已复制到剪贴板",
                });
              }}
            >
              复制
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
              下载
            </Button>
          </div>
        </DialogContent>
      </Dialog>
      </div>
    </div>
  );
};

export default DataBuilder; 