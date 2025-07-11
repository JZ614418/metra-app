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
  Check,
  RefreshCw
} from 'lucide-react';
import { trainingApi } from '@/lib/api';

interface TrainingProcessProps {
  onBack: () => void;
}

const TrainingProcess = ({ onBack }: TrainingProcessProps) => {
  const [trainingJobs, setTrainingJobs] = useState<any[]>([]);
  const [currentJob, setCurrentJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchTrainingJobs = async () => {
    try {
      setRefreshing(true);
      const jobs = await trainingApi.getJobs();
      setTrainingJobs(jobs);
      
      // Set current job to the first one or the most recent
      if (jobs.length > 0) {
        setCurrentJob(jobs[0]);
      }
    } catch (error) {
      console.error('Failed to fetch training jobs:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchJobStatus = async (jobId: string) => {
    try {
      const status = await trainingApi.getStatus(jobId);
      setCurrentJob(status);
    } catch (error) {
      console.error('Failed to fetch job status:', error);
    }
  };

  useEffect(() => {
    fetchTrainingJobs();
  }, []);

  // Auto-refresh job status if training is in progress
  useEffect(() => {
    if (currentJob && (currentJob.status === 'training' || currentJob.status === 'preparing')) {
      const interval = setInterval(() => {
        fetchJobStatus(currentJob.id);
      }, 5000); // Refresh every 5 seconds

      return () => clearInterval(interval);
    }
  }, [currentJob]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'training':
        return 'bg-blue-100 text-blue-800';
      case 'preparing':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading training jobs...</p>
        </div>
      </div>
    );
  }

  if (trainingJobs.length === 0) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Training Jobs</h1>
            <p className="text-gray-600">No training jobs found</p>
          </div>
          <Button variant="outline" onClick={onBack}>
            Return to Config
          </Button>
        </div>
        <Card className="border border-gray-200 shadow-sm">
          <CardContent className="p-8 text-center">
            <Activity className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Training Jobs</h3>
            <p className="text-gray-600">Start your first training job to see progress here.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Training Jobs</h1>
          <p className="text-gray-600">Monitor your model training progress</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" onClick={onBack}>
            Return to Config
          </Button>
          <Button 
            variant="outline"
            onClick={fetchTrainingJobs}
            disabled={refreshing}
          >
            {refreshing ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Refreshing...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Job Selection */}
      {trainingJobs.length > 1 && (
        <Card className="border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle>Select Training Job</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {trainingJobs.map((job) => (
                <div
                  key={job.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    currentJob?.id === job.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setCurrentJob(job)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">{job.task_name}</h3>
                    <Badge className={getStatusColor(job.status)}>
                      {job.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{job.task_description}</p>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Model: {job.base_model}</span>
                    <span>Progress: {job.progress}%</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {currentJob && (
        <>
          {/* Current Job Status */}
          <Card className="border border-gray-200 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center space-x-2">
                  <Activity className="h-5 w-5" />
                  <span>{currentJob.task_name}</span>
                </span>
                <Badge className={getStatusColor(currentJob.status)}>
                  {currentJob.status}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <div className="text-sm text-gray-600">Progress</div>
                  <div className="text-2xl font-bold text-gray-900">{currentJob.progress}%</div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm text-gray-600">Data Count</div>
                  <div className="text-2xl font-bold text-gray-900">{currentJob.data_count}</div>
                </div>
              </div>
              <Progress value={currentJob.progress} className="h-2" />
            </CardContent>
          </Card>

          {/* Training Details */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border border-gray-200 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Training Configuration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Base Model</span>
                    <span className="font-medium">{currentJob.base_model}</span>
                  </div>
                  {currentJob.training_config && (
                    <>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Epochs</span>
                        <span className="font-medium">{currentJob.training_config.epochs}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Learning Rate</span>
                        <span className="font-medium">{currentJob.training_config.learning_rate}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Batch Size</span>
                        <span className="font-medium">{currentJob.training_config.batch_size}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Training Mode</span>
                        <span className="font-medium capitalize">{currentJob.training_config.training_mode}</span>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            {currentJob.metrics && (
              <Card className="border border-gray-200 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg">Training Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Accuracy</span>
                      <span className="text-lg font-semibold text-green-600">
                        {(currentJob.metrics.accuracy * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Final Loss</span>
                      <span className="text-lg font-semibold text-red-600">
                        {currentJob.metrics.final_loss.toFixed(4)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Training Logs */}
          {currentJob.logs && currentJob.logs.length > 0 && (
            <Card className="border border-gray-200 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center space-x-2">
                  <TrendingUp className="h-5 w-5" />
                  <span>Training Logs</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {currentJob.logs.map((log: any, index: number) => (
                    <div key={index} className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-4">
                        <span className="text-xs text-gray-500 font-mono">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        <span className="text-sm">{log.message}</span>
                      </div>
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Training Complete */}
          {currentJob.status === 'completed' && (
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

          {/* Training Failed */}
          {currentJob.status === 'failed' && currentJob.error && (
            <Card className="border border-red-200 shadow-sm bg-red-50">
              <CardContent className="p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <AlertCircle className="h-6 w-6 text-red-600" />
                  <div>
                    <h3 className="text-lg font-semibold text-red-900">Training failed</h3>
                    <p className="text-sm text-red-700">{currentJob.error}</p>
                  </div>
                </div>
                <div className="flex space-x-3">
                  <Button variant="outline" onClick={() => fetchJobStatus(currentJob.id)}>
                    Retry
                  </Button>
                  <Button variant="outline" onClick={onBack}>
                    Back to Config
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
};

export default TrainingProcess;