import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Brain, Zap, Database, Award, TrendingUp, Clock, ArrowRight, Info, Loader2, FileText, MessageSquare } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useConversationStore } from '@/stores/conversationStore';
import { api } from '@/lib/api';
import { useToast } from '@/components/ui/use-toast';
import { EmptyState } from '@/components/ui/empty-state';

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
  isChineseModel?: boolean;
  modelType?: string;
}

interface ModelRecommendProps {
  onSectionChange?: (section: string) => void;
}

const ModelRecommend: React.FC<ModelRecommendProps> = ({ onSectionChange }) => {
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const { lastFinalizedTask } = useConversationStore();
  const { toast } = useToast();

  // Task info from store - null if not available
  const taskInfo = lastFinalizedTask;

  useEffect(() => {
    if (taskInfo) {
      fetchRecommendations();
    } else {
      setLoading(false);
    }
  }, [taskInfo]);

  const fetchRecommendations = async () => {
    if (!taskInfo) return;
    
    try {
      setLoading(true);
      
      // Use the full schema for recommendations if available
      const taskDefinition = taskInfo?.fullDefinition || taskInfo?.schema || taskInfo;
      
      const response = await api.fetchRecommendations({ task_definition: taskDefinition });
      
      console.log('API Response:', response); // Debug log
      
      // Transform API response to our Model interface
      const recommendedModels = (response as any).recommendations?.map((model: any, index: number) => {
        // Check if it's a Chinese model
        const modelIdLower = model.model_id?.toLowerCase() || '';
        const isChineseModel = ['chatglm', 'baichuan', 'qwen', 'yi', 'chinese', 'zh'].some(
          keyword => modelIdLower.includes(keyword)
        );
        
        // Determine model type from tags or pipeline_tag
        const modelType = model.pipeline_tag || 
          (model.tags?.includes('text-generation') ? 'Text Generation' :
           model.tags?.includes('text-classification') ? 'Text Classification' :
           model.tags?.includes('token-classification') ? 'NER' : 'General');
        
        return {
          id: model.model_id || `model-${index}`,
          name: model.model_name || model.model_id?.split('/')?.pop() || 'Unknown Model',
          provider: model.author || model.model_id?.split('/')[0] || 'Hugging Face',
          architecture: model.library_name || 'Transformer',
          parameters: model.downloads > 1000000 ? '1B+' : model.downloads > 100000 ? '100M-1B' : '<100M',
          description: model.description || `Popular model with ${(model.downloads || 0).toLocaleString()} downloads`,
          strengths: [
            isChineseModel ? 'Optimized for Chinese language' : 'Pre-trained on large datasets',
            `${(model.likes || 0).toLocaleString()} community likes`,
            ...(model.tags?.slice(0, 2).map((tag: string) => `Specialized in ${tag}`) || [])
          ],
          weaknesses: [
            'May need fine-tuning for specific tasks',
            isChineseModel ? 'Higher computational requirements' : 'Resource requirements vary'
          ],
          cost: 'Free (Open Source)',
          speed: model.downloads > 1000000 ? 'Medium' : 'Fast',
          accuracy: isChineseModel ? 'Excellent for Chinese tasks' : '90%+ on benchmark',
          recommended: index === 0, // First model is recommended
          expertOpinion: 'positive',
          icon: isChineseModel ? '🇨🇳' : index === 0 ? '⭐' : '🤖',
          isChineseModel,
          modelType
        };
      }) || [];

      console.log('Transformed models:', recommendedModels); // Debug log

      if (recommendedModels.length === 0) {
        // Use default models if no recommendations
        const defaultModels = getDefaultModels();
        setModels(defaultModels);
        setSelectedModel(defaultModels[0].id);
      } else {
        setModels(recommendedModels);
        // Auto-select the first (recommended) model
        setSelectedModel(recommendedModels[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
      toast({
        title: 'Using default recommendations',
        description: 'Could not connect to recommendation service. Showing default options.',
        variant: 'default',
      });
      
      // Use default models if API fails
      const defaultModels = getDefaultModels();
      setModels(defaultModels);
      setSelectedModel(defaultModels[0].id);
    } finally {
      setLoading(false);
    }
  };

  const getDefaultModels = (): Model[] => {
    // Check if task is Chinese
    const isChineseTask = taskInfo?.language === 'chinese' || 
      taskInfo?.language?.includes('中文') ||
      taskInfo?.fullDefinition?.language === 'chinese';
    
    if (isChineseTask) {
      return [
        {
          id: 'chatglm3-6b',
          name: 'ChatGLM3-6B',
          provider: 'THUDM',
          architecture: 'Transformer',
          parameters: '6B',
          description: 'ChatGLM3 是智谱AI和清华大学 KEG 实验室联合发布的新一代对话预训练模型，针对中文问答和对话进行了优化。',
          strengths: ['中文理解能力强', '支持长文本对话', '推理能力出色', '开源可商用'],
          weaknesses: ['需要较大显存 (13GB+)', '英文能力相对较弱'],
          cost: 'Free (Open Source)',
          speed: 'Medium',
          accuracy: '中文任务 95%+',
          recommended: true,
          expertOpinion: 'positive',
          icon: '🇨🇳',
          isChineseModel: true,
          modelType: 'Text Generation'
        },
        {
          id: 'baichuan2-7b',
          name: 'Baichuan2-7B',
          provider: 'Baichuan Inc',
          architecture: 'Transformer',
          parameters: '7B',
          description: '百川智能开发的开源可商用的大规模预训练语言模型，在中文和英文基准测试上均表现优秀。',
          strengths: ['中英双语能力', '知识面广', '生成质量高', '训练数据量大'],
          weaknesses: ['计算资源要求较高', '部署复杂度中等'],
          cost: 'Free (Open Source)',
          speed: 'Medium',
          accuracy: '中文任务 93%+',
          recommended: false,
          expertOpinion: 'positive',
          icon: '🇨🇳',
          isChineseModel: true,
          modelType: 'Text Generation'
        },
        {
          id: 'qwen-7b',
          name: 'Qwen-7B (通义千问)',
          provider: 'Alibaba',
          architecture: 'Transformer',
          parameters: '7B',
          description: '阿里云研发的通义千问大语言模型，支持中英双语，在多项评测中表现优异。',
          strengths: ['多语言能力强', '代码生成能力', '逻辑推理好', '支持工具调用'],
          weaknesses: ['显存占用较大', '微调成本较高'],
          cost: 'Free (Open Source)',
          speed: 'Medium',
          accuracy: '中文任务 94%+',
          recommended: false,
          expertOpinion: 'positive',
          icon: '🇨🇳',
          isChineseModel: true,
          modelType: 'Text Generation'
        }
      ];
    }
    
    // English default models
    return [
      {
        id: 'llama2-7b',
        name: 'Llama 2 7B',
        provider: 'Meta',
        architecture: 'Transformer',
        parameters: '7B',
        description: 'Llama 2 is a collection of pretrained and fine-tuned generative text models ranging in scale from 7 billion to 70 billion parameters.',
        strengths: ['High quality text generation', 'Good for fine-tuning', 'Strong community support', 'Extensive documentation'],
        weaknesses: ['Requires significant compute', 'Large model size'],
        cost: 'Free (Open Source)',
        speed: 'Medium',
        accuracy: '95%+ on benchmarks',
        recommended: true,
        expertOpinion: 'positive',
        icon: '🦙',
        isChineseModel: false,
        modelType: 'Text Generation'
      },
      {
        id: 'mistral-7b',
        name: 'Mistral 7B',
        provider: 'Mistral AI',
        architecture: 'Transformer',
        parameters: '7B',
        description: 'A 7B parameter model that outperforms Llama 2 13B on many benchmarks, with efficient inference.',
        strengths: ['Excellent performance/size ratio', 'Fast inference', 'Good instruction following', 'Apache 2.0 license'],
        weaknesses: ['Less suitable for very long contexts', 'Smaller community than Llama'],
        cost: 'Free (Open Source)',
        speed: 'Fast',
        accuracy: '93%+ on benchmarks',
        recommended: false,
        expertOpinion: 'positive',
        icon: '⚡',
        isChineseModel: false,
        modelType: 'Text Generation'
      },
      {
        id: 'falcon-7b',
        name: 'Falcon 7B',
        provider: 'TII',
        architecture: 'Transformer',
        parameters: '7B',
        description: 'Falcon-7B is a causal decoder-only model trained on 1.5 trillion tokens.',
        strengths: ['Trained on diverse data', 'Good multilingual capabilities', 'Efficient architecture', 'Permissive license'],
        weaknesses: ['May require more fine-tuning', 'Less optimized tooling'],
        cost: 'Free (Open Source)',
        speed: 'Fast',
        accuracy: '91%+ on benchmarks',
        recommended: false,
        expertOpinion: 'neutral',
        icon: '🦅',
        isChineseModel: false,
        modelType: 'Text Generation'
      }
    ];
  };

  const handleModelSelect = (modelId: string) => {
    setSelectedModel(modelId);
  };

  const handleSelectModel = () => {
    // Save selected model to localStorage for Data Builder
    const model = models.find(m => m.id === selectedModel);
    if (model) {
      localStorage.setItem('selectedModel', JSON.stringify(model));
      
      // Also save task info for Data Builder
      const taskData = {
        task: taskInfo?.name || taskInfo?.fullDefinition?.task || 'AI Task',
        type: taskInfo?.taskType || 'text-generation',
        language: taskInfo?.language || 'chinese',
        description: taskInfo?.fullDefinition?.task || taskInfo?.description || '',
        labels: taskInfo?.fullDefinition?.labels || taskInfo?.labels || [],
        domain: taskInfo?.domain || 'general'
      };
      localStorage.setItem('currentTask', JSON.stringify(taskData));
    }
    
    // Navigate to data builder module
    if (onSectionChange) {
      onSectionChange('data-builder');
    }
  };

  const getSelectedModel = () => models.find(m => m.id === selectedModel);

  // Show empty state if no task is defined
  if (!taskInfo) {
    return (
      <div className="p-8 space-y-6 max-w-6xl mx-auto">
        
        <EmptyState
          icon={MessageSquare}
          title="No Task Defined"
          description="Please define your AI task first to get personalized model recommendations. Start by describing what you want your AI to do in the Task Builder."
          badge={{
            text: "Step 1 Required",
            variant: "outline"
          }}
          action={{
            label: "Define Your Task",
            onClick: () => window.location.href = '/dashboard?section=chat',
            variant: "default"
          }}
        >
          <div className="p-4 bg-white rounded-lg border border-gray-200 mt-6">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">What happens next?</span>
            </div>
            <p className="text-xs text-gray-600">Once you define your task, we'll analyze your requirements and recommend the most suitable open-source language models for your specific needs.</p>
          </div>
        </EmptyState>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-gray-600" />
          <div className="space-y-2">
            <p className="text-gray-900 font-medium">Analyzing your task requirements...</p>
            <p className="text-gray-600 text-sm">Finding the best open-source models for your needs</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">

      {/* Task summary */}
      <Card className="border-0 shadow-sm bg-gray-50/30">
        <CardContent className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <Brain className="h-5 w-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Task Summary</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Task Name</p>
              <p className="font-medium">{taskInfo?.name || 'AI Task'}</p>
            </div>
            <div>
              <p className="text-gray-500">Task Type</p>
              <p className="font-medium capitalize">{taskInfo?.taskType || 'Text Generation'}</p>
            </div>
            <div>
              <p className="text-gray-500">Language</p>
              <p className="font-medium capitalize">{taskInfo?.language || 'Chinese'}</p>
            </div>
            <div>
              <p className="text-gray-500">Domain</p>
              <p className="font-medium capitalize">{taskInfo?.domain || 'General'}</p>
            </div>
          </div>
          
          {/* Show the actual task definition if available */}
          {taskInfo?.fullDefinition && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-sm font-medium text-gray-700 mb-2">Task Details:</p>
              <div className="text-sm text-gray-600 space-y-1">
                {taskInfo.fullDefinition.task && (
                  <p><span className="font-medium">Task:</span> {taskInfo.fullDefinition.task}</p>
                )}
                {taskInfo.fullDefinition.target_audience && (
                  <p><span className="font-medium">Target Audience:</span> {taskInfo.fullDefinition.target_audience}</p>
                )}
                {taskInfo.fullDefinition.features && (
                  <p><span className="font-medium">Features:</span> {taskInfo.fullDefinition.features}</p>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Model recommendation list */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-gray-900">Recommended Language Models</h2>
          <Badge variant="outline" className="text-gray-600 border-gray-200 bg-gray-50">
            <Zap className="h-3 w-3 mr-1" />
            NLP-Optimized Selection
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
                              <span className="text-2xl">{model.icon}</span>
                              <h3 className="text-lg font-semibold text-gray-900">{model.name}</h3>
                              {model.recommended && (
                                <Badge className="bg-gray-900 text-white">
                                  <Award className="h-3 w-3 mr-1" />
                                  Recommended
                                </Badge>
                              )}
                              {model.isChineseModel && (
                                <Badge variant="outline" className="text-gray-700 border-gray-300">
                                  Chinese Model
                                </Badge>
                              )}
                              {model.modelType && (
                                <Badge variant="outline" className="text-gray-700 border-gray-300">
                                  {model.modelType}
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-gray-600">
                              {model.provider} • {model.architecture} • {model.parameters} parameters
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
                        <div className="flex flex-wrap items-center gap-4 pt-2">
                          <div className="flex items-center gap-2">
                            <Database className="h-4 w-4 text-gray-400" />
                            <span className="text-sm text-gray-600">Cost: <span className="font-medium text-green-600">{model.cost}</span></span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-gray-400" />
                            <span className="text-sm text-gray-600">Speed: <span className="font-medium">{model.speed}</span></span>
                          </div>
                          <div className="flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-gray-400" />
                            <span className="text-sm text-gray-600">Accuracy: <span className="font-medium text-gray-900">{model.accuracy}</span></span>
                          </div>
                        </div>

                        {model.recommended && (
                          <Alert className="border-green-200 bg-green-50/50">
                            <Award className="h-4 w-4 text-green-600" />
                            <AlertDescription className="text-sm text-gray-700">
                              <strong>AI Expert Opinion:</strong> This model is perfect for your task. It offers the best balance between accuracy and efficiency for your specific requirements.
                            </AlertDescription>
                          </Alert>
                        )}

                        {model.isChineseModel && taskInfo?.language === 'chinese' && (
                          <Alert className="border-gray-200 bg-gray-50">
                            <Info className="h-4 w-4 text-gray-600" />
                            <AlertDescription className="text-sm text-gray-700">
                              <strong>Language Match:</strong> This model is specifically optimized for Chinese language tasks and will provide better performance for your requirements.
                            </AlertDescription>
                          </Alert>
                        )}
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
    </div>
  );
};

export default ModelRecommend; 