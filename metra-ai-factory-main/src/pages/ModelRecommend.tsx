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
  } = useModelStore();

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

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold">Model Recommendations</h1>
        <p className="text-muted-foreground mt-2">
          Based on your task definition, here are the top 5 open-source models we recommend.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Your Task Definition Summary</CardTitle>
        </CardHeader>
        <CardContent>
          {lastFinalizedTask ? (
            <SchemaDisplay schema={lastFinalizedTask} />
          ) : (
            <p className="text-muted-foreground">No task definition found.</p>
          )}
        </CardContent>
      </Card>
      
      {isLoading && (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="w-12 h-12 animate-spin text-primary" />
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!isLoading && !error && recommendedModels.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recommendedModels.map((model) => (
            <ModelCard key={model.modelId} model={model} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ModelRecommend; 