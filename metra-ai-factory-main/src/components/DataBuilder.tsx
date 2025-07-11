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
            domain: task.domain || 'general'
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
            domain: finalizedTask.domain || 'general'
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
  
  // Collection settings
  const [dataCount, setDataCount] = useState<number[]>([10000]);
  const [qualityMode, setQualityMode] = useState('balanced');
  
  // Collection progress
  const [isCollecting, setIsCollecting] = useState(false);
  const [jobId, setJobId] = useState<string | null>('demo-task-123'); // Set a demo task ID to show DFE button
  const [progress, setProgress] = useState(0);
  const [collectedCount, setCollectedCount] = useState(0);
  const [sourcesProgress, setSourcesProgress] = useState<Record<string, number>>({});

  const [selectedTask, setSelectedTask] = useState<CollectionTask | null>(null);
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());
  const [isJsonDialogOpen, setIsJsonDialogOpen] = useState(false);
  const [jsonData, setJsonData] = useState<string>('');
  
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
    if (!taskInfo || !selectedModel) return;
    
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
                  onClick={() => navigate(`/data-viewer/${jobId}`)}
                >
                  <Eye className="h-5 w-5 mr-2" />
                  View Previous Data
                </Button>
              </>
            )}
          </>
        ) : (
          <Button
            size="lg"
            variant="outline"
            className="flex-1"
            onClick={() => navigate(`/data-viewer/${jobId}`)}
          >
            <Eye className="h-5 w-5 mr-2" />
            View Collected Data
          </Button>
        )}
      </div>

      {/* Next Steps */}
      {jobId && (
        <Card className="mt-6 border border-gray-200">
          <CardHeader>
            <CardTitle className="text-lg">Next: Data Processing & Enhancement</CardTitle>
            <CardDescription>
              Your data has been collected. Now enhance it for training with our Data Fusion Engine (DFE).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="space-y-1">
                <h4 className="font-semibold">Metra Data Fusion Engine</h4>
                <p className="text-sm text-gray-600">
                  Automatically clean, structure, and enhance your collected data for optimal training results.
                </p>
              </div>
              <Button
                size="lg"
                onClick={() => {
                  // Navigate to DFE with collected data
                  navigate(`/dashboard?section=data-engine&data_task=${jobId}`);
                }}
                className="bg-gray-900 hover:bg-gray-800"
              >
                <ArrowRight className="h-5 w-5 mr-2" />
                Process Data
              </Button>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <h5 className="font-medium text-gray-900">What DFE will do:</h5>
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