import React, { useEffect } from 'react';
import { useConversationStore } from '@/stores/conversationStore';
import { useModelStore } from '@/stores/modelStore';
import { api } from '@/lib/api';
import { ModelCard } from '@/components/ModelCard';
import SchemaDisplay from '@/components/SchemaDisplay';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Brain, Zap, Database, Award, TrendingUp, Clock, ArrowRight, Info } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

const ModelRecommend = () => {
  const navigate = useNavigate();
  const { lastFinalizedTask } = useConversationStore();
  const {
    recommendedModels,
    isLoading,
    error,
    setRecommendedModels,
    setLoading,
    setError,
    recommendations,
    selectedModelId,
    fetchRecommendations,
    selectModel,
  } = useModelStore();

  const currentConversation = useConversationStore((state) => state.currentConversation);
  
  const lastAiMessage = currentConversation?.messages.filter(m => m.role === 'assistant').pop();
  const schemaMatch = lastAiMessage?.content.match(/```json\s*([\s\S]*?)\s*```/);

  useEffect(() => {
    if (!lastFinalizedTask) {
      // If there's no task, maybe redirect to the task builder
      navigate('/');
      return;
    }

    const getRecommendations = async () => {
      setLoading(true);
      setError(null);
      try {
        const models = await api.fetchRecommendations(lastFinalizedTask);
        setRecommendedModels(models);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch model recommendations.');
      } finally {
        setLoading(false);
      }
    };

    getRecommendations();
  }, [lastFinalizedTask, setRecommendedModels, setLoading, setError, navigate]);

  useEffect(() => {
    if (schemaMatch) {
      try {
        const schema = JSON.parse(schemaMatch[1]);
        fetchRecommendations(schema);
      } catch (e) {
        console.error("Failed to parse task definition schema:", e);
      }
    }
  }, [schemaMatch, fetchRecommendations]);

  const handleSelectModel = () => {
    navigate('/data-builder');
  };

  const getSelectedModel = () => recommendations.find(m => m.modelId === selectedModelId);

  if (isLoading) {
    return (
      <div className="p-8 space-y-6 max-w-6xl mx-auto">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-8 max-w-6xl mx-auto">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      {/* Recommended Open Source Models section */}
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold">Recommended Models</h2>
        <RadioGroup value={selectedModelId || ''} onValueChange={selectModel}>
          <div className="space-y-4">
            {recommendations.map((model) => (
              <Label key={model.modelId} htmlFor={model.modelId} className="block cursor-pointer">
                <Card className={`border-2 transition-all ${selectedModelId === model.modelId ? 'border-gray-900' : 'border-gray-200'}`}>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <RadioGroupItem value={model.modelId} id={model.modelId} />
                      <div className="flex-1 space-y-4">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="text-lg font-semibold">{model.name}</h3>
                            <p className="text-sm text-gray-600">{model.provider} • {model.parameters} parameters</p>
                          </div>
                          {model.recommended && <Badge>Recommended</Badge>}
                        </div>
                        <p className="text-sm">{model.description}</p>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="font-medium">Strengths</p>
                            <ul>{model.strengths.map(s => <li key={s}>{s}</li>)}</ul>
                          </div>
                          <div>
                            <p className="font-medium">Considerations</p>
                            <ul>{model.weaknesses.map(w => <li key={w}>{w}</li>)}</ul>
                          </div>
                        </div>
                        <div className="flex items-center gap-6">
                          <span>Cost: {model.trainCost}</span>
                          <span>Time: {model.trainTime}</span>
                          <span>Accuracy: {model.accuracy}</span>
                        </div>
                        <div>
                          <p className="font-medium">AI Expert Opinion</p>
                          <p>{model.expertOpinion}</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Label>
            ))}
          </div>
        </RadioGroup>
      </div>

      {/* Action buttons section */}
      {selectedModelId && (
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p>Selected Model</p>
              <p className="font-semibold">{getSelectedModel()?.name}</p>
            </div>
            <Button onClick={handleSelectModel}>
              Next: Prepare Training Data <ArrowRight className="ml-2" />
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ModelRecommend; 