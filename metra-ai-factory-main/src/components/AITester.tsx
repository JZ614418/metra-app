import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Play, 
  Loader2, 
  Copy, 
  CheckCircle2, 
  AlertCircle,
  Clock,
  Target,
  Sparkles,
  Brain,
  TestTube
} from 'lucide-react';
import { toast } from 'sonner';
import { deploymentApi, Deployment } from '@/lib/api';

interface AITesterProps {
  deployment: Deployment;
}

interface TestResult {
  prediction: any;
  confidence?: number;
  processing_time?: number;
  model_version?: string;
  status?: string;
  note?: string;
  error?: string;
}

const AITester: React.FC<AITesterProps> = ({ deployment }) => {
  const [testInput, setTestInput] = useState('');
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleTest = async () => {
    if (!testInput.trim()) {
      toast.error('Please enter test input');
      return;
    }

    setIsLoading(true);
    const startTime = Date.now();

    try {
      const result = await deploymentApi.testDeployment(deployment.id, { 
        text: testInput 
      });

      const endTime = Date.now();
      const actualResponseTime = endTime - startTime;

      const testResult: TestResult = {
        ...result,
        processing_time: result.processing_time || actualResponseTime
      };

      setTestResults([testResult, ...testResults]);
      
      // Show success notification
      if (result.status === 'real_prediction') {
        toast.success('🎉 Real AI prediction completed!');
      } else {
        toast.success('✅ Test completed');
      }

    } catch (error) {
      console.error('Test failed:', error);
      const errorResult: TestResult = {
        prediction: null,
        error: error instanceof Error ? error.message : 'Test failed',
        status: 'error'
      };
      setTestResults([errorResult, ...testResults]);
      toast.error('Test failed, please try again');
    } finally {
      setIsLoading(false);
    }
  };


  const copyResult = (result: TestResult) => {
    const resultText = JSON.stringify(result, null, 2);
    navigator.clipboard.writeText(resultText);
    toast.success('Result copied to clipboard');
  };

  const renderResult = (result: TestResult, index: number) => {
    const isError = result.status === 'error' || result.error;
    const isReal = result.status === 'real_prediction';

    return (
      <Card key={index} className={`mb-4 ${isError ? 'border-red-200' : isReal ? 'border-green-200' : 'border-gray-200'}`}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {isError ? (
                <AlertCircle className="h-4 w-4 text-red-500" />
              ) : isReal ? (
                <Sparkles className="h-4 w-4 text-green-500" />
              ) : (
                <Brain className="h-4 w-4 text-blue-500" />
              )}
              <span className="text-sm font-medium">
                {isError ? 'Error' : isReal ? 'Real Prediction' : 'Mock Prediction'}
              </span>
              {result.processing_time && (
                <Badge variant="outline" className="ml-2">
                  <Clock className="h-3 w-3 mr-1" />
                  {result.processing_time}ms
                </Badge>
              )}
            </div>
            <Button 
              size="sm" 
              variant="outline" 
              onClick={() => copyResult(result)}
            >
              <Copy className="h-3 w-3" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {isError ? (
            <Alert className="border-red-200">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-red-700">
                {result.error}
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-3">
              <div>
                <div className="text-sm font-medium text-gray-700 mb-1">Prediction Result:</div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <code className="text-sm">
                    {typeof result.prediction === 'object' 
                      ? JSON.stringify(result.prediction, null, 2)
                      : String(result.prediction)
                    }
                  </code>
                </div>
              </div>
              
              {result.confidence && (
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">Confidence:</span>
                  <Badge variant="secondary">
                    {(result.confidence * 100).toFixed(1)}%
                  </Badge>
                </div>
              )}

              {result.model_version && (
                <div className="text-xs text-gray-500">
                  Model Version: {result.model_version}
                </div>
              )}

              {result.note && (
                <Alert>
                  <AlertDescription className="text-sm">
                    {result.note}
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Test input area */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TestTube className="h-5 w-5" />
            Test Your AI Model
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Input field */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              Test Input:
            </label>
            <Textarea
              value={testInput}
              onChange={(e) => setTestInput(e.target.value)}
              placeholder="Enter any text here to test your AI model..."
              className="min-h-[120px]"
            />
          </div>

          {/* Test button */}
          <Button 
            onClick={handleTest}
            disabled={isLoading || !testInput.trim()}
            className="w-full"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Test My AI
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Test results area */}
      {testResults.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-500" />
            Test Results
          </h3>
          <div>
            {testResults.map((result, index) => renderResult(result, index))}
          </div>
        </div>
      )}

      {/* Empty state hint */}
      {testResults.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="p-8 text-center">
            <TestTube className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Start Testing Your AI</h3>
            <p className="text-gray-600 mb-4">
              Enter any text to see how your trained AI responds
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AITester;