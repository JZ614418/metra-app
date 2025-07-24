import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { 
  Brain,
  Zap,
  Clock,
  DollarSign,
  Play,
  CheckCircle,
  AlertCircle,
  Loader2,
  TestTube,
  Rocket,
  Sparkles,
  TrendingUp,
  Info,
  ArrowRight,
  MessageSquare,
  Activity,
  FileText,
  Database
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useLocation } from 'react-router-dom';
import { useConversationStore } from '@/stores/conversationStore';
import { EmptyState } from '@/components/ui/empty-state';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface TrainingLog {
  timestamp: string;
  message: string;
}

const ModelBuilder = () => {
  const { toast } = useToast();
  const location = useLocation();
  const { lastFinalizedTask } = useConversationStore();
  
  // Get data from URL params (passed from DataBuilder) or localStorage fallback
  const params = new URLSearchParams(location.search);
  const dataTaskId = params.get('data_task') || localStorage.getItem('dataTaskId');
  const collectedCount = params.get('collected_count') || localStorage.getItem('collectedCount');
  
  // Training state
  const [trainingMode, setTrainingMode] = useState('standard');
  const [isTraining, setIsTraining] = useState(false);
  const [trainingJobId, setTrainingJobId] = useState<string | null>(null);
  const [trainingStatus, setTrainingStatus] = useState<string>('');
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [trainingLogs, setTrainingLogs] = useState<TrainingLog[]>([]);
  const [trainingComplete, setTrainingComplete] = useState(false);
  const [trainedModelId, setTrainedModelId] = useState<string | null>(null);
  
  // Test dialog state
  const [showTestDialog, setShowTestDialog] = useState(false);
  const [testInput, setTestInput] = useState('');
  const [testOutput, setTestOutput] = useState('');
  const [isTestingModel, setIsTestingModel] = useState(false);
  
  // Cost estimation
  const [estimatedCost, setEstimatedCost] = useState<number>(0);
  const [estimatedTime, setEstimatedTime] = useState<number>(0);
  
  // Get task info from lastFinalizedTask
  const taskName = lastFinalizedTask?.name || 'Custom AI Model';
  const taskDescription = lastFinalizedTask?.description || '';
  // Extract base model from the schema or use the recommended model from model selection
  const baseModel = (() => {
    // Check if there's a selected model in localStorage
    const selectedModelStr = localStorage.getItem('selectedModel');
    if (selectedModelStr) {
      try {
        const selectedModel = JSON.parse(selectedModelStr);
        return selectedModel.id || 'gpt-3.5-turbo';
      } catch (e) {
        console.error('Failed to parse selected model:', e);
      }
    }
    // Fallback to default
    return 'gpt-3.5-turbo';
  })();
  const dataCount = parseInt(processedCount || '0');

  useEffect(() => {
    // Estimate cost when component loads
    estimateTrainingCost();
  }, [dataCount, baseModel, trainingMode]);

  const estimateTrainingCost = async () => {
    try {
      const response = await fetch(
        `${API_URL}/training/estimate-cost?data_count=${dataCount}&base_model=${baseModel}&training_mode=${trainingMode}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setEstimatedCost(data.estimated_cost_usd);
        setEstimatedTime(data.estimated_time_minutes);
      }
    } catch (error) {
      console.error('Error estimating cost:', error);
    }
  };

  const startTraining = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      toast({
        title: "Authentication required",
        description: "Please log in to start training",
        variant: "destructive"
      });
      return;
    }

    setIsTraining(true);
    setTrainingProgress(0);
    setTrainingLogs([]);
    
    try {
      const response = await fetch(`${API_URL}/training/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          task_name: taskName,
          task_description: taskDescription,
          base_model: baseModel,
          data_builder_job_id: dataTaskId || 'demo',
          training_mode: trainingMode
        })
      });

      if (!response.ok) throw new Error('Failed to start training');
      
      const result = await response.json();
      setTrainingJobId(result.job_id);
      
      toast({
        title: "Training Started!",
        description: `Estimated time: ${result.estimated_time}`,
      });
      
      // Start polling for status
      pollTrainingStatus(result.job_id);
      
    } catch (error) {
      console.error('Training error:', error);
      setIsTraining(false);
      toast({
        title: "Training Failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive"
      });
    }
  };

  const pollTrainingStatus = async (jobId: string) => {
    const token = localStorage.getItem('token');
    
    const checkStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/training/status/${jobId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) throw new Error('Failed to get status');
        
        const status = await response.json();
        
        setTrainingStatus(status.status);
        setTrainingProgress(status.progress);
        
        // Update logs
        if (status.logs && status.logs.length > 0) {
          setTrainingLogs(status.logs);
        }
        
        if (status.status === 'training' || status.status === 'preparing') {
          // Continue polling
          setTimeout(checkStatus, 2000);
        } else if (status.status === 'completed') {
          setIsTraining(false);
          setTrainingComplete(true);
          setTrainedModelId(jobId);
          
          toast({
            title: "Training Complete!",
            description: "Your model is ready to use",
          });
        } else if (status.status === 'failed') {
          setIsTraining(false);
          toast({
            title: "Training Failed",
            description: status.error || "Unknown error occurred",
            variant: "destructive"
          });
        }
      } catch (error) {
        console.error('Poll status error:', error);
      }
    };
    
    checkStatus();
  };

  const testModel = async () => {
    if (!trainingJobId || !testInput.trim()) return;
    
    const token = localStorage.getItem('token');
    setIsTestingModel(true);
    setTestOutput('');
    
    try {
      const response = await fetch(`${API_URL}/training/test/${trainingJobId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          test_input: testInput
        })
      });
      
      if (!response.ok) throw new Error('Failed to test model');
      
      const result = await response.json();
      setTestOutput(result.output);
      
    } catch (error) {
      console.error('Test error:', error);
      toast({
        title: "Test Failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive"
      });
    } finally {
      setIsTestingModel(false);
    }
  };

  const proceedToDeployment = () => {
    window.location.href = `/dashboard?section=deployed-models&model_id=${trainedModelId}&task_name=${encodeURIComponent(taskName)}`;
  };

  // Show empty state if no processed data is available
  if (!dataTaskId && dataCount === 0) {
    return (
      <div className="p-8 space-y-6 max-w-6xl mx-auto">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Model Training Center
          </h1>
          <p className="text-gray-600">
            Train your custom AI model with processed training data
          </p>
        </div>
        
        <EmptyState
          icon={Rocket}
          title="No Training Data Available"
          description="You need processed training data before you can start model training. Please complete the data collection and processing steps first."
          badge={{
            text: "Steps 1-3 Required",
            variant: "outline"
          }}
          action={{
            label: "Go to Data Builder",
            onClick: () => window.location.href = '/dashboard?section=data-builder',
            variant: "default"
          }}
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div className="p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Step 1: Define Task</span>
              </div>
              <p className="text-xs text-gray-600">Create your AI task definition</p>
            </div>
            <div className="p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Step 2: Select Model</span>
              </div>
              <p className="text-xs text-gray-600">Choose your base model</p>
            </div>
            <div className="p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <Database className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Step 3: Process Data</span>
              </div>
              <p className="text-xs text-gray-600">Collect and enhance training data</p>
            </div>
          </div>
        </EmptyState>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">

      {/* Task Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Training Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-sm text-gray-500">Task Name</Label>
              <p className="font-semibold">{taskName}</p>
            </div>
            <div>
              <Label className="text-sm text-gray-500">Base Model</Label>
              <p className="font-semibold flex items-center gap-2">
                {baseModel}
                <Badge variant="secondary" className="text-xs">Recommended</Badge>
              </p>
            </div>
          </div>
          
          {taskDescription && (
            <div>
              <Label className="text-sm text-gray-500">Description</Label>
              <p className="text-sm mt-1">{taskDescription}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Training Options */}
      <Card>
        <CardHeader>
          <CardTitle>Training Mode</CardTitle>
          <CardDescription>
            Choose how thoroughly you want to train your model
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RadioGroup value={trainingMode} onValueChange={setTrainingMode}>
            <div className="grid grid-cols-3 gap-4">
              <div className={`relative rounded-lg border p-4 cursor-pointer transition-all ${
                trainingMode === 'light' ? 'border-gray-900 bg-gray-50' : 'border-gray-200'
              }`}>
                <RadioGroupItem value="light" id="light" className="absolute top-4 right-4" />
                <Label htmlFor="light" className="cursor-pointer">
                  <div className="flex items-center gap-2 mb-2">
                    <Zap className="h-5 w-5 text-gray-600" />
                    <span className="font-semibold">Light Training</span>
                  </div>
                  <p className="text-sm text-gray-600">Quick test run</p>
                  <p className="text-xs text-gray-500 mt-1">~{Math.round(estimatedTime * 0.5)} minutes</p>
                </Label>
              </div>

              <div className={`relative rounded-lg border p-4 cursor-pointer transition-all ${
                trainingMode === 'standard' ? 'border-gray-900 bg-gray-50' : 'border-gray-200'
              }`}>
                <RadioGroupItem value="standard" id="standard" className="absolute top-4 right-4" />
                <Label htmlFor="standard" className="cursor-pointer">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="h-5 w-5 text-gray-600" />
                    <span className="font-semibold">Standard</span>
                    <Badge variant="secondary" className="text-xs">Recommended</Badge>
                  </div>
                  <p className="text-sm text-gray-600">Balanced quality</p>
                  <p className="text-xs text-gray-500 mt-1">~{estimatedTime} minutes</p>
                </Label>
              </div>

              <div className={`relative rounded-lg border p-4 cursor-pointer transition-all ${
                trainingMode === 'deep' ? 'border-gray-900 bg-gray-50' : 'border-gray-200'
              }`}>
                <RadioGroupItem value="deep" id="deep" className="absolute top-4 right-4" />
                <Label htmlFor="deep" className="cursor-pointer">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="h-5 w-5 text-gray-600" />
                    <span className="font-semibold">Deep Training</span>
                  </div>
                  <p className="text-sm text-gray-600">Best quality</p>
                  <p className="text-xs text-gray-500 mt-1">~{estimatedTime * 2} minutes</p>
                </Label>
              </div>
            </div>
          </RadioGroup>

          {/* Cost Estimation */}
          <Alert className="mt-4">
            <Info className="h-4 w-4" />
            <AlertTitle>Estimated Cost</AlertTitle>
            <AlertDescription>
              <div className="flex items-center gap-4 mt-2">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  <span>{estimatedTime} minutes</span>
                </div>
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  <span>${estimatedCost.toFixed(2)} USD</span>
                </div>
              </div>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* Training Progress */}
      {isTraining && (
        <Card className="border border-gray-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Training in Progress
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  {trainingStatus === 'preparing' ? 'Preparing data...' :
                   trainingStatus === 'training' ? 'Training model...' :
                   'Processing...'}
                </span>
                <span className="text-sm text-gray-500">{trainingProgress}%</span>
              </div>
              <Progress value={trainingProgress} className="h-2" />
            </div>

            {/* Training Logs */}
            <div className="bg-gray-900 text-gray-100 rounded-lg p-4 h-48 overflow-y-auto font-mono text-sm">
              {trainingLogs.map((log, index) => (
                <div key={index} className="mb-1">
                  <span className="text-gray-400">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                  <span className="ml-2">{log.message}</span>
                </div>
              ))}
              {isTraining && <span className="animate-pulse">_</span>}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Training Complete */}
      {trainingComplete && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-800">
              <CheckCircle className="h-5 w-5" />
              Training Complete!
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <Sparkles className="h-4 w-4" />
              <AlertTitle>Your model is ready!</AlertTitle>
              <AlertDescription>
                Successfully trained {taskName} with {dataCount.toLocaleString()} samples.
              </AlertDescription>
            </Alert>

            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setShowTestDialog(true)}
              >
                <TestTube className="h-4 w-4 mr-2" />
                Test Model
              </Button>
              <Button
                onClick={proceedToDeployment}
                className="bg-gray-900 hover:bg-gray-800"
              >
                <Rocket className="h-4 w-4 mr-2" />
                Deploy Model
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Start Training Button */}
      {!isTraining && !trainingComplete && (
        <div className="flex justify-center">
          <Button
            size="lg"
            onClick={startTraining}
            className="bg-gray-900 hover:bg-gray-800"
          >
            <Play className="h-5 w-5 mr-2" />
            Start Training
          </Button>
        </div>
      )}

      {/* Test Model Dialog */}
      <Dialog open={showTestDialog} onOpenChange={setShowTestDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Test Your Model</DialogTitle>
            <DialogDescription>
              Try your trained model with a sample input
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div>
              <Label htmlFor="test-input">Test Input</Label>
              <Textarea
                id="test-input"
                placeholder="Enter your test question or prompt..."
                value={testInput}
                onChange={(e) => setTestInput(e.target.value)}
                rows={3}
              />
            </div>

            <Button
              onClick={testModel}
              disabled={isTestingModel || !testInput.trim()}
              className="w-full"
            >
              {isTestingModel ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Send Test
                </>
              )}
            </Button>

            {testOutput && (
              <div>
                <Label>Model Response</Label>
                <div className="mt-2 p-4 bg-gray-50 rounded-lg">
                  <p className="whitespace-pre-wrap">{testOutput}</p>
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ModelBuilder;
