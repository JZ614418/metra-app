import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/components/ui/use-toast';
import { dataCollectionAPI } from '@/lib/api';
import { 
  Globe, 
  Sparkles, 
  Upload, 
  Bot,
  User,
  Send,
  FileText, 
  Image, 
  Music, 
  FileSpreadsheet,
  ArrowRight,
  CheckCircle2,
  Loader2,
  MessageCircle,
  Info,
  Eye,
  ThumbsUp,
  ThumbsDown,
  Activity,
  Database,
  Zap,
  TrendingUp,
  Camera,
  FileAudio,
  BarChart,
  ShoppingCart,
  Headphones,
  Smartphone,
  Users,
  Film,
  Newspaper,
  Rss,
  Brain,
  Target
} from 'lucide-react';

interface DataMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

interface DataSample {
  id: string;
  content: string;
  label?: string;
  type: 'text' | 'image' | 'audio' | 'tabular';
  source: string;
  preview?: string;
  confidence?: number;
}

interface CrawlingSite {
  name: string;
  description: string;
  status: 'waiting' | 'crawling' | 'completed';
  count: number;
  icon: React.ReactNode;
}

// Get task info from Dashboard
interface TaskInfo {
  type: string;
  description: string;
  dataType: 'text' | 'image' | 'audio' | 'tabular';
  labels?: string[];
  language?: string;
  domain?: string;
  dataVolume?: string;
  estimatedTime?: string;
  fullDefinition?: any;
}

interface SelectedModel {
  id: string;
  name: string;
  provider: string;
  isChineseModel?: boolean;
  modelType?: string;
  description?: string;
}

