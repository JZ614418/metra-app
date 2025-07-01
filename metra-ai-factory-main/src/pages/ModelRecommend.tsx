import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Brain, Zap, Database, Award, TrendingUp, Clock, ArrowRight, Info } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

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
  const [selectedModel, setSelectedModel] = useState<string>('bert-base');

  // Task info retrieved from previous step
  const taskInfo = {
    taskType: 'classification',
    inputType: 'text',
    outputType: 'binary',
    dataAmount: 'medium',
    language: 'english',
    domain: 'customer_service'
  };

  const models = [
    {
      id: 'bert-base',
      name: 'BERT Base',
      provider: 'Google',
      architecture: 'Transformer',
      parameters: '110M',
      strengths: ['High accuracy for text classification', 'Good for sentiment analysis', 'Pre-trained on large corpus'],
      weaknesses: ['Higher computational requirements', 'Larger model size'],
      recommendScore: 95,
      trainTime: '~30 min',
      trainCost: '$5-10',
      recommended: true,
      expertOpinion: 'positive',
      icon: '🤖'
    },
    {
      id: 'distilbert',
      name: 'DistilBERT',
      provider: 'Hugging Face',
      architecture: 'Distilled Transformer',
      parameters: '66M',
      strengths: ['40% smaller than BERT', '60% faster', 'Maintains 97% of BERT performance'],
      weaknesses: ['Slightly lower accuracy', 'Less suitable for complex tasks'],
      recommendScore: 88,
      trainTime: '~20 min',
      trainCost: '$3-5',
      recommended: false,
      expertOpinion: 'positive',
      icon: '⚡'
    },
    {
      id: 'roberta',
      name: 'RoBERTa',
      provider: 'Facebook',
      architecture: 'Optimized BERT',
      parameters: '125M',
      strengths: ['Better than BERT on many tasks', 'Robust training approach', 'Excellent for classification'],
      weaknesses: ['Requires more training data', 'Longer training time'],
      recommendScore: 82,
      trainTime: '~45 min',
      trainCost: '$8-15',
      recommended: false,
      expertOpinion: 'neutral',
      icon: '🔬'
    }
  ];

  const handleModelSelect = (modelId: string) => {
    setSelectedModel(modelId);
  };

  const handleSelectModel = () => {
    // Navigate to data builder module
    console.log('Selected model:', selectedModel);
  };

  const getSelectedModel = () => models.find(m => m.id === selectedModel);

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

        <RadioGroup value={selectedModel} onValueChange={handleModelSelect}>
          <div className="space-y-4">
            {models.map((model) => (
              <Label
                key={model.id}
                htmlFor={model.id}
                className="block cursor-pointer"
              >
                <Card className={`border-2 transition-all ${
                  selectedModel === model.id 
                    ? 'border-gray-900 shadow-md bg-gray-900/5' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <RadioGroupItem value={model.id} id={model.id} className="mt-1" />
                      
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
      {selectedModel && (
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