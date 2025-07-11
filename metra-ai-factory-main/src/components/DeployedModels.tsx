import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  ArrowUp, Activity, Globe, Settings, TestTube, FileText, 
  Play, Pause, RefreshCw, CheckCircle2, Code, Download,
  Rocket, Server, Copy, Eye, EyeOff, Trash2, Brain, Database
} from 'lucide-react';
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, 
  DialogDescription, DialogFooter 
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { deploymentApi, TrainedModel, Deployment } from '@/lib/api';
import { format } from 'date-fns';
import { EmptyState } from '@/components/ui/empty-state';

const DeployedModels = () => {
  const [trainedModels, setTrainedModels] = useState<TrainedModel[]>([]);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedModel, setSelectedModel] = useState<TrainedModel | null>(null);
  const [showDeployDialog, setShowDeployDialog] = useState(false);
  const [deploymentType, setDeploymentType] = useState<'api' | 'widget' | 'export'>('api');
  const [deploying, setDeploying] = useState(false);
  const [showApiKey, setShowApiKey] = useState<{[key: string]: boolean}>({});
  const [testInput, setTestInput] = useState('');
  const [testingDeployment, setTestingDeployment] = useState<string | null>(null);
  const [exportFormat, setExportFormat] = useState('onnx');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [modelsData, deploymentsData] = await Promise.all([
        deploymentApi.getTrainedModels(),
        deploymentApi.getDeployments()
      ]);
      setTrainedModels(modelsData);
      setDeployments(deploymentsData);
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load deployment data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
    toast.success('Deployment status refreshed');
  };

  const handleDeploy = async () => {
    if (!selectedModel) return;

    setDeploying(true);
    try {
      const config: any = {};
      if (deploymentType === 'export') {
        config.format = exportFormat;
      }

      const deployment = await deploymentApi.deployModel({
        model_id: selectedModel.id,
        type: deploymentType,
        config
      });

      setDeployments([deployment, ...deployments]);
      setShowDeployDialog(false);
      toast.success(`Model deployed successfully as ${deploymentType.toUpperCase()}`);
    } catch (error) {
      console.error('Deployment failed:', error);
      toast.error('Failed to deploy model');
    } finally {
      setDeploying(false);
    }
  };

  const handleStartStop = async (deployment: Deployment) => {
    try {
      if (deployment.status === 'active') {
        await deploymentApi.stopDeployment(deployment.id);
        toast.success('Deployment stopped');
      } else if (deployment.status === 'stopped') {
        await deploymentApi.startDeployment(deployment.id);
        toast.success('Deployment started');
      }
      await loadData();
    } catch (error) {
      console.error('Failed to change deployment status:', error);
      toast.error('Failed to change deployment status');
    }
  };

  const handleTest = async (deployment: Deployment) => {
    if (!testInput.trim()) {
      toast.error('Please enter test input');
      return;
    }

    setTestingDeployment(deployment.id);
    try {
      const result = await deploymentApi.testDeployment(deployment.id, { text: testInput });
      toast.success(
        <div>
          <p className="font-semibold">Test Result:</p>
          <p>Prediction: {result.prediction}</p>
          <p>Confidence: {(result.confidence * 100).toFixed(1)}%</p>
          <p>Response Time: {result.processing_time}ms</p>
        </div>
      );
    } catch (error) {
      console.error('Test failed:', error);
      toast.error('Failed to test deployment');
    } finally {
      setTestingDeployment(null);
    }
  };

  const handleDelete = async (deployment: Deployment) => {
    if (!confirm('Are you sure you want to delete this deployment?')) return;

    try {
      await deploymentApi.deleteDeployment(deployment.id);
      setDeployments(deployments.filter(d => d.id !== deployment.id));
      toast.success('Deployment deleted');
    } catch (error) {
      console.error('Failed to delete deployment:', error);
      toast.error('Failed to delete deployment');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'stopped': return 'bg-gray-100 text-gray-800';
      case 'deploying': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'completed': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getHealthColor = (health: number = 0) => {
    if (health >= 95) return 'text-green-600';
    if (health >= 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Calculate stats
  const activeDeployments = deployments.filter(d => d.status === 'active').length;
  const totalApiCalls = deployments.reduce((sum, d) => sum + d.metrics.api_calls, 0);
  const avgResponseTime = deployments.length > 0 
    ? deployments.reduce((sum, d) => sum + d.metrics.avg_response_time, 0) / deployments.length 
    : 0;
  const avgUptime = deployments.length > 0
    ? deployments.reduce((sum, d) => sum + d.metrics.uptime, 0) / deployments.length
    : 0;

  // Show empty state if no trained models exist
  if (!loading && trainedModels.length === 0) {
    return (
      <div className="p-8 space-y-6 max-w-6xl mx-auto">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Model Deployment
          </h1>
          <p className="text-gray-600">
            Deploy your trained models as APIs, widgets, or export them for local use
          </p>
        </div>
        
        <EmptyState
          icon={Rocket}
          title="No Trained Models Available"
          description="You need to train a model before you can deploy it. Complete the training process to see your deployable models here."
          badge={{
            text: "Training Required",
            variant: "outline"
          }}
          action={{
            label: "Go to Training Center",
            onClick: () => window.location.href = '/dashboard?section=model-training',
            variant: "default"
          }}
        >
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
            <div className="p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Step 1: Define Task</span>
              </div>
              <p className="text-xs text-gray-600">Create your AI task</p>
            </div>
            <div className="p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Step 2: Select Model</span>
              </div>
              <p className="text-xs text-gray-600">Choose base model</p>
            </div>
            <div className="p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <Database className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Step 3: Process Data</span>
              </div>
              <p className="text-xs text-gray-600">Collect training data</p>
            </div>
            <div className="p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <Rocket className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Step 4: Train Model</span>
              </div>
              <p className="text-xs text-gray-600">Complete training process</p>
            </div>
          </div>
        </EmptyState>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h3 className="text-lg font-semibold text-gray-900">Model Deployment</h3>
            <Button
              size="sm"
              variant="outline"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
          <Button 
            className="bg-gray-900 hover:bg-gray-800"
            onClick={() => setShowDeployDialog(true)}
          >
            <Rocket className="h-4 w-4 mr-2" />
            Deploy New Model
          </Button>
        </div>
        <p className="text-sm text-gray-600">
          Deploy your trained models as APIs, widgets, or export them for local use.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <Card className="border border-gray-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-green-500" />
              <span className="text-sm text-gray-600">Active Deployments</span>
            </div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{activeDeployments}</div>
          </CardContent>
        </Card>
        <Card className="border border-gray-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Globe className="h-4 w-4 text-blue-500" />
              <span className="text-sm text-gray-600">Total API Calls</span>
            </div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{totalApiCalls.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card className="border border-gray-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-purple-500" />
              <span className="text-sm text-gray-600">Avg Response Time</span>
            </div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{avgResponseTime.toFixed(0)}ms</div>
          </CardContent>
        </Card>
        <Card className="border border-gray-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="text-sm text-gray-600">Avg Uptime</span>
            </div>
            <div className="text-2xl font-bold text-green-900 mt-1">{avgUptime.toFixed(1)}%</div>
          </CardContent>
        </Card>
      </div>

      {/* Deployed Models List */}
      {deployments.length > 0 ? (
        <div className="space-y-4">
          {deployments.map((deployment) => {
            const model = trainedModels.find(m => m.id === deployment.model_id);
            return (
              <Card key={deployment.id} className="border border-gray-200 shadow-sm">
                <CardContent className="p-6">
                  <div className="space-y-4">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <h4 className="font-medium text-gray-900">
                          {model?.name || 'Unknown Model'}
                        </h4>
                        <Badge className={getStatusColor(deployment.status)}>
                          {deployment.status}
                        </Badge>
                        <Badge variant="outline">
                          {deployment.type.toUpperCase()}
                        </Badge>
                      </div>
                      <div className="flex items-center space-x-2">
                        {deployment.status === 'active' && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setTestInput('');
                                setTestingDeployment(deployment.id);
                              }}
                            >
                              <TestTube className="h-4 w-4 mr-1" />
                              Test
                            </Button>
                          </>
                        )}
                        {(deployment.status === 'active' || deployment.status === 'stopped') && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleStartStop(deployment)}
                          >
                            {deployment.status === 'active' ? (
                              <>
                                <Pause className="h-4 w-4 mr-1" />
                                Stop
                              </>
                            ) : (
                              <>
                                <Play className="h-4 w-4 mr-1" />
                                Start
                              </>
                            )}
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-red-600 hover:text-red-700"
                          onClick={() => handleDelete(deployment)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    {/* Deployment Details */}
                    {deployment.type === 'api' && deployment.endpoint && (
                      <div className="space-y-3">
                        <div>
                          <Label className="text-sm text-gray-600">API Endpoint</Label>
                          <div className="flex items-center gap-2 mt-1">
                            <code className="flex-1 px-3 py-2 bg-gray-100 rounded text-xs font-mono text-gray-800">
                              {deployment.endpoint}
                            </code>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => copyToClipboard(deployment.endpoint!)}
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                        <div>
                          <Label className="text-sm text-gray-600">API Key</Label>
                          <div className="flex items-center gap-2 mt-1">
                            <code className="flex-1 px-3 py-2 bg-gray-100 rounded text-xs font-mono text-gray-800">
                              {showApiKey[deployment.id] ? deployment.api_key : 'sk-metra-••••••••'}
                            </code>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setShowApiKey({
                                ...showApiKey,
                                [deployment.id]: !showApiKey[deployment.id]
                              })}
                            >
                              {showApiKey[deployment.id] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => copyToClipboard(deployment.api_key!)}
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}

                    {deployment.type === 'widget' && deployment.widget_code && (
                      <div>
                        <Label className="text-sm text-gray-600">Widget Code</Label>
                        <div className="mt-1">
                          <Textarea
                            value={deployment.widget_code}
                            readOnly
                            className="font-mono text-xs"
                            rows={6}
                          />
                          <Button
                            size="sm"
                            variant="outline"
                            className="mt-2"
                            onClick={() => copyToClipboard(deployment.widget_code!)}
                          >
                            <Copy className="h-4 w-4 mr-2" />
                            Copy Widget Code
                          </Button>
                        </div>
                      </div>
                    )}

                    {deployment.type === 'export' && deployment.export_url && (
                      <div>
                        <Label className="text-sm text-gray-600">Download Link</Label>
                        <div className="mt-1">
                          <Button
                            variant="outline"
                            onClick={() => window.open(deployment.export_url, '_blank')}
                          >
                            <Download className="h-4 w-4 mr-2" />
                            Download Model ({deployment.config?.format?.toUpperCase() || 'ONNX'})
                          </Button>
                        </div>
                      </div>
                    )}

                    {/* Metrics */}
                    {deployment.status === 'active' && (
                      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 pt-4 border-t">
                        <div>
                          <span className="text-sm text-gray-500">API Calls</span>
                          <div className="font-medium text-gray-900">{deployment.metrics.api_calls.toLocaleString()}</div>
                        </div>
                        <div>
                          <span className="text-sm text-gray-500">Last Used</span>
                          <div className="font-medium text-gray-900">{deployment.metrics.last_used || 'Never'}</div>
                        </div>
                        <div>
                          <span className="text-sm text-gray-500">Response Time</span>
                          <div className="font-medium text-gray-900">{deployment.metrics.avg_response_time}ms</div>
                        </div>
                        <div>
                          <span className="text-sm text-gray-500">Uptime</span>
                          <div className="font-medium text-gray-900">{deployment.metrics.uptime}%</div>
                        </div>
                        <div>
                          <span className="text-sm text-gray-500">Health</span>
                          <div className={`font-medium ${getHealthColor(deployment.metrics.health)}`}>
                            {deployment.metrics.health || 0}%
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Test Interface */}
                    {testingDeployment === deployment.id && (
                      <div className="p-4 bg-gray-50 rounded-lg space-y-3">
                        <Label>Test Input</Label>
                        <Textarea
                          value={testInput}
                          onChange={(e) => setTestInput(e.target.value)}
                          placeholder="Enter test text (e.g., 'I had a bad experience with the product')"
                          rows={3}
                        />
                        <div className="flex gap-2">
                          <Button
                            onClick={() => handleTest(deployment)}
                            disabled={!testInput.trim()}
                          >
                            Run Test
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => setTestingDeployment(null)}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card className="border border-gray-200 shadow-sm bg-gray-50">
          <CardContent className="p-8 text-center">
            <div className="text-4xl mb-4">🚀</div>
            <h4 className="font-medium text-gray-900 mb-2">No deployed models yet</h4>
            <p className="text-sm text-gray-600 mb-4">
              Deploy your trained models to start using them in production.
            </p>
            <Button onClick={() => setShowDeployDialog(true)}>
              Deploy Your First Model
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Deployment Dialog */}
      <Dialog open={showDeployDialog} onOpenChange={setShowDeployDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Deploy Model</DialogTitle>
            <DialogDescription>
              Choose a trained model and deployment method.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Model Selection */}
            <div>
              <Label>Select Model</Label>
              <Select
                value={selectedModel?.id}
                onValueChange={(value) => {
                  const model = trainedModels.find(m => m.id === value);
                  setSelectedModel(model || null);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose a trained model" />
                </SelectTrigger>
                <SelectContent>
                  {trainedModels.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      <div className="flex items-center justify-between w-full">
                        <span>{model.name}</span>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span>{model.base_model}</span>
                          <span>•</span>
                          <span>{(model.accuracy * 100).toFixed(1)}% accuracy</span>
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Deployment Type */}
            <div>
              <Label>Deployment Type</Label>
              <div className="grid grid-cols-3 gap-3 mt-2">
                <Card 
                  className={`cursor-pointer transition-all ${
                    deploymentType === 'api' ? 'border-gray-900 bg-gray-50' : 'border-gray-200'
                  }`}
                  onClick={() => setDeploymentType('api')}
                >
                  <CardContent className="p-4 text-center">
                    <Globe className="h-8 w-8 mx-auto mb-2 text-gray-700" />
                    <h4 className="font-medium">REST API</h4>
                    <p className="text-xs text-gray-600 mt-1">
                      Deploy as HTTP endpoint
                    </p>
                  </CardContent>
                </Card>

                <Card 
                  className={`cursor-pointer transition-all ${
                    deploymentType === 'widget' ? 'border-gray-900 bg-gray-50' : 'border-gray-200'
                  }`}
                  onClick={() => setDeploymentType('widget')}
                >
                  <CardContent className="p-4 text-center">
                    <Code className="h-8 w-8 mx-auto mb-2 text-gray-700" />
                    <h4 className="font-medium">Web Widget</h4>
                    <p className="text-xs text-gray-600 mt-1">
                      Embed in your website
                    </p>
                  </CardContent>
                </Card>

                <Card 
                  className={`cursor-pointer transition-all ${
                    deploymentType === 'export' ? 'border-gray-900 bg-gray-50' : 'border-gray-200'
                  }`}
                  onClick={() => setDeploymentType('export')}
                >
                  <CardContent className="p-4 text-center">
                    <Download className="h-8 w-8 mx-auto mb-2 text-gray-700" />
                    <h4 className="font-medium">Export Model</h4>
                    <p className="text-xs text-gray-600 mt-1">
                      Download for local use
                    </p>
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Export Format (if export type selected) */}
            {deploymentType === 'export' && (
              <div>
                <Label>Export Format</Label>
                <Select value={exportFormat} onValueChange={setExportFormat}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="onnx">ONNX (Recommended)</SelectItem>
                    <SelectItem value="tensorflow">TensorFlow</SelectItem>
                    <SelectItem value="pytorch">PyTorch</SelectItem>
                    <SelectItem value="coreml">Core ML (iOS)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Deployment Features */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-sm mb-2">Included Features</h4>
              <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                {deploymentType === 'api' && (
                  <>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Auto-scaling
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      HTTPS encryption
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Rate limiting
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      API key authentication
                    </div>
                  </>
                )}
                {deploymentType === 'widget' && (
                  <>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Customizable UI
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Mobile responsive
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Analytics tracking
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Multi-language support
                    </div>
                  </>
                )}
                {deploymentType === 'export' && (
                  <>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Optimized for inference
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Cross-platform compatible
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Offline usage
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      No API limits
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeployDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleDeploy}
              disabled={!selectedModel || deploying}
            >
              {deploying ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Deploying...
                </>
              ) : (
                <>
                  <Rocket className="h-4 w-4 mr-2" />
                  Deploy Model
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DeployedModels;
