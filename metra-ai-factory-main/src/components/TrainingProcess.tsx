import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Play, 
  Pause, 
  Square, 
  Activity, 
  Clock, 
  Cpu, 
  Database,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Download,
  Check
} from 'lucide-react';

interface TrainingProcessProps {
  onBack: () => void;
}

const TrainingProcess = ({ onBack }: TrainingProcessProps) => {
  const [isTraining, setIsTraining] = useState(true);
  const [currentEpoch, setCurrentEpoch] = useState(15);
  const [totalEpochs] = useState(50);
  const [accuracy, setAccuracy] = useState(0.8247);
  const [loss, setLoss] = useState(0.3621);
  const [progress, setProgress] = useState(30);

  const trainingLogs = [
    { timestamp: '14:32:45', epoch: 15, loss: 0.3621, accuracy: 0.8247, lr: 0.001, status: 'training' },
    { timestamp: '14:32:30', epoch: 14, loss: 0.3698, accuracy: 0.8201, lr: 0.001, status: 'completed' },
    { timestamp: '14:32:15', epoch: 13, loss: 0.3775, accuracy: 0.8156, lr: 0.001, status: 'completed' },
    { timestamp: '14:32:00', epoch: 12, loss: 0.3852, accuracy: 0.8089, lr: 0.001, status: 'completed' },
    { timestamp: '14:31:45', epoch: 11, loss: 0.3929, accuracy: 0.8024, lr: 0.001, status: 'completed' },
  ];

  const metrics = [
    { name: 'GPU Usage', value: '87%', icon: Cpu, color: 'text-orange-600' },
    { name: 'Memory Usage', value: '12.3GB', icon: Database, color: 'text-blue-600' },
    { name: 'Training Speed', value: '2.3 it/s', icon: Activity, color: 'text-green-600' },
    { name: 'Remaining Time', value: '35 minutes', icon: Clock, color: 'text-purple-600' },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      if (isTraining && progress < 100) {
        setProgress(prev => Math.min(prev + 0.5, 100));
        setCurrentEpoch(prev => Math.min(prev + 1, totalEpochs));
        setAccuracy(prev => Math.min(prev + 0.001, 0.95));
        setLoss(prev => Math.max(prev - 0.002, 0.15));
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isTraining, progress]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Model Training Progress</h1>
          <p className="text-gray-600">Monitor your model fine-tuning progress in real-time</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" onClick={onBack}>
            Return to Config
          </Button>
          <Button 
            variant={isTraining ? "destructive" : "default"}
            onClick={() => setIsTraining(!isTraining)}
          >
            {isTraining ? (
              <>
                <Pause className="h-4 w-4 mr-2" />
                Pause Training
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Continue Training
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Training Status */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Training Status</span>
            </span>
            <Badge 
              className={isTraining ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"}
            >
              {isTraining ? "Training" : "Paused"}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <div className="text-sm text-gray-600">Current Stage</div>
              <div className="text-2xl font-bold text-gray-900">{currentEpoch}/{totalEpochs}</div>
            </div>
            <div className="space-y-1">
              <div className="text-sm text-gray-600">Total Progress</div>
              <div className="text-2xl font-bold text-gray-900">{Math.round(progress)}%</div>
            </div>
          </div>
          <Progress value={progress} className="h-2" />
        </CardContent>
      </Card>

      {/* Real-time Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, index) => (
          <Card key={index} className="border border-gray-200 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <metric.icon className={`h-8 w-8 ${metric.color}`} />
                <div className="space-y-1">
                  <div className="text-sm text-gray-600">{metric.name}</div>
                  <div className="text-lg font-semibold text-gray-900">{metric.value}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Training Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Accuracy</span>
                <span className="text-lg font-semibold text-green-600">
                  {(accuracy * 100).toFixed(2)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Loss</span>
                <span className="text-lg font-semibold text-red-600">
                  {loss.toFixed(4)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Learning Rate</span>
                <span className="text-lg font-semibold text-blue-600">0.001</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Training Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Training Platform</span>
                <span className="font-medium">Replicate GPU</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">GPU Model</span>
                <span className="font-medium">NVIDIA A100</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Batch Size</span>
                <span className="font-medium">32</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Dataset Size</span>
                <span className="font-medium">10,247 samples</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Training Logs */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg flex items-center space-x-2">
            <TrendingUp className="h-5 w-5" />
            <span>Training Logs</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {trainingLogs.map((log, index) => (
              <div key={index} className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <span className="text-xs text-gray-500 font-mono">{log.timestamp}</span>
                  <span className="text-sm font-medium">Epoch {log.epoch}</span>
                  <div className="flex items-center space-x-3 text-xs">
                    <span>Loss: <span className="font-medium text-red-600">{log.loss}</span></span>
                    <span>Acc: <span className="font-medium text-green-600">{(log.accuracy * 100).toFixed(1)}%</span></span>
                    <span>LR: <span className="font-medium">{log.lr}</span></span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {log.status === 'training' ? (
                    <Badge className="bg-blue-100 text-blue-800">Training</Badge>
                  ) : (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Training Complete */}
      {progress >= 100 && (
        <Card className="border border-green-200 shadow-sm bg-green-50">
          <CardContent className="p-6">
            <div className="flex items-center space-x-3 mb-4">
              <CheckCircle className="h-6 w-6 text-green-600" />
              <div>
                <h3 className="text-lg font-semibold text-green-900">Training completed!</h3>
                <p className="text-sm text-green-700">Your AI model has been successfully trained and is ready for deployment</p>
              </div>
            </div>
            <div className="flex space-x-3">
              <Button className="bg-gray-900 hover:bg-gray-800">
                View Results
              </Button>
              <Button variant="outline">
                Deploy Model
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default TrainingProcess;
