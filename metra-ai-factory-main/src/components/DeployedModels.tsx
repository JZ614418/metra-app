import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ArrowUp, Activity, Globe, Settings, TestTube, FileText, Play, Pause, RefreshCw, CheckCircle2, Code, Download } from 'lucide-react';
import { TableHead } from '@/components/ui/table';

const DeployedModels = () => {
  const [refreshing, setRefreshing] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  const deployedModels = [
    {
      id: '1',
      name: 'Customer Complaint Classifier v1.0',
      baseModel: 'BERT Base',
      accuracy: 94.5,
      deployedAt: '2024-03-20',
      status: 'active',
      apiCalls: 12580,
      lastUsed: '2 hours ago',
      endpoint: 'https://api.metra.ai/v1/models/complaint-classifier',
      apiKey: 'sk-...abc123',
      version: '1.0',
      uptime: '99.9%',
      responseTime: '213ms',
      health: 98,
      cpu: 12,
      memory: 256
    }
  ];

  const deploymentOptions = [
    {
      id: 'api',
      title: 'REST API',
      description: 'Deploy as HTTP API endpoint for easy integration',
      icon: <Globe className="h-5 w-5" />,
      features: ['Auto-scaling', 'Load balancing', 'HTTPS encryption', 'Rate limiting']
    },
    {
      id: 'widget',
      title: 'Web Widget',
      description: 'Embed directly into your website',
      icon: <Code className="h-5 w-5" />,
      features: ['Customizable UI', 'Mobile responsive', 'Multi-language', 'Analytics']
    },
    {
      id: 'export',
      title: 'Model Export',
      description: 'Download model files for local deployment',
      icon: <Download className="h-5 w-5" />,
      features: ['ONNX format', 'TensorFlow', 'PyTorch', 'Offline usage']
    }
  ];

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1500);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-800";
      case "stopped":
        return "bg-gray-100 text-gray-800";
      case "error":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getHealthColor = (health) => {
    if (health >= 95) return "text-green-600";
    if (health >= 80) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h3 className="text-lg font-semibold text-gray-900">Deployed Models</h3>
            <Button
              size="sm"
              variant="outline"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh Status
            </Button>
          </div>
          <Button className="bg-gray-900 hover:bg-gray-800">
            Deploy New Model
          </Button>
        </div>
        <p className="text-sm text-gray-600">
          Manage your deployed models, monitor call status and performance metrics.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <Card className="border border-gray-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-green-500" />
              <span className="text-sm text-gray-600">Running</span>
            </div>
            <div className="text-2xl font-bold text-gray-900 mt-1">2</div>
          </CardContent>
        </Card>
        <Card className="border border-gray-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Globe className="h-4 w-4 text-blue-500" />
              <span className="text-sm text-gray-600">Today's Calls</span>
            </div>
            <div className="text-2xl font-bold text-gray-900 mt-1">245</div>
          </CardContent>
        </Card>
        <Card className="border border-gray-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-green-500" />
              <span className="text-sm text-gray-600">Avg Response</span>
            </div>
            <div className="text-2xl font-bold text-gray-900 mt-1">213ms</div>
          </CardContent>
        </Card>
        <Card className="border border-gray-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-green-500" />
              <span className="text-sm text-gray-600">Total Uptime</span>
            </div>
            <div className="text-2xl font-bold text-green-900 mt-1">99.8%</div>
          </CardContent>
        </Card>
      </div>

      {/* Deployed Models List */}
      <div className="space-y-4">
        {deployedModels.map((model, index) => (
          <Card key={index} className="border border-gray-200 shadow-sm">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1 space-y-4">
                  {/* Model Header */}
                  <div className="flex items-center space-x-3">
                    <h4 className="font-medium text-gray-900">{model.name}</h4>
                    <Badge className={getStatusColor(model.status)}>
                      {model.status === "active" ? "Active" : model.status === "stopped" ? "Stopped" : "Error"}
                    </Badge>
                    <span className="text-xs text-gray-500">v{model.version}</span>
                  </div>
                  
                  {/* Endpoint */}
                  <div className="space-y-2">
                    <span className="text-sm font-medium text-gray-700">Endpoint:</span>
                    <code className="block px-3 py-2 bg-gray-100 rounded text-xs font-mono text-gray-800 break-all">
                      {model.endpoint}
                    </code>
                  </div>

                  {/* Metrics */}
                  {model.status === "active" && (
                    <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 text-sm">
                      <div className="space-y-1">
                        <span className="text-gray-500">Total Calls</span>
                        <div className="font-medium text-gray-900">{model.apiCalls}</div>
                      </div>
                      <div className="space-y-1">
                        <span className="text-gray-500">Last Call</span>
                        <div className="font-medium text-gray-900">{model.lastUsed}</div>
                      </div>
                      <div className="space-y-1">
                        <span className="text-gray-500">Uptime</span>
                        <div className="font-medium text-gray-900">{model.uptime}</div>
                      </div>
                      <div className="space-y-1">
                        <span className="text-gray-500">Response Time</span>
                        <div className="font-medium text-gray-900">{model.responseTime}</div>
                      </div>
                      <div className="space-y-1">
                        <span className="text-gray-500">Health</span>
                        <div className={`font-medium ${getHealthColor(model.health)}`}>
                          {model.health}%
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Resource Usage */}
                  {model.status === "active" && (
                    <div className="space-y-3">
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500">CPU Usage</span>
                          <span className="font-medium">{model.cpu}%</span>
                        </div>
                        <Progress value={model.cpu} className="h-1" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500">Memory Usage</span>
                          <span className="font-medium">{model.memory}MB</span>
                        </div>
                        <Progress value={(model.memory / 1024) * 100} className="h-1" />
                      </div>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col space-y-2 ml-6">
                  {model.status === "active" ? (
                    <>
                      <Button size="sm" variant="outline">
                        <TestTube className="h-4 w-4 mr-1" />
                        Test
                      </Button>
                      <Button size="sm" variant="outline">
                        <FileText className="h-4 w-4 mr-1" />
                        Logs
                      </Button>
                      <Button size="sm" variant="outline">
                        <Settings className="h-4 w-4 mr-1" />
                        Settings
                      </Button>
                      <Button size="sm" variant="outline" className="text-red-600 hover:text-red-700">
                        <Pause className="h-4 w-4 mr-1" />
                        Stop
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button size="sm" className="bg-gray-900 hover:bg-gray-800">
                        <Play className="h-4 w-4 mr-1" />
                        Start
                      </Button>
                      <Button size="sm" variant="outline">
                        <Settings className="h-4 w-4 mr-1" />
                        Settings
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      <Card className="border border-gray-200 shadow-sm bg-gray-50">
        <CardContent className="p-8 text-center">
          <div className="text-4xl mb-4">🚀</div>
          <h4 className="font-medium text-gray-900 mb-2">No deployed models yet?</h4>
          <p className="text-sm text-gray-600 mb-4">
            Start training your first model from Task Builder, then deploy it as an API here.
          </p>
          <Button variant="outline">
            Start Training Model
          </Button>
        </CardContent>
      </Card>

      {/* Quick Start Guide */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl">Quick Start Guide</CardTitle>
          <p className="text-sm text-gray-500 mt-1">Integrate your model in 3 simple steps</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="font-medium text-gray-900 mb-2">1. Get your API key</p>
            <p className="text-sm text-gray-600">Copy your unique API key from the deployment details</p>
            <p className="font-medium text-gray-900 mb-2">2. Make API calls</p>
            <p className="text-sm text-gray-600 mb-2">Send POST requests to your endpoint</p>
            <p className="font-medium text-gray-900 mb-2">3. Handle responses</p>
            <p className="text-sm text-gray-600 mb-2">Process the model predictions</p>
          </div>
        </CardContent>
      </Card>

      {/* API Deployment Details */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl">API Deployment Details</CardTitle>
          <p className="text-sm text-gray-500 mt-1">Configure and manage your API deployment</p>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg mb-4">
            <div className="flex items-center gap-2 text-green-800 mb-2">
              <CheckCircle2 className="h-5 w-5" />
              <span className="font-medium">Deployment Successful!</span>
            </div>
            <p className="text-sm text-green-700">
              Your model is now available as an API. Use the endpoint below to make predictions.
            </p>
          </div>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600 mb-2">API Endpoint</p>
              <code className="block px-3 py-2 bg-gray-100 rounded text-xs font-mono text-gray-800 break-all">
                {deployedModels[0].endpoint}
              </code>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-2">API Key</p>
              <div className="flex items-center gap-2">
                <code className="block px-3 py-2 bg-gray-100 rounded text-xs font-mono text-gray-800 flex-1">
                  {showApiKey ? deployedModels[0].apiKey : 'sk-...hidden'}
                </code>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowApiKey(!showApiKey)}
                >
                  {showApiKey ? 'Hide' : 'Show'}
                </Button>
                <Button size="sm" variant="outline">
                  Copy
                </Button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Rate Limit</p>
                <p className="font-medium">1000 requests/hour</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Response Time</p>
                <p className="font-medium">&lt; 100ms</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Uptime SLA</p>
                <p className="font-medium">99.9%</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">SSL/TLS</p>
                <p className="font-medium">Enabled</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Example Request */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl">Example Request</CardTitle>
        </CardHeader>
        <CardContent>
          <code className="block px-3 py-2 bg-gray-100 rounded text-xs font-mono text-gray-800 break-all">
            {`curl -X POST -H "Content-Type: application/json" -d '{"text": "I had a bad experience with the product"}' https://api.metra.ai/v1/models/complaint-classifier`}
          </code>
        </CardContent>
      </Card>

      {/* Example Response */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl">Example Response</CardTitle>
        </CardHeader>
        <CardContent>
          <code className="block px-3 py-2 bg-gray-100 rounded text-xs font-mono text-gray-800 break-all">
            {`{
              "sentiment": "negative",
              "confidence": 0.98
            }`}
          </code>
        </CardContent>
      </Card>

      {/* View Documentation */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl">View Documentation</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600">
            Check out our detailed documentation for more information on how to use the API.
          </p>
          <Button variant="outline">
            View Documentation
          </Button>
        </CardContent>
      </Card>

      {/* Monitor Usage */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl">Monitor Usage</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600">
            Monitor the usage and performance of your deployed model.
          </p>
          <Button variant="outline">
            Monitor Usage
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default DeployedModels;
