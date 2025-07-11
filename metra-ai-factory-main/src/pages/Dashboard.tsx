import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import TaskBuilder from '@/components/TaskBuilder';
import ModelRecommend from '@/components/ModelRecommend';
import DataBuilder from '@/components/DataBuilder';
import DataEngine from '@/components/DataEngine';
import ModelBuilder from '@/components/ModelBuilder';
import ModelMarket from '@/components/ModelMarket';
import DeployedModels from '@/components/DeployedModels';
import UserProfile from '@/components/UserProfile';
import TrainingProcess from '@/components/TrainingProcess';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Activity, MessageSquare, Layers, Database, Sparkles, Rocket, Package, Store, Loader2, LogOut, User, Cpu, Clock } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { api } from '@/lib/api';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/components/ui/use-toast';

interface UsageStats {
  models_created_this_month: number;
  api_calls_this_month: number;
  training_minutes_this_month: number;
  models_remaining: number;
  api_calls_remaining: number;
  training_minutes_remaining: number;
}

const Dashboard = () => {
  const [activeSection, setActiveSection] = useState('prompt-schema');
  const [showTrainingProcess, setShowTrainingProcess] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user, logout } = useAuthStore();
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUsageStats();
  }, []);

  const loadUsageStats = async () => {
    try {
      const stats = await api.getUsageStats();
      setUsage(stats);
    } catch (error) {
      toast({
        title: 'Error loading usage stats',
        description: error instanceof Error ? error.message : 'Something went wrong',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    toast({
      title: 'Logged out',
      description: 'You have been successfully logged out.',
    });
  };

  const renderContent = () => {
    if (showTrainingProcess) {
      return <TrainingProcess onBack={() => setShowTrainingProcess(false)} />;
    }

    switch (activeSection) {
      case 'prompt-schema':
        return <TaskBuilder onSectionChange={setActiveSection} />;
      case 'model-recommend':
        return <ModelRecommend onSectionChange={setActiveSection} />;
      case 'data-builder':
        return <DataBuilder />;
      case 'data-engine':
        return <DataEngine />;
      case 'model-training':
        return <ModelBuilder />;
      case 'model-deploy':
        return <DeployedModels />;
      case 'model-market':
        return <ModelMarket />;
      case 'profile':
        return <UserProfile />;
      default:
        return <TaskBuilder onSectionChange={setActiveSection} />;
    }
  };

  const getSectionTitle = () => {
    if (showTrainingProcess) return 'Model Training Progress';
    
    switch (activeSection) {
      case 'prompt-schema':
        return 'Task Definition';
      case 'model-recommend':
        return 'Model Recommendation';
      case 'data-builder':
        return 'Data Builder';
      case 'data-engine':
        return 'Data Fusion Engine';
      case 'model-training':
        return 'Training Center';
      case 'model-deploy':
        return 'Model Deployment';
      case 'model-market':
        return 'Model Marketplace';
      case 'profile':
        return 'Account Settings';
      default:
        return 'Task Definition';
    }
  };

  const getSectionDescription = () => {
    if (showTrainingProcess) return 'Monitor your language model fine-tuning progress in real-time';
    
    switch (activeSection) {
      case 'prompt-schema':
        return 'Define your NLP task - text generation, classification, Q&A, summarization, or custom tasks';
      case 'model-recommend':
        return 'Get matched with the best language model - GPT, BERT, T5, LLaMA, or domain-specific LLMs';
      case 'data-builder':
        return 'Collect text data via web scraping, synthetic generation, or upload your text files';
      case 'data-engine':
        return 'Intelligent text processing - tokenization, formatting, and dataset preparation for LLM training';
      case 'model-training':
        return 'Fine-tune language models with LoRA or full fine-tuning for your specific NLP task';
      case 'model-deploy':
        return 'Deploy as text generation API, chatbot interface, or export for local inference';
      case 'model-market':
        return 'Share your fine-tuned language models and monetize your NLP solutions';
      case 'profile':
        return 'Manage your account information and usage';
      default:
        return 'Define your NLP task through natural conversation';
    }
  };

  const getSectionIcon = () => {
    switch (activeSection) {
      case 'prompt-schema':
        return MessageSquare;
      case 'model-recommend':
        return Layers;
      case 'data-builder':
        return Database;
      case 'data-engine':
        return Sparkles;
      case 'model-training':
        return Rocket;
      case 'model-deploy':
        return Package;
      case 'model-market':
        return Store;
      default:
        return MessageSquare;
    }
  };

  const SectionIcon = getSectionIcon();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex w-full">
      <Sidebar activeSection={activeSection} setActiveSection={setActiveSection} />
      
      <main className="flex-1 flex flex-col ml-72">
        <div className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-6xl mx-auto space-y-8">
            {/* Header */}
            <header className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-4xl font-semibold text-gray-900 mb-3">Metra Language Model Platform</h1>
                  <p className="text-gray-600 text-lg">Fine-tune open-source language models for text generation, classification, and NLP tasks</p>
                </div>
                <div className="flex items-center gap-4">
                  <Button 
                    variant="outline" 
                    onClick={() => setShowTrainingProcess(true)}
                    className="flex items-center gap-2 px-4 py-2 h-10 border-gray-300 hover:bg-gray-50 transition-colors"
                  >
                    <Activity className="h-4 w-4" />
                    <span>View Training</span>
                  </Button>
                  <div className="px-4 py-2 bg-purple-50/50 rounded-lg border border-purple-200">
                    <span className="text-sm font-medium text-purple-700">Credits: 3 models/month</span>
                  </div>
                </div>
              </div>
              
              {/* Section Info Card */}
              <Card className="border border-gray-200 shadow-sm bg-white">
                <CardContent className="p-6">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                      <SectionIcon className="h-6 w-6 text-gray-700" />
                    </div>
                    <div>
                      <h2 className="text-xl font-medium text-gray-900 mb-2">{getSectionTitle()}</h2>
                      <p className="text-gray-600">{getSectionDescription()}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </header>
            
            {/* Main Content */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              {renderContent()}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
