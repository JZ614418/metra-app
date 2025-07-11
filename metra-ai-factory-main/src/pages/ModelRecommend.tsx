import React, { useEffect } from 'react';
import { useConversationStore } from '@/stores/conversationStore';
import { useModelStore } from '@/stores/modelStore';
import { api } from '@/lib/api';
import { ModelCard } from '@/components/ModelCard';
import SchemaDisplay from '@/components/SchemaDisplay';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertCircle, Sparkles, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const ModelRecommend = () => {
  const navigate = useNavigate();
  const { lastFinalizedTask } = useConversationStore();
  const {
    recommendedModels,
    isLoading,
    error,
    searchKeywords,
    setRecommendedModels,
    setLoading,
    setError,
    setSearchKeywords,
  } = useModelStore();

  useEffect(() => {
    if (!lastFinalizedTask) {
      // If there's no task, redirect to the task builder
      navigate('/');
      return;
    }

    const getRecommendations = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.fetchRecommendations(lastFinalizedTask);
        setRecommendedModels(response.recommendations);
        setSearchKeywords(response.search_keywords);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch model recommendations.');
      } finally {
        setLoading(false);
      }
    };

    getRecommendations();
  }, [lastFinalizedTask, setRecommendedModels, setLoading, setError, setSearchKeywords, navigate]);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-2">
          <Sparkles className="h-8 w-8 text-purple-600" />
          <h1 className="text-3xl font-bold">Smart Model Recommendations</h1>
        </div>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Based on your task definition, our AI has analyzed your requirements and found the most suitable open-source models from Hugging Face Hub.
        </p>
      </div>

      {/* Task Summary */}
      <Card className="border-purple-200 bg-purple-50/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>Your Task Definition</span>
            <Badge variant="secondary">Analyzed</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {lastFinalizedTask ? (
            <SchemaDisplay schema={lastFinalizedTask} />
          ) : (
            <p className="text-gray-500">No task definition found.</p>
          )}
        </CardContent>
      </Card>

      {/* AI Search Keywords */}
      {searchKeywords && !isLoading && (
        <Card className="border-gray-200 bg-gray-50/50">
          <CardContent className="p-6">
            <div className="flex items-start gap-3">
              <Search className="h-5 w-5 text-gray-600 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-700 mb-2">
                  AI-Generated Search Strategy
                </p>
                <p className="text-sm text-gray-600">
                  Our AI analyzed your task and searched for models using these keywords:
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {searchKeywords.split(',').map((keyword, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {keyword.trim()}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Loading State */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <Loader2 className="w-12 h-12 animate-spin text-purple-600" />
          <p className="text-gray-600">Analyzing your requirements and searching for the best models...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Model Recommendations */}
      {!isLoading && !error && recommendedModels.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Top {recommendedModels.length} Recommended Models</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendedModels.map((model) => (
              <ModelCard key={model.model_id} model={model} />
            ))}
          </div>
        </div>
      )}

      {/* No results */}
      {!isLoading && !error && recommendedModels.length === 0 && (
        <Card className="border-orange-200 bg-orange-50/30">
          <CardContent className="p-6">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                No models found matching your specific requirements. This might be because your task is very specialized. 
                Try simplifying your requirements or contact support for assistance.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ModelRecommend; 