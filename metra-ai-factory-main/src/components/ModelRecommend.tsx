import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Brain, Zap, Database, Award, TrendingUp, Clock, ArrowRight, Info, Loader2, ServerCrash } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useConversationStore } from '@/stores/conversationStore';
import { useModelStore } from '@/stores/modelStore';
import { api } from '@/lib/api';

interface Model {
  id: string;
  name: string;
  provider: string;
  architecture: string;
  parameters: string;
  description: string;
  strengths: string[];
  weaknesses: string[];
  cost: string;
  speed: string;
  accuracy: string;
  recommended: boolean;
  expertOpinion: string;
  icon: string;
}

const ModelRecommend = () => {
  const { currentConversation } = useConversationStore();
  const { selectedModelId, setSelectedModelId, recommendations, setRecommendations } = useModelStore();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecommendations = async () => {
      // ... (logic to get taskSchema from conversationStore, same as before)

      try {
        const taskSchema = /* ... get schema ... */;
        const response = await api.post<Model[]>('/recommend', taskSchema);
        setRecommendations(response);
        if (response.length > 0) {
          setSelectedModelId(response[0].modelId);
        }
      } catch (err: any) {
        setError(err.message || "Failed to fetch model recommendations.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecommendations();
  }, [currentConversation, setRecommendations, setSelectedModelId]);

  const handleModelSelect = (modelId: string) => {
    setSelectedModelId(modelId);
  };

  const handleSelectModel = () => {
    // Navigate to data builder module
    console.log('Selected model:', selectedModelId);
  };

  const getSelectedModel = () => recommendations.find(m => m.modelId === selectedModelId);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
        <p className="ml-4 text-md">Analyzing your task and finding the best models...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <Alert variant="destructive">
          <ServerCrash className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      {/* Task summary */}
      <Card className="border-0 shadow-sm bg-purple-50/30">
        <CardContent className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <Brain className="h-5 w-5 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">Task Summary</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Task Type</p>
              <p className="font-medium">Classification</p>
            </div>
            <div>
              <p className="text-gray-500">Input Type</p>
              <p className="font-medium">Text</p>
            </div>
            <div>
              <p className="text-gray-500">Output Type</p>
              <p className="font-medium">Binary</p>
            </div>
            <div>
              <p className="text-gray-500">Data Amount</p>
              <p className="font-medium">Medium</p>
            </div>
            <div>
              <p className="text-gray-500">Language</p>
              <p className="font-medium">English</p>
            </div>
            <div>
              <p className="text-gray-500">Domain</p>
              <p className="font-medium">Customer Service</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Model recommendation list */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-gray-900">Recommended Open Source Models</h2>
          <Badge variant="outline" className="text-purple-600 border-purple-200 bg-purple-50/50">
            <Zap className="h-3 w-3 mr-1" />
            Smart Recommendation
          </Badge>
        </div>

        <RadioGroup value={selectedModelId || ''} onValueChange={setSelectedModelId}>
          <div className="space-y-4">
            {recommendations.map((model) => (
              <Label
                key={model.modelId}
                htmlFor={model.modelId}
                className="block cursor-pointer"
              >
                <Card className={`border-2 transition-all ${
                  selectedModelId === model.modelId 
                    ? 'border-gray-900 shadow-md bg-gray-900/5' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <RadioGroupItem value={model.modelId} id={model.modelId} className="mt-1" />
                      
                      <div className="flex-1 space-y-4">
                        {/* Model header info */}
                        <div className="flex items-start justify-between">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <h3 className="text-lg font-semibold text-gray-900">{model.name}</h3>
                              {model.recommended && (
                                <Badge className="bg-gray-900 text-white">
                                  <Award className="h-3 w-3 mr-1" />
                                  Recommended
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-gray-600">
                              {model.provider} • {model.parameters} parameters
                            </p>
                          </div>
                        </div>

                        {/* Model description */}
                        <p className="text-sm text-gray-600">{model.description}</p>

                        {/* Pros and cons */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm font-medium text-gray-700 mb-2">Strengths</p>
                            <ul className="space-y-1">
                              {model.strengths.map((strength, index) => (
                                <li key={index} className="text-sm text-gray-600 flex items-center gap-2">
                                  <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                                  {strength}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-700 mb-2">Considerations</p>
                            <ul className="space-y-1">
                              {model.weaknesses.map((weakness, index) => (
                                <li key={index} className="text-sm text-gray-600 flex items-center gap-2">
                                  <div className="w-1.5 h-1.5 bg-orange-400 rounded-full"></div>
                                  {weakness}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>

                        {/* Performance metrics */}
                        <div className="flex items-center gap-6 pt-2">
                          <div className="flex items-center gap-2">
                            <Database className="h-4 w-4 text-gray-400" />
                            <span className="text-sm text-gray-600">Training Cost: <span className="font-medium">{model.trainCost}</span></span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-gray-400" />
                            <span className="text-sm text-gray-600">Training Time: <span className="font-medium">{model.trainTime}</span></span>
                          </div>
                          <div className="flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-gray-400" />
                            <span className="text-sm text-gray-600">Estimated Accuracy: <span className="font-medium">{model.accuracy}</span></span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 text-green-700">
                          <Award className="h-4 w-4" />
                          <span className="text-sm font-medium">AI Expert Opinion</span>
                        </div>
                        <p className="text-sm text-gray-600">
                          {model.recommended 
                            ? "This model is perfect for your task. It offers the best balance between accuracy and efficiency for customer complaint classification."
                            : model.expertOpinion === 'positive'
                            ? "This is a solid alternative that can also work well for your needs, especially if you have resource constraints."
                            : "This model could work but may require more resources or data for optimal results."}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Label>
            ))}
          </div>
        </RadioGroup>
      </div>

      {/* Action buttons */}
      {selectedModelId && (
        <Card className="border-0 shadow-sm">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 mb-1">Selected Model</p>
                <p className="font-semibold text-gray-900">{getSelectedModel()?.name}</p>
              </div>
              <Button 
                onClick={handleSelectModel}
                className="bg-gray-900 hover:bg-gray-800"
              >
                Next: Prepare Training Data
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="border-0 shadow-sm">
        <CardContent className="p-6">
          <h3 className="text-lg font-semibold text-gray-900">Why BERT Base?</h3>
          <p className="text-sm text-gray-500">AI recommendation explanation</p>
          <Alert className="border-green-200 bg-green-50/50">
            <Info className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-sm text-gray-700">
              <strong>AI Analysis:</strong> Based on your text classification task with customer reviews, 
              BERT Base offers the best balance of accuracy (95%+) and training efficiency. Its pre-training 
              on massive text data makes it ideal for understanding customer sentiment nuances.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  );
};

export default ModelRecommend; 