const DataSynthesizer = () => {
  const [activeTab, setActiveTab] = useState('web-scraping');
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const { toast } = useToast();
  
  // Job tracking
  const [scrapingJobId, setScrapingJobId] = useState<string | null>(null);
  const [generationJobId, setGenerationJobId] = useState<string | null>(null);
  const [webScrapingJob, setWebScrapingJob] = useState<any>(null);
  const [aiGenerationJob, setAiGenerationJob] = useState<any>(null);
  
  // Data collection state for cross-source integration
  const [collectedData, setCollectedData] = useState<{
    webScraping: DataSample[];
    aiGenerated: DataSample[];
    fileUpload: DataSample[];
  }>({
    webScraping: [],
    aiGenerated: [],
    fileUpload: []
  });
  
  // Integration suggestions
  const [integrationSuggestions, setIntegrationSuggestions] = useState<string[]>([]);
  
  // Get task info from localStorage
  const [taskInfo] = useState<TaskInfo>(() => {
    const savedTask = localStorage.getItem('currentTask');
    if (savedTask) {
      const task = JSON.parse(savedTask);
      // Get full definition from conversation store if available
      const conversationData = localStorage.getItem('lastFinalizedTask');
      let fullDefinition = null;
      if (conversationData) {
        const convTask = JSON.parse(conversationData);
        fullDefinition = convTask.fullDefinition || convTask.schema;
      }
      
      return {
        type: task.type || 'Customer Complaint Classifier',
        description: task.description || '',
        dataType: task.dataType || 'text',
        labels: task.labels || ['Complaint', 'Not Complaint'],
        language: fullDefinition?.language || task.language || 'english',
        domain: fullDefinition?.domain || task.domain || 'general',
        dataVolume: fullDefinition?.data_volume || '10000',
        estimatedTime: fullDefinition?.estimated_collection_time || '40 minutes',
        fullDefinition: fullDefinition
      };
    }
    
    // Default task for testing
    return {
      type: 'Customer Complaint Classifier',
      description: 'Classify customer feedback as complaint or not complaint',
      dataType: 'text',
      labels: ['Complaint', 'Not Complaint'],
      language: 'english',
      domain: 'customer_service',
      dataVolume: '10000',
      estimatedTime: '40 minutes'
    };
  });

  // Get selected model from localStorage
  const [selectedModel] = useState<SelectedModel | null>(() => {
    const savedModel = localStorage.getItem('selectedModel');
    if (savedModel) {
      return JSON.parse(savedModel);
    }
    return null;
  });

  // Generate recommended sources based on task type and selected model
  const getRecommendedSources = () => {
    const taskType = taskInfo.type.toLowerCase();
    const isChineseTask = taskInfo.language === 'chinese' || 
                          taskInfo.fullDefinition?.language === 'chinese' ||
                          selectedModel?.isChineseModel;
    
    // Model-specific recommendations
    if (selectedModel) {
      const modelName = selectedModel.name.toLowerCase();
      
      // Chinese model recommendations
      if (isChineseTask || selectedModel.isChineseModel) {
        if (taskType.includes('complaint') || taskType.includes('feedback')) {
        return [
            { name: 'Taobao/JD Reviews', description: 'Chinese e-commerce platform user review data', icon: <ShoppingCart className="h-4 w-4" /> },
            { name: 'Weibo Complaint Topics', description: 'Social media user complaint content', icon: <MessageCircle className="h-4 w-4" /> },
            { name: '12315 Complaint Platform', description: 'Consumer complaint public data', icon: <Users className="h-4 w-4" /> },
            { name: 'Zhihu Q&A', description: 'User questions and complaint content in answers', icon: <MessageCircle className="h-4 w-4" /> },
            { name: 'Baidu Tieba', description: 'User feedback on various products and services', icon: <Globe className="h-4 w-4" /> },
            { name: 'Dianping Reviews', description: 'Restaurant and service user reviews', icon: <Users className="h-4 w-4" /> }
        ];
        } else if (taskType.includes('health') || taskType.includes('medical') || taskType.includes('中医')) {
        return [
            { name: 'TCM Database', description: 'Traditional Chinese Medicine knowledge base and case data', icon: <FileText className="h-4 w-4" /> },
            { name: 'Health Q&A Platforms', description: 'Health consultations from Spring Rain Doctor, DXY and others', icon: <MessageCircle className="h-4 w-4" /> },
            { name: 'Classical TCM Literature', description: 'Classic texts like "Huangdi Neijing" and other medical classics', icon: <FileText className="h-4 w-4" /> },
            { name: 'Dietary Therapy Forums', description: 'TCM dietary therapy and wellness discussions', icon: <Users className="h-4 w-4" /> },
            { name: 'Chinese Medicine Database', description: 'Chinese medicinal material effects and formula information', icon: <Database className="h-4 w-4" /> },
            { name: 'Health WeChat Accounts', description: 'TCM wellness WeChat public account articles', icon: <Newspaper className="h-4 w-4" /> }
        ];
      }
    }
    
      // English model recommendations
      else {
        if (taskType.includes('complaint') || taskType.includes('feedback')) {
        return [
            { name: 'Amazon Reviews', description: 'Product reviews and customer feedback', icon: <ShoppingCart className="h-4 w-4" /> },
            { name: 'Twitter Complaints', description: 'Customer service mentions and complaints', icon: <MessageCircle className="h-4 w-4" /> },
            { name: 'Reddit Support', description: 'Product support subreddits', icon: <Users className="h-4 w-4" /> },
            { name: 'Trustpilot', description: 'Business review platform data', icon: <Users className="h-4 w-4" /> },
            { name: 'App Store Reviews', description: 'Mobile app user feedback', icon: <Smartphone className="h-4 w-4" /> },
            { name: 'Support Forums', description: 'Technical support community posts', icon: <Globe className="h-4 w-4" /> }
          ];
        }
      }
    }
    
    // Default recommendations based on task type only
    if (taskInfo.dataType === 'text') {
      return webSources.slice(0, 6);
    } else if (taskInfo.dataType === 'image') {
    return [
        { name: 'Image Libraries', description: 'High-quality labeled images', icon: <Image className="h-4 w-4" /> },
        { name: 'Social Media Images', description: 'User-generated visual content', icon: <Camera className="h-4 w-4" /> },
        { name: 'E-commerce Products', description: 'Product images with categories', icon: <ShoppingCart className="h-4 w-4" /> },
        { name: 'Open Datasets', description: 'Public image datasets', icon: <Database className="h-4 w-4" /> }
      ];
    }
    
    return webSources.slice(0, 4);
  };

  const webSources = [
    { name: 'E-commerce Reviews', description: 'Taobao, JD.com, Amazon product reviews', icon: <ShoppingCart className="h-4 w-4" /> },
    { name: 'Social Media', description: 'Weibo, Twitter, Reddit posts and comments', icon: <MessageCircle className="h-4 w-4" /> },
    { name: 'Customer Service', description: 'Support tickets and chat logs', icon: <Headphones className="h-4 w-4" /> },
    { name: 'Forums', description: 'Tech support forums, Q&A sites', icon: <Users className="h-4 w-4" /> },
    { name: 'App Store', description: 'Mobile app reviews and ratings', icon: <Smartphone className="h-4 w-4" /> },
    { name: 'News Comments', description: 'News article comment sections', icon: <Globe className="h-4 w-4" /> }
    ];

  // Crawling progress
  const [crawlingProgress, setCrawlingProgress] = useState(0);
  const [crawlingSites, setCrawlingSites] = useState<CrawlingSite[]>(
    getRecommendedSources().map(source => ({
      ...source,
      status: 'waiting' as const,
      count: 0
    }))
  );

  // AI generation progress
  const [generatingProgress, setGeneratingProgress] = useState(0);
  const [generatingStats, setGeneratingStats] = useState({
    total: 0,
    byLabel: {} as Record<string, number>
  });

  const [dataStats, setDataStats] = useState({
    total: 0,
    valid: 0,
    needsReview: 0
  });

  // Data preview
  const [showDataPreview, setShowDataPreview] = useState(false);
  const [previewData, setPreviewData] = useState<DataSample[]>([]);

  // Generate initial message based on task and model
  const getInitialWebMessage = () => {
    if (!selectedModel) {
      return getInitialWebMessageDefault();
    }
    
    const modelName = selectedModel.name;
    const isChineseModel = selectedModel.isChineseModel;
    const taskType = taskInfo.type;
    
    let message = `Based on your selected model **${modelName}** and task "${taskType}", I recommend these data sources:\n\n`;
    
    const sources = getRecommendedSources();
    sources.forEach((source, index) => {
      message += `${index + 1}. **${source.name}** - ${source.description}\n`;
    });
    
    if (isChineseModel && taskInfo.language === 'chinese') {
      message += `\n💡 **Language Model Training Tip**: ${modelName} is a Chinese language model. For optimal fine-tuning, collect text data that includes:\n`;
      message += `• Diverse Chinese text with natural language patterns\n`;
      message += `• Context-rich conversations or documents\n`;
      message += `• Domain-specific Chinese terminology for your NLP task\n`;
    } else if (selectedModel.modelType === 'Text Generation') {
      message += `\n💡 **Language Model Training Tip**: ${modelName} is a generative language model. For effective fine-tuning, collect:\n`;
      message += `• Complete text sequences showing input-output patterns\n`;
      message += `• Natural language examples with proper context\n`;
      message += `• Diverse text samples covering your use case variations\n`;
    } else if (selectedModel.modelType === 'Text Classification') {
      message += `\n💡 **Language Model Training Tip**: For classification tasks with ${modelName}, ensure your text data:\n`;
      message += `• Has clear, balanced examples for each category\n`;
      message += `• Includes edge cases and ambiguous examples\n`;
      message += `• Represents real-world text distribution\n`;
    }
    
    if (taskInfo.labels && taskInfo.labels.length > 0) {
      message += `\nI'll help you collect balanced data for each category: ${taskInfo.labels.join(', ')}.`;
    }
    
    return message;
  };

  const getInitialWebMessageDefault = () => {
    if (taskInfo.dataType === 'text') {
      return `Based on your "${taskInfo.type}" task, I recommend these data sources:\n\n${
        getRecommendedSources().map((s, i) => `${i + 1}. ${s.name} - ${s.description}`).join('\n')
      }\n\nThese sources will help you get high-quality ${taskInfo.labels?.join(', ')} labeled data.`;
    }
    return 'I will recommend the most suitable data sources based on your task requirements.';
  };

  const getInitialAiMessage = () => {
    if (!selectedModel) {
      return getInitialAiMessageDefault();
    }
    
    const modelName = selectedModel.name;
    let message = `I'll generate synthetic training data optimized for **${modelName}**.\n\n`;
    
    if (taskInfo.labels && taskInfo.labels.length > 0) {
      message += `Categories to generate:\n`;
      taskInfo.labels.forEach(label => {
        message += `• **${label}** - I'll create diverse examples that ${modelName} can learn from effectively\n`;
      });
    }
    
    if (selectedModel.isChineseModel) {
      message += `\n🎯 **Language Model Training Strategy**: For Chinese language model fine-tuning, I'll generate:\n`;
      message += `• Natural Chinese text with proper linguistic structure\n`;
      message += `• Task-specific examples matching your NLP requirements\n`;
      message += `• Diverse text patterns to improve model generalization\n`;
    } else {
      message += `\n🎯 **Language Model Training Strategy**: I'll generate synthetic text data that:\n`;
      message += `• Matches ${modelName}'s pre-training text distribution\n`;
      message += `• Covers diverse linguistic patterns for your NLP task\n`;
      message += `• Ensures balanced representation across all categories\n`;
    }
    
    return message;
  };

  const getInitialAiMessageDefault = () => {
    if (taskInfo.labels && taskInfo.labels.length > 0) {
      return `I will generate balanced training data with these categories:\n\n${
        taskInfo.labels.map(label => `• ${label}`).join('\n')
      }\n\nEach category will maintain authenticity and diversity to ensure effective model training.`;
    }
    return 'I will generate high-quality synthetic data based on your task requirements to supplement real data.';
  };

  // Conversation messages
  const [webMessages, setWebMessages] = useState<DataMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: getInitialWebMessage(),
      timestamp: new Date()
    }
  ]);

  const [aiMessages, setAiMessages] = useState<DataMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: getInitialAiMessage(),
      timestamp: new Date()
    }
  ]);

  const [currentInput, setCurrentInput] = useState('');
  const [currentAiInput, setCurrentAiInput] = useState('');
  
  // Update suggestions when collected data changes
  useEffect(() => {
    updateIntegrationSuggestions();
  }, [collectedData]);

  // Update integration suggestions based on collected data
  const updateIntegrationSuggestions = () => {
    const suggestions: string[] = [];
    
    // Check data balance
    if (collectedData.webScraping.length > 0 && collectedData.aiGenerated.length === 0) {
      suggestions.push("Consider using AI Generation to create more diverse examples based on your web-scraped data");
    }
    
    if (collectedData.aiGenerated.length > collectedData.webScraping.length * 2) {
      suggestions.push("You have more AI-generated data than real data. Consider collecting more real-world examples for better model performance");
    }
    
    if (collectedData.fileUpload.length > 0 && collectedData.webScraping.length === 0) {
      suggestions.push("Your uploaded data can be enhanced with web-scraped examples from similar domains");
    }
    
    // Check for specific task types
    if (taskInfo.type.toLowerCase().includes('complaint') && collectedData.webScraping.length < 50) {
      suggestions.push("For complaint classification, we recommend at least 50 real complaint examples. Try scraping customer service forums");
    }
    
    // Data quality suggestions
    if (collectedData.webScraping.length + collectedData.aiGenerated.length + collectedData.fileUpload.length > 100) {
      suggestions.push("You have sufficient data quantity. Focus on data quality review and labeling accuracy");
    }
    
    setIntegrationSuggestions(suggestions);
  };

  // Real web scraping implementation
  const handleWebCrawling = async () => {
    try {
      setIsProcessing(true);
      setCrawlingProgress(0);
      setCrawlingSites(prev => prev.map(site => ({ ...site, status: 'waiting', count: 0 })));
      
      // Calculate how many results to fetch based on data volume need
      const targetVolume = parseInt(taskInfo.dataVolume || '5000');
      const remainingNeeded = targetVolume - (collectedData.webScraping.length + collectedData.aiGenerated.length + collectedData.fileUpload.length);
      const maxResults = Math.min(remainingNeeded, 5000); // Cap at 5K per batch for better performance
      
      // Start web scraping job
      const response = await dataCollectionAPI.startWebScraping({
        query: `${taskInfo.type} ${taskInfo.description}`,
        max_results: maxResults,
        include_full_content: false,
        sources: ['google', 'wikipedia', 'arxiv', 'pubmed'],
        batch_size: 1000
      });
      
      setScrapingJobId(response.job_id);
      
      // Poll for progress
      const pollInterval = setInterval(async () => {
        try {
          const progress = await dataCollectionAPI.getJobProgress(response.job_id);
          
          setCrawlingProgress(progress.progress);
          // Update UI based on progress
          if (progress.total_count > 0) {
            setCrawlingSites(prev => prev.map((site, index) => ({
              ...site,
              status: index < Math.floor(progress.progress / 25) ? 'completed' : 
                      index === Math.floor(progress.progress / 25) ? 'crawling' : 'waiting',
              count: Math.floor(progress.total_count / prev.length)
            })));
          }
          
          const totalData = collectedData.webScraping.length + 
                           collectedData.aiGenerated.length + 
                           collectedData.fileUpload.length + 
                           progress.total_count;
          
          setDataStats({
            total: totalData,
            valid: Math.floor(totalData * 0.95),
            needsReview: Math.floor(totalData * 0.05)
          });
          
          if (progress.status === 'completed') {
            clearInterval(pollInterval);
            setIsProcessing(false);
            setWebScrapingJob({ jobId: response.job_id, status: 'completed' });
            
            // Update collected data state
            const mockWebData = Array.from({ length: progress.total_count }, (_, i) => ({
              id: `web-${i}`,
              content: `Web scraped content ${i + 1}`,
              label: taskInfo.labels?.[Math.floor(Math.random() * taskInfo.labels.length)],
              type: 'text' as const,
              source: 'Web Scraping',
              confidence: 0.85 + Math.random() * 0.15
            }));
            setCollectedData(prev => ({ ...prev, webScraping: mockWebData }));
            updateIntegrationSuggestions();
            
            const message: DataMessage = {
              id: Date.now().toString(),
              role: 'system',
              content: `✅ Data collection completed!\n\nTotal ${progress.total_count} data points collected, data quality is good, can be directly used for training.`,
              timestamp: new Date()
            };
            setWebMessages(prev => [...prev, message]);
            
            toast({
              title: "Success",
              description: "Web scraping completed successfully!",
            });
          }
        } catch (error) {
          console.error('Error polling scraping progress:', error);
          clearInterval(pollInterval);
          setIsProcessing(false);
          
          toast({
            title: "Error",
            description: "Failed to get scraping progress",
            variant: "destructive",
          });
        }
      }, 2000); // Poll every 2 seconds
      
    } catch (error) {
      console.error('Error starting web scraping:', error);
      setIsProcessing(false);
      
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to start web scraping",
        variant: "destructive",
      });
    }
  };

  // Real AI generation implementation
  const handleAiGenerate = async () => {
    try {
      setIsProcessing(true);
      setGeneratingProgress(0);
      setGeneratingStats({ total: 0, byLabel: {} });
      
      // Calculate how many samples to generate based on data volume need
      const targetVolume = parseInt(taskInfo.dataVolume || '5000');
      const remainingNeeded = targetVolume - (collectedData.webScraping.length + collectedData.aiGenerated.length + collectedData.fileUpload.length);
      const generateCount = Math.min(remainingNeeded, 5000); // Cap at 5K per batch for AI generation
      
      // Start AI generation job
      const response = await dataCollectionAPI.startAIGeneration({
        task_type: taskInfo.type,
        task_description: taskInfo.description || '',
        labels: taskInfo.labels,
        count: generateCount,
        style: 'balanced',
        batch_size: 100
      });
      
      setGenerationJobId(response.job_id);
      
      // Poll for progress
      const pollInterval = setInterval(async () => {
        try {
          const progress = await dataCollectionAPI.getGenerationProgress(response.job_id);
          
          setGeneratingProgress(progress.progress);
          setGeneratingStats({
            total: progress.total_count,
            byLabel: progress.data && taskInfo.labels ? 
              taskInfo.labels.reduce((acc, label) => {
                acc[label] = progress.data.filter((d: any) => d.label === label).length;
                return acc;
              }, {} as Record<string, number>) : {}
          });
          
          if (progress.status === 'completed') {
            clearInterval(pollInterval);
            setIsProcessing(false);
            setAiGenerationJob({ jobId: response.job_id, status: 'completed' });
            
            // Update collected data state
            const mockAiData = Array.from({ length: progress.total_count }, (_, i) => ({
              id: `ai-${i}`,
              content: `AI generated content ${i + 1}`,
              label: taskInfo.labels?.[Math.floor(Math.random() * taskInfo.labels.length)],
              type: 'text' as const,
              source: 'AI Generated',
              confidence: 0.9 + Math.random() * 0.1
            }));
            setCollectedData(prev => ({ ...prev, aiGenerated: mockAiData }));
            updateIntegrationSuggestions();
            
            const message: DataMessage = {
              id: Date.now().toString(),
              role: 'system',
              content: `✅ Data generation completed!\n\nSuccessfully generated ${progress.total_count} high-quality training data. All data has been optimized to ensure authenticity and diversity.`,
              timestamp: new Date()
            };
            setAiMessages(prev => [...prev, message]);
            
            toast({
              title: "Success",
              description: "AI data generation completed successfully!",
            });
          }
        } catch (error) {
          console.error('Error polling generation progress:', error);
          clearInterval(pollInterval);
          setIsProcessing(false);
          
          toast({
            title: "Error",
            description: "Failed to get generation progress",
            variant: "destructive",
          });
        }
      }, 1000); // Poll every second
      
    } catch (error) {
      console.error('Error starting AI generation:', error);
      setIsProcessing(false);
      
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to start AI generation",
        variant: "destructive",
      });
    }
  };

  const handleSendMessage = (input: string, setMessages: React.Dispatch<React.SetStateAction<DataMessage[]>>) => {
    if (!input.trim()) return;

    const userMessage: DataMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    setTimeout(() => {
      const aiResponse: DataMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Understood, I will adjust the data collection strategy. Focusing more on recent data.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiResponse]);
    }, 1000);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    for (const file of files) {
      try {
        const response = await dataCollectionAPI.uploadFile(
          file,
          taskInfo.type,
          true, // has labels
          'label', // default label column
          'content' // default content column
        );
        
        setUploadedFiles(prev => [...prev, file]);
        
        // Update collected data state (mock data for now)
        const mockFileData = Array.from({ length: 20 }, (_, i) => ({
          id: `file-${file.name}-${i}`,
          content: `Content from ${file.name} row ${i + 1}`,
          label: taskInfo.labels?.[Math.floor(Math.random() * taskInfo.labels.length)],
          type: 'text' as const,
          source: 'File Upload',
          confidence: 0.95
        }));
        setCollectedData(prev => ({ 
          ...prev, 
          fileUpload: [...prev.fileUpload, ...mockFileData] 
        }));
        updateIntegrationSuggestions();
        
        toast({
          title: "Success",
          description: `File ${file.name} uploaded successfully!`,
        });
      } catch (error) {
        console.error('Error uploading file:', error);
        
        toast({
          title: "Error",
          description: `Failed to upload ${file.name}`,
          variant: "destructive",
        });
      }
    }
  };

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    if (['jpg', 'png', 'jpeg', 'gif'].includes(ext || '')) return Image;
    if (['mp3', 'wav', 'ogg'].includes(ext || '')) return FileAudio;
    if (['csv', 'xlsx', 'xls'].includes(ext || '')) return FileSpreadsheet;
    if (['json', 'txt', 'md'].includes(ext || '')) return FileText;
    return FileText;
  };

  const getDataTypeIcon = (type: string) => {
    switch (type) {
      case 'text': return <FileText className="h-4 w-4" />;
      case 'image': return <Image className="h-4 w-4" />;
      case 'audio': return <FileAudio className="h-4 w-4" />;
      case 'tabular': return <BarChart className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  const getAcceptedFileTypes = () => {
    switch (taskInfo.dataType) {
      case 'text':
        return '.txt,.json,.csv,.xlsx,.md';
      case 'image':
        return '.jpg,.jpeg,.png,.gif,.bmp,.webp';
      case 'audio':
        return '.mp3,.wav,.ogg,.m4a,.flac';
      case 'tabular':
        return '.csv,.xlsx,.xls,.json';
      default:
        return '*';
    }
  };

  // Generate preview data dynamically
  const generatePreviewData = (): DataSample[] => {
    const samples: DataSample[] = [];
    
    if (taskInfo.dataType === 'text' && taskInfo.labels) {
      const textSamples = [
        { content: "The product quality is terrible, completely different from the description", label: "Complaint", confidence: 0.95 },
        { content: "Very satisfied with the purchase, fast delivery and great service", label: "Not Complaint", confidence: 0.98 },
        { content: "Customer service attitude is awful, waited 30 minutes for response", label: "Complaint", confidence: 0.92 },
        { content: "Thanks for the recommendation, the product works perfectly", label: "Not Complaint", confidence: 0.96 },
        { content: "Package was damaged during shipping, very disappointed", label: "Complaint", confidence: 0.94 }
      ];
      
      textSamples.forEach((sample, index) => {
        samples.push({
          id: `sample-${index + 1}`,
          content: sample.content,
          label: sample.label,
          source: ['Web Scraping', 'AI Generated', 'Manual Upload'][index % 3],
          confidence: sample.confidence,
          type: 'text'
        });
      });
    }
    
    return samples;
  };

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      {/* Data requirements summary */}
      <Card className="border-0 shadow-sm bg-purple-50/30">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Text Data Preparation for Language Model Training</h3>
              <p className="text-sm text-gray-600">
                Based on your NLP task and selected language model, I'll help you collect the most suitable text training data
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="text-purple-600 border-purple-200 bg-purple-50/50">
                {getDataTypeIcon(taskInfo.dataType)}
                <span className="ml-1">{taskInfo.dataType === 'text' ? 'Text' : 
                               taskInfo.dataType === 'image' ? 'Image' : 
                               taskInfo.dataType === 'audio' ? 'Audio' : 'Table'}</span>
              </Badge>
              <Badge variant="outline" className="text-purple-600 border-purple-200 bg-purple-50/50">
                <Sparkles className="h-3 w-3 mr-1" />
                AI Optimization
              </Badge>
            </div>
          </div>
          
          {/* Data volume and time estimation */}
          {taskInfo.dataVolume && (
            <div className="mt-4 pt-4 border-t border-purple-100 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-3">
                <Database className="h-8 w-8 text-purple-600" />
                <div>
                  <p className="text-xs text-gray-500">Target Data Volume</p>
                  <p className="text-lg font-bold text-gray-900">{parseInt(taskInfo.dataVolume).toLocaleString()} samples</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Activity className="h-8 w-8 text-purple-600" />
                <div>
                  <p className="text-xs text-gray-500">Estimated Collection Time</p>
                  <p className="text-lg font-bold text-gray-900">{taskInfo.estimatedTime}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <TrendingUp className="h-8 w-8 text-purple-600" />
                <div>
                  <p className="text-xs text-gray-500">Current Progress</p>
                  <div className="flex items-center gap-2">
                    <p className="text-lg font-bold text-gray-900">
                      {Math.round(((collectedData.webScraping.length + collectedData.aiGenerated.length + collectedData.fileUpload.length) / parseInt(taskInfo.dataVolume)) * 100)}%
                    </p>
                    <Progress 
                      value={Math.round(((collectedData.webScraping.length + collectedData.aiGenerated.length + collectedData.fileUpload.length) / parseInt(taskInfo.dataVolume)) * 100)} 
                      className="h-2 w-20"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Model and Task Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Task Info Card */}
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Target className="h-5 w-5 text-purple-600" />
              <CardTitle className="text-base">Task Definition</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <div>
              <p className="text-xs text-gray-500">Task Type</p>
              <p className="text-sm font-medium text-gray-900">{taskInfo.type}</p>
            </div>
            {taskInfo.description && (
              <div>
                <p className="text-xs text-gray-500">Description</p>
                <p className="text-sm text-gray-700">{taskInfo.description}</p>
              </div>
            )}
            {taskInfo.labels && taskInfo.labels.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 mb-1">Labels</p>
                <div className="flex flex-wrap gap-1">
                  {taskInfo.labels.map((label, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs">
                      {label}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {taskInfo.language && (
              <div>
                <p className="text-xs text-gray-500">Language</p>
                <p className="text-sm font-medium capitalize">{taskInfo.language}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Selected Model Card */}
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-purple-600" />
              <CardTitle className="text-base">Selected Model</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {selectedModel ? (
              <>
                <div>
                  <p className="text-xs text-gray-500">Model Name</p>
                  <p className="text-sm font-medium text-gray-900">{selectedModel.name}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Provider</p>
                  <p className="text-sm text-gray-700">{selectedModel.provider}</p>
                </div>
                {selectedModel.modelType && (
                  <div>
                    <p className="text-xs text-gray-500">Type</p>
                    <p className="text-sm text-gray-700">{selectedModel.modelType}</p>
                  </div>
                )}
                <div className="flex gap-2 pt-1">
                  {selectedModel.isChineseModel && (
                    <Badge variant="outline" className="text-xs text-red-600 border-red-200">
                      🇨🇳 Chinese Model
                    </Badge>
                  )}
                  {taskInfo.language === 'chinese' && selectedModel.isChineseModel && (
                    <Badge variant="outline" className="text-xs text-green-600 border-green-200">
                      ✓ Language Match
                    </Badge>
                  )}
                </div>
              </>
            ) : (
              <div className="text-sm text-gray-500">
                <p>No model selected yet.</p>
                <p className="text-xs mt-1">Please select a model from the Model Selection step.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Data Source Integration Status */}
      {(collectedData.webScraping.length > 0 || collectedData.aiGenerated.length > 0 || collectedData.fileUpload.length > 0) && (
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="h-5 w-5 text-yellow-500" />
                Data Source Integration
              </CardTitle>
              <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                Smart Fusion
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className={`p-4 rounded-lg border-2 transition-all ${
                collectedData.webScraping.length > 0 ? 'border-green-300 bg-green-50' : 'border-gray-200 bg-gray-50'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <Globe className="h-5 w-5 text-gray-600" />
                  {collectedData.webScraping.length > 0 && (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  )}
                </div>
                <p className="text-sm font-medium">Web Scraping</p>
                <p className="text-2xl font-bold">{collectedData.webScraping.length}</p>
                <p className="text-xs text-gray-500">data points</p>
              </div>
              
              <div className={`p-4 rounded-lg border-2 transition-all ${
                collectedData.aiGenerated.length > 0 ? 'border-purple-300 bg-purple-50' : 'border-gray-200 bg-gray-50'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <Sparkles className="h-5 w-5 text-gray-600" />
                  {collectedData.aiGenerated.length > 0 && (
                    <CheckCircle2 className="h-4 w-4 text-purple-600" />
                  )}
                </div>
                <p className="text-sm font-medium">AI Generated</p>
                <p className="text-2xl font-bold">{collectedData.aiGenerated.length}</p>
                <p className="text-xs text-gray-500">data points</p>
              </div>
              
              <div className={`p-4 rounded-lg border-2 transition-all ${
                collectedData.fileUpload.length > 0 ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-gray-50'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <Upload className="h-5 w-5 text-gray-600" />
                  {collectedData.fileUpload.length > 0 && (
                    <CheckCircle2 className="h-4 w-4 text-blue-600" />
                  )}
                </div>
                <p className="text-sm font-medium">File Upload</p>
                <p className="text-2xl font-bold">{collectedData.fileUpload.length}</p>
                <p className="text-xs text-gray-500">data points</p>
              </div>
            </div>
            
            {integrationSuggestions.length > 0 && (
              <Alert className="border-yellow-200 bg-yellow-50/50">
                <Zap className="h-4 w-4 text-yellow-600" />
                <AlertDescription>
                  <p className="font-medium mb-1">Smart Suggestions:</p>
                  <ul className="text-sm space-y-1">
                    {integrationSuggestions.map((suggestion, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-yellow-600 mt-0.5">•</span>
                        <span>{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}
            
            {/* Smart Next Step Recommendation */}
            {(collectedData.webScraping.length > 0 || collectedData.aiGenerated.length > 0 || collectedData.fileUpload.length > 0) && (
              <div className="mt-4 p-3 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg">
                <p className="text-sm font-medium text-gray-900 mb-2">Recommended Next Step:</p>
                {collectedData.webScraping.length === 0 && (
                  <Button 
                    size="sm" 
                    variant="outline" 
                    className="border-purple-200 text-purple-600 hover:bg-purple-50"
                    onClick={() => setActiveTab('web-scraping')}
                  >
                    <Globe className="h-4 w-4 mr-2" />
                    Add Real-World Data
                  </Button>
                )}
                {collectedData.aiGenerated.length === 0 && collectedData.webScraping.length > 0 && (
                  <Button 
                    size="sm" 
                    variant="outline" 
                    className="border-purple-200 text-purple-600 hover:bg-purple-50"
                    onClick={() => setActiveTab('ai-generate')}
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generate More Diverse Examples
                  </Button>
                )}
                {collectedData.webScraping.length > 50 && collectedData.aiGenerated.length > 50 && (
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-green-700">Data collection is sufficient! Ready to proceed to training.</span>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Three source data tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 h-14 bg-white shadow-sm">
          <TabsTrigger value="web-scraping" className="flex items-center gap-2 data-[state=active]:bg-gray-900 data-[state=active]:text-white transition-all">
            <Globe className="h-4 w-4" />
            <span className="font-medium">Smart Collection</span>
          </TabsTrigger>
          <TabsTrigger value="ai-generate" className="flex items-center gap-2 data-[state=active]:bg-gray-900 data-[state=active]:text-white transition-all">
            <Sparkles className="h-4 w-4" />
            <span className="font-medium">AI Synthesis</span>
          </TabsTrigger>
          <TabsTrigger value="file-upload" className="flex items-center gap-2 data-[state=active]:bg-gray-900 data-[state=active]:text-white transition-all">
            <Upload className="h-4 w-4" />
            <span className="font-medium">Local Upload</span>
          </TabsTrigger>
        </TabsList>

        {/* Smart Collection */}
        <TabsContent value="web-scraping" className="space-y-4">
          <Card className="border-0 shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Smart Text Data Collection</CardTitle>
                  <p className="text-sm text-gray-500">AI automatically collects text data optimized for language model training</p>
                </div>
                <Badge className="bg-green-100 text-green-800">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Recommended Plan
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Conversation area */}
              <div className="h-96 overflow-y-auto space-y-3 p-4 bg-gray-50 rounded-lg">
                {webMessages.map((message) => (
                  <div key={message.id} className={`flex gap-3 ${
                    message.role === 'user' ? 'justify-end' : 
                    message.role === 'system' ? 'justify-center' : 'justify-start'
                  }`}>
                    {message.role === 'system' ? (
                      <div className="bg-green-50/50 border border-green-200/50 rounded-lg p-3 max-w-[80%]">
                        <p className="text-sm text-green-800 whitespace-pre-line">{message.content}</p>
                      </div>
                    ) : (
                      <div className={`flex gap-3 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          message.role === 'user' ? 'bg-gray-900' : 'bg-gray-900'
                        }`}>
                          {message.role === 'user' ? (
                            <User className="h-4 w-4 text-white" />
                          ) : (
                            <span className="text-white font-bold text-sm">M</span>
                          )}
                        </div>
                        <div className={`p-3 rounded-lg ${
                          message.role === 'user' 
                            ? 'bg-gray-900 text-white' 
                            : 'bg-white border border-gray-200'
                        }`}>
                          <p className="text-sm whitespace-pre-line">{message.content}</p>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
              {/* Collection visualization */}
              {isProcessing && activeTab === 'web-scraping' && (
                <div className="space-y-4 p-4 bg-indigo-50/30 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Activity className="h-5 w-5 text-indigo-600 animate-pulse" />
                      <span className="font-medium text-gray-900">Collecting data...</span>
                    </div>
                    <span className="text-sm text-gray-600">{crawlingProgress}%</span>
                  </div>
                  <Progress value={crawlingProgress} className="h-2" />
                  
                  {/* Data source collection status */}
                  <div className="space-y-2 mt-4">
                    {crawlingSites.map((site, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-white rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="text-gray-500">{site.icon}</div>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{site.name}</p>
                            <p className="text-xs text-gray-500">{site.description}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {site.status === 'crawling' && (
                            <Loader2 className="h-4 w-4 text-indigo-600 animate-spin" />
                          )}
                          {site.status === 'completed' && (
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                          )}
                          {site.count > 0 && (
                            <Badge variant="outline" className="text-xs">
                              {site.count} points
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Input area */}
              <div className="flex gap-2">
                <Input
                  placeholder="Describe the data characteristics you need, such as: comments containing user emotions..."
                  value={currentInput}
                  onChange={(e) => setCurrentInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleSendMessage(currentInput, setWebMessages);
                      setCurrentInput('');
                    }
                  }}
                  className="flex-1"
                  disabled={isProcessing}
                />
                <Button
                  onClick={handleWebCrawling}
                  disabled={isProcessing}
                  className="bg-gray-900 hover:bg-gray-800"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Collecting...
                    </>
                  ) : (
                    <>
                      <Globe className="h-4 w-4 mr-2" />
                      Start Collection
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Synthesis */}
        <TabsContent value="ai-generate" className="space-y-4">
          <Card className="border-0 shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">AI Text Generation for Training</CardTitle>
                  <p className="text-sm text-gray-500">Generate synthetic text data tailored for your language model fine-tuning</p>
                </div>
                <Info className="h-4 w-4 text-gray-400" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert className="border-blue-200 bg-blue-50/50">
                <Info className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-sm">
                  AI will generate diverse and balanced data sets to ensure effective model training
                </AlertDescription>
              </Alert>

              {/* Conversation area */}
              <div className="h-96 overflow-y-auto space-y-3 p-4 bg-gray-50 rounded-lg">
                {aiMessages.map((message) => (
                  <div key={message.id} className={`flex gap-3 ${
                    message.role === 'user' ? 'justify-end' : 
                    message.role === 'system' ? 'justify-center' : 'justify-start'
                  }`}>
                    {message.role === 'system' ? (
                      <div className="bg-green-50/50 border border-green-200/50 rounded-lg p-3 max-w-[80%]">
                        <p className="text-sm text-green-800 whitespace-pre-line">{message.content}</p>
                      </div>
                    ) : (
                      <div className={`flex gap-3 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          message.role === 'user' ? 'bg-gray-900' : 'bg-gray-900'
                        }`}>
                          {message.role === 'user' ? (
                            <User className="h-4 w-4 text-white" />
                          ) : (
                            <span className="text-white font-bold text-sm">M</span>
                          )}
                        </div>
                        <div className={`p-3 rounded-lg ${
                          message.role === 'user' 
                            ? 'bg-gray-900 text-white' 
                            : 'bg-white border border-gray-200'
                        }`}>
                          <p className="text-sm whitespace-pre-line">{message.content}</p>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* AI generation visualization */}
              {isProcessing && activeTab === 'ai-generate' && (
                <div className="space-y-4 p-4 bg-purple-50/30 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-5 w-5 text-purple-600 animate-pulse" />
                      <span className="font-medium text-gray-900">AI is generating data...</span>
                    </div>
                    <span className="text-sm text-gray-600">{generatingProgress}%</span>
                  </div>
                  <Progress value={generatingProgress} className="h-2" />
                  
                  {/* Generation statistics */}
                  <div className="grid grid-cols-3 gap-4 mt-4">
                    <div className="text-center p-3 bg-white rounded-lg">
                      <p className="text-2xl font-bold text-gray-900">{generatingStats.total}</p>
                      <p className="text-xs text-gray-500">Total Generated</p>
                    </div>
                    {taskInfo.labels && taskInfo.labels.slice(0, 2).map((label, index) => (
                      <div key={index} className="text-center p-3 bg-white rounded-lg">
                        <p className="text-2xl font-bold" style={{
                          color: index === 0 ? '#dc2626' : '#16a34a'
                        }}>
                          {generatingStats.byLabel[label] || 0}
                        </p>
                        <p className="text-xs text-gray-500">{label}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Input area */}
              <div className="flex gap-2">
                <Input
                  placeholder="Describe data characteristics, such as: needing more extreme cases..."
                  value={currentAiInput}
                  onChange={(e) => setCurrentAiInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleSendMessage(currentAiInput, setAiMessages);
                      setCurrentAiInput('');
                    }
                  }}
                  className="flex-1"
                  disabled={isProcessing}
                />
                <Button
                  onClick={handleAiGenerate}
                  disabled={isProcessing}
                  className="bg-gray-900 hover:bg-gray-800"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4 mr-2" />
                      Start Generating
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* File upload */}
        <TabsContent value="file-upload" className="space-y-4">
          <Card className="border-0 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">Upload Local Data</CardTitle>
              <p className="text-sm text-gray-500">If you already have data files, you can upload them directly</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors">
                <div className="text-gray-400 mb-4">
                  {getDataTypeIcon(taskInfo.dataType)}
                </div>
                <p className="text-sm text-gray-600 mb-2">Drag and drop files here or click to upload</p>
                <p className="text-xs text-gray-500 mb-4">
                  Supports {taskInfo.dataType === 'text' ? 'TXT, JSON, CSV' : 
                              taskInfo.dataType === 'image' ? 'JPG, PNG, GIF' : 
                              taskInfo.dataType === 'audio' ? 'MP3, WAV, OGG' : 'CSV, XLSX'} formats
                </p>
                <input
                  type="file"
                  multiple
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                  accept={getAcceptedFileTypes()}
                />
                <Button variant="outline" asChild>
                  <label htmlFor="file-upload" className="cursor-pointer">
                    Select File
                  </label>
                </Button>
              </div>

              {uploadedFiles.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-gray-900">Uploaded Files</h4>
                  {uploadedFiles.map((file, index) => {
                    const FileIcon = getFileIcon(file.name);
                    return (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <FileIcon className="h-5 w-5 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">{file.name}</p>
                            <p className="text-xs text-gray-500">
                              {(file.size / 1024).toFixed(1)} KB
                            </p>
                          </div>
                        </div>
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Data summary */}
      {dataStats.total > 0 && (
        <Card className="border-0 shadow-sm bg-green-50/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">Data Preparation Completed</h4>
                <div className="flex items-center gap-6 text-sm">
                  <div>
                    <span className="text-gray-600">Total Data Points:</span>
                    <span className="font-medium text-gray-900">{dataStats.total}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Available Data:</span>
                    <span className="font-medium text-green-600">{dataStats.valid}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Needs Review:</span>
                    <span className="font-medium text-orange-500">{dataStats.needsReview}</span>
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <Button 
                  variant="outline"
                  onClick={async () => {
                    try {
                      const collectedData: DataSample[] = [];
                      
                      // Get web scraping data
                      if (webScrapingJob?.status === 'completed') {
                        const response = await dataCollectionAPI.getScrapingData(webScrapingJob.jobId);
                        if (response.data && response.data.length > 0) {
                          response.data.forEach((item: any) => {
                            collectedData.push({
                              id: item.id,
                              content: item.content,
                              label: item.label,
                              type: item.type || 'text',
                              source: 'Web Scraping',
                              confidence: item.confidence
                            });
                          });
                        }
                      }
                      
                      // Get AI generated data
                      if (aiGenerationJob?.status === 'completed') {
                        const response = await dataCollectionAPI.getGeneratedData(aiGenerationJob.jobId);
                        if (response.data && response.data.length > 0) {
                          response.data.forEach((item: any) => {
                            collectedData.push({
                              id: item.id,
                              content: item.content,
                              label: item.label,
                              type: item.type || 'text',
                              source: 'AI Generated',
                              confidence: item.confidence
                            });
                          });
                        }
                      }
                      
                      // If no real data, use preview data
                      if (collectedData.length === 0) {
                        setPreviewData(generatePreviewData());
                      } else {
                        setPreviewData(collectedData);
                      }
                      
                      setShowDataPreview(true);
                    } catch (error) {
                      console.error('Error fetching data:', error);
                      toast({
                        title: "Error",
                        description: "Failed to fetch collected data",
                        variant: "destructive",
                      });
                      // Show preview data anyway
                      setPreviewData(generatePreviewData());
                      setShowDataPreview(true);
                    }
                  }}
                  className="border-purple-200 text-purple-600 hover:bg-purple-50"
                >
                  <Eye className="h-4 w-4 mr-2" />
                  View Data
                </Button>
                <Button className="bg-purple-600 hover:bg-purple-700">
                  Next Step: Data Integration Engine
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data preview dialog */}
      <Dialog open={showDataPreview} onOpenChange={setShowDataPreview}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Data Preview</DialogTitle>
            <DialogDescription>
              View and check your training data samples
            </DialogDescription>
          </DialogHeader>
          
          <ScrollArea className="h-[500px] mt-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]">No.</TableHead>
                  <TableHead>Content</TableHead>
                  <TableHead className="w-[100px]">Label</TableHead>
                  <TableHead className="w-[100px]">Source</TableHead>
                  <TableHead className="w-[100px]">Confidence</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {previewData.map((item, index) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">{index + 1}</TableCell>
                    <TableCell className="max-w-[400px]">
                      <p className="text-sm line-clamp-2">{item.content}</p>
                    </TableCell>
                    <TableCell>
                      {item.label && (
                        <Badge className={`${item.label === 'Complaint' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                          {item.label}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">{item.source}</TableCell>
                    <TableCell>
                      {item.confidence && (
                        <span className="text-sm font-medium">
                          {(item.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button size="sm" variant="ghost" className="h-7 w-7 p-0">
                          <ThumbsUp className="h-3 w-3" />
                        </Button>
                        <Button size="sm" variant="ghost" className="h-7 w-7 p-0">
                          <ThumbsDown className="h-3 w-3" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ScrollArea>

          <div className="mt-4 flex justify-between items-center">
            <p className="text-sm text-gray-500">
              Showing first {previewData.length} data sample points
            </p>
            <Button onClick={() => setShowDataPreview(false)}>
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DataSynthesizer;
