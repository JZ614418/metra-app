import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Rocket, 
  Settings, 
  Play, 
  Pause,
  CheckCircle2,
  AlertCircle,
  Clock,
  Cpu,
  BarChart,
  Info,
  Sparkles
} from 'lucide-react';

const ModelBuilder = () => {
  const [isTraining, setIsTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [currentEpoch, setCurrentEpoch] = useState(0);
  const [trainingStarted, setTrainingStarted] = useState(false);

  // Training configuration (technical parameters hidden from users)
  const trainingConfig = {
    learningRate: 2e-5,
    batchSize: 32,
    epochs: 3,
    warmupSteps: 500,
    weightDecay: 0.01,
    gradientAccumulation: 1,
    maxLength: 512,
    fp16: true
  };

  // User-friendly training information
  const trainingInfo = {
    baseModel: 'BERT Base',
    datasetSize: '1,189 samples',
    estimatedTime: 'About 30 minutes',
    estimatedCost: '$5-10',
    targetAccuracy: '92-95%'
  };

  // Training metrics
  const [metrics, setMetrics] = useState({
    loss: 3.45,
    accuracy: 0.45,
    validationAccuracy: 0.42,
    learningRate: 0.00002,
    epoch: currentEpoch
  });

  // Simulate training progress
  useEffect(() => {
    if (isTraining && trainingProgress < 100) {
      const interval = setInterval(() => {
        setTrainingProgress(prev => {
          const newProgress = prev + 2;
          return newProgress > 100 ? 100 : newProgress;
        });
        
        // Update metrics
        setMetrics(prev => ({
          ...prev,
          loss: Math.max(0.35, prev.loss - Math.random() * 0.15),
          accuracy: Math.min(0.96, prev.accuracy + Math.random() * 0.03),
          validationAccuracy: Math.min(0.94, prev.validationAccuracy + Math.random() * 0.025),
          epoch: Math.floor((trainingProgress / 100) * 3) + 1
        }));
        
        if (trainingProgress >= 33 && trainingProgress < 34) {
          setCurrentEpoch(2);
        } else if (trainingProgress >= 66 && trainingProgress < 67) {
          setCurrentEpoch(3);
        }
      }, 800);
      
      return () => clearInterval(interval);
    }
  }, [isTraining, trainingProgress]);

  const handleStartTraining = () => {
    setIsTraining(true);
  };

  const handlePauseTraining = () => {
    setIsTraining(false);
    // Real implementation would call API to pause training
  };

  const modelInfo = {
    name: 'BERT Base',
    baseModel: 'bert-base-uncased',
    architecture: 'Transformer',
    parameters: '110M',
    taskType: 'Text Classification',
    datasetSize: 5420,
    estimatedTime: '30 minutes',
    estimatedCost: '$8.50'
  };

  const trainingSettings = {
    learningRate: 'Auto',
    batchSize: 'Auto',
    epochs: 'Auto',
    validationSplit: '20%',
    earlyStop: 'Enabled'
  };

  const advancedOptions = [
    { name: 'Learning Rate', value: '2e-5', type: 'auto' },
    { name: 'Batch Size', value: '32', type: 'auto' },
    { name: 'Training Epochs', value: '3-5', type: 'auto' },
    { name: 'Warm-up Steps', value: '500', type: 'auto' },
    { name: 'Weight Decay', value: '0.01', type: 'auto' }
  ];

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      {/* Training ready status */}
      <Card className="border-0 shadow-sm bg-green-50/30">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Ready to Start</h3>
                <p className="text-sm text-gray-600">Fine-tune open source models with LoRA technology</p>
              </div>
            </div>
            <Badge className="bg-green-50/50 text-green-700">
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Ready
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Training overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Training configuration summary */}
          <Card className="border-0 shadow-sm">
            <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Training Configuration
            </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Base Model</span>
              <span className="text-sm font-medium">{modelInfo.baseModel}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Task Type</span>
              <span className="text-sm font-medium">{modelInfo.taskType}</span>
                      </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Training Data</span>
              <span className="text-sm font-medium">{modelInfo.datasetSize.toLocaleString()} samples</span>
                    </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Estimated Time</span>
              <span className="text-sm font-medium">{modelInfo.estimatedTime}</span>
                  </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-gray-600">Training Cost</span>
              <span className="text-sm font-medium">{modelInfo.estimatedCost}</span>
                </div>
            </CardContent>
          </Card>

        {/* Technical description */}
          <Card className="border-0 shadow-sm">
            <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Info className="h-5 w-5" />
              Training Features
            </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
            <Alert className="border-purple-200 bg-purple-50/50">
              <AlertCircle className="h-4 w-4 text-purple-600" />
              <AlertDescription className="text-sm text-gray-700">
                Metra uses advanced proprietary optimization technology, which only requires minor adjustments to perfectly match your needs
              </AlertDescription>
            </Alert>
            
            <div className="space-y-2">
              <p className="text-sm text-gray-600">Training process includes:</p>
              <ul className="space-y-1 text-sm text-gray-600">
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-purple-500 rounded-full"></div>
                  Automatic parameter optimization
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-purple-500 rounded-full"></div>
                  Real-time performance monitoring
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-purple-500 rounded-full"></div>
                  Intelligent quality protection
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-purple-500 rounded-full"></div>
                  Best model automatic saving
                </li>
              </ul>
              </div>
            </CardContent>
          </Card>
        </div>

      {/* Training control and progress */}
      {trainingStarted && (
          <Card className="border-0 shadow-sm">
            <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Training Progress</CardTitle>
              <div className="flex items-center gap-4">
                <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50/50">
                  <Cpu className="h-3 w-3 mr-1" />
                  GPU running
                </Badge>
                <Badge variant="outline" className="text-purple-600 border-purple-200 bg-purple-50/50">
                  <Clock className="h-3 w-3 mr-1" />
                  Stage {currentEpoch}/3
                </Badge>
              </div>
            </div>
            </CardHeader>
          <CardContent className="space-y-6">
            {/* Progress bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Overall Progress</span>
                <span className="font-medium">{trainingProgress}%</span>
              </div>
              <Progress value={trainingProgress} className="h-3" />
                    </div>

            {/* Real-time metrics */}
            <div className="grid grid-cols-3 gap-4">
              <Card className="border border-gray-100">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Training Loss</span>
                    <BarChart className="h-4 w-4 text-gray-400" />
                  </div>
                  <p className="text-2xl font-semibold">{metrics.loss.toFixed(2)}</p>
                  <p className="text-xs text-green-600 mt-1">↓ Decreasing</p>
                </CardContent>
              </Card>
              
              <Card className="border border-gray-100">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Training Accuracy</span>
                    <BarChart className="h-4 w-4 text-gray-400" />
              </div>
                  <p className="text-2xl font-semibold">{metrics.accuracy.toFixed(1)}%</p>
                  <p className="text-xs text-green-600 mt-1">↑ Increasing</p>
            </CardContent>
          </Card>

              <Card className="border border-gray-100">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Validation Accuracy</span>
                    <BarChart className="h-4 w-4 text-gray-400" />
                  </div>
                  <p className="text-2xl font-semibold">{metrics.validationAccuracy.toFixed(1)}%</p>
                  <p className="text-xs text-green-600 mt-1">↑ Increasing</p>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action buttons */}
      <Card className="border-0 shadow-sm">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">
                {isTraining ? 'Training in progress...' : trainingProgress === 100 ? 'Training completed!' : 'Ready to Start'}
              </p>
              <p className="font-semibold text-gray-900">
                {trainingProgress === 100 
                  ? 'Your dedicated AI model is ready' 
                  : 'Click Start to launch dedicated optimization'}
              </p>
                </div>
            
            {!trainingStarted ? (
              <Button 
                onClick={handleStartTraining}
                className="bg-gray-900 hover:bg-gray-800"
              >
                <Play className="h-4 w-4 mr-2" />
                Start Training
              </Button>
            ) : isTraining ? (
              <Button 
                onClick={handlePauseTraining}
                variant="outline"
                className="border-orange-300 text-orange-600 hover:bg-orange-50"
              >
                <Pause className="h-4 w-4 mr-2" />
                Pause Training
              </Button>
            ) : trainingProgress === 100 ? (
              <Button className="bg-gray-900 hover:bg-gray-800">
                Next Step: Deploy Model
              </Button>
            ) : (
                <Button 
                  onClick={handleStartTraining} 
                className="bg-gray-900 hover:bg-gray-800"
                >
                  <Play className="h-4 w-4 mr-2" />
                Continue Training
                </Button>
            )}
              </div>
            </CardContent>
          </Card>
    </div>
  );
};

export default ModelBuilder;
