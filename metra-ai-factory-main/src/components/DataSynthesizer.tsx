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
  Rss
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
}

const DataSynthesizer = () => {
  const [activeTab, setActiveTab] = useState('web-scraping');
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  
  // Get task info from Dashboard
  const [taskInfo] = useState<TaskInfo>({
    type: 'Customer Complaint Classifier',
    dataType: 'text',
    labels: ['Complaint', 'Not Complaint']
  });

  // Data sources based on task type
  const webSources = [
    { name: 'E-commerce Reviews', description: 'Taobao, JD.com, Amazon product reviews', icon: <ShoppingCart className="h-4 w-4" /> },
    { name: 'Social Media', description: 'Weibo, Twitter, Reddit posts and comments', icon: <MessageCircle className="h-4 w-4" /> },
    { name: 'Customer Service', description: 'Support tickets and chat logs', icon: <Headphones className="h-4 w-4" /> },
    { name: 'Forums', description: 'Tech support forums, Q&A sites', icon: <Users className="h-4 w-4" /> },
    { name: 'App Store', description: 'Mobile app reviews and ratings', icon: <Smartphone className="h-4 w-4" /> },
    { name: 'News Comments', description: 'News article comment sections', icon: <Globe className="h-4 w-4" /> }
  ];

  // Generate recommended sources based on task type
  const getRecommendedSources = () => {
    const taskType = taskInfo.type.toLowerCase();
    
    // Text classification tasks
    if (taskInfo.dataType === 'text') {
      if (taskType.includes('complaint') || taskType.includes('feedback') || taskType.includes('review')) {
        return webSources.slice(0, 4);
      } else if (taskType.includes('emotion') || taskType.includes('sentiment')) {
        return [
          { name: 'Social Media', description: 'Rich emotional expression content', icon: <MessageCircle className="h-4 w-4" /> },
          { name: 'Movie Reviews', description: 'User ratings and comments', icon: <Film className="h-4 w-4" /> },
          { name: 'News Comments', description: 'Public opinion and attitudes', icon: <Newspaper className="h-4 w-4" /> },
          { name: 'Blog Posts', description: 'Personal emotional expressions', icon: <FileText className="h-4 w-4" /> }
        ];
      } else if (taskType.includes('news') || taskType.includes('category')) {
        return [
          { name: 'News Sites', description: 'Various news categories', icon: <Newspaper className="h-4 w-4" /> },
          { name: 'Professional Media', description: 'High-quality categorized content', icon: <Globe className="h-4 w-4" /> },
          { name: 'RSS Feeds', description: 'Structured news data', icon: <Rss className="h-4 w-4" /> },
          { name: 'Academic Papers', description: 'Research literature in relevant fields', icon: <FileText className="h-4 w-4" /> }
        ];
      }
    }
    
    // Image recognition tasks
    else if (taskInfo.dataType === 'image') {
      if (taskType.includes('product') || taskType.includes('object')) {
        return [
          { name: 'E-commerce Platforms', description: 'Product images and categories', icon: <ShoppingCart className="h-4 w-4" /> },
          { name: 'Image Libraries', description: 'High-quality labeled images', icon: <Image className="h-4 w-4" /> },
          { name: 'Social Media', description: 'User-generated images', icon: <Image className="h-4 w-4" /> },
          { name: 'Open Datasets', description: 'Public image datasets', icon: <Database className="h-4 w-4" /> }
        ];
      } else if (taskType.includes('face') || taskType.includes('emotion')) {
        return [
          { name: 'Portrait Libraries', description: 'Face images with emotion labels', icon: <Camera className="h-4 w-4" /> },
          { name: 'Video Platforms', description: 'Facial expression screenshots', icon: <Image className="h-4 w-4" /> },
          { name: 'Photo Communities', description: 'Portrait photography works', icon: <Image className="h-4 w-4" /> },
          { name: 'Research Datasets', description: 'Academic facial datasets', icon: <Database className="h-4 w-4" /> }
        ];
      }
    }
    
    // Default return general data sources
    return [
      { name: 'Web Scraping', description: 'General web data', icon: <Globe className="h-4 w-4" /> },
      { name: 'Public APIs', description: 'Structured data interfaces', icon: <Database className="h-4 w-4" /> },
      { name: 'Open Datasets', description: 'Public datasets', icon: <FileSpreadsheet className="h-4 w-4" /> },
      { name: 'Social Media', description: 'User-generated content', icon: <MessageCircle className="h-4 w-4" /> }
    ];
  };

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

  // Generate conversation messages based on task type
  const getInitialWebMessage = () => {
    if (taskInfo.dataType === 'text') {
      return `Based on your "${taskInfo.type}" task, I recommend these data sources:\n\n${
        getRecommendedSources().map((s, i) => `${i + 1}. ${s.name} - ${s.description}`).join('\n')
      }\n\nThese sources will help you get high-quality ${taskInfo.labels?.join(', ')} labeled data.`;
    } else if (taskInfo.dataType === 'image') {
      return `Your image recognition task needs labeled images. I suggest getting them from:\n\n${
        getRecommendedSources().map((s, i) => `${i + 1}. ${s.name} - ${s.description}`).join('\n')
      }\n\nThe system will automatically label these images for you.`;
    }
    return 'I will recommend the most suitable data sources based on your task requirements.';
  };

  const getInitialAiMessage = () => {
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
    },
    {
      id: '2',
      role: 'user',
      content: 'I want to adjust the data collection strategy, can we focus more on recent data?',
      timestamp: new Date(Date.now() - 2000)
    },
    {
      id: '3',
      role: 'assistant',
      content: 'Absolutely! I\'ll prioritize recent data (last 3 months) to capture current trends. This will make your model more relevant to current customer behaviors.',
      timestamp: new Date(Date.now() - 1000)
    }
  ]);

  const [aiMessages, setAiMessages] = useState<DataMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: getInitialAiMessage(),
      timestamp: new Date()
    },
    {
      id: '2',
      role: 'user',
      content: 'Please ensure the generated data covers various complaint scenarios',
      timestamp: new Date(Date.now() - 2000)
    },
    {
      id: '3',
      role: 'assistant',
      content: 'Will do! I\'ll include diverse scenarios: product quality issues, shipping problems, customer service complaints, pricing disputes, etc. Each with appropriate context and realistic language patterns.',
      timestamp: new Date(Date.now() - 1000)
    }
  ]);

  const [currentInput, setCurrentInput] = useState('');
  const [currentAiInput, setCurrentAiInput] = useState('');

  // Simulate crawling effect
  const simulateCrawling = () => {
    let progress = 0;
    const sites = [...crawlingSites];
    let currentSiteIndex = 0;

    const crawlInterval = setInterval(() => {
      if (currentSiteIndex < sites.length) {
        sites[currentSiteIndex].status = 'crawling';
        setCrawlingSites([...sites]);

        const dataIncrement = Math.floor(Math.random() * 200) + 100;
        sites[currentSiteIndex].count += dataIncrement;

        progress += 5;
        setCrawlingProgress(progress);

        if (progress % 25 === 0) {
          sites[currentSiteIndex].status = 'completed';
          currentSiteIndex++;
        }

        setCrawlingSites([...sites]);
      }

      if (progress >= 100) {
        clearInterval(crawlInterval);
        setIsProcessing(false);
        
        const totalCount = sites.reduce((sum, site) => sum + site.count, 0);
        setDataStats({
          total: totalCount,
          valid: Math.floor(totalCount * 0.95),
          needsReview: Math.floor(totalCount * 0.05)
        });
        
        const message: DataMessage = {
          id: Date.now().toString(),
          role: 'system',
          content: `✅ Data collection completed!\n\nTotal ${totalCount} data points collected, data quality is good, can be directly used for training.`,
          timestamp: new Date()
        };
        setWebMessages(prev => [...prev, message]);
      }
    }, 300);
  };

  // Simulate AI generation effect
  const simulateGenerating = () => {
    let progress = 0;
    const stats = { 
      total: 0, 
      byLabel: taskInfo.labels ? 
        Object.fromEntries(taskInfo.labels.map(label => [label, 0])) : 
        {} 
    };

    const genInterval = setInterval(() => {
      progress += 2;
      setGeneratingProgress(progress);

      // Generate data based on labels
      if (taskInfo.labels) {
        taskInfo.labels.forEach(label => {
          const increment = Math.floor(Math.random() * 10) + 5;
          stats.byLabel[label] = (stats.byLabel[label] || 0) + increment;
          stats.total += increment;
        });
      } else {
        stats.total += Math.floor(Math.random() * 20) + 10;
      }
      
      setGeneratingStats({...stats});

      if (progress >= 100) {
        clearInterval(genInterval);
        setIsProcessing(false);
        
        const message: DataMessage = {
          id: Date.now().toString(),
          role: 'system',
          content: `✅ Data generation completed!\n\nSuccessfully generated ${stats.total} high-quality training data. All data has been optimized to ensure authenticity and diversity.`,
          timestamp: new Date()
        };
        setAiMessages(prev => [...prev, message]);
      }
    }, 100);
  };

  const handleWebCrawling = () => {
    setIsProcessing(true);
    setCrawlingProgress(0);
    setCrawlingSites(prev => prev.map(site => ({ ...site, status: 'waiting', count: 0 })));
    simulateCrawling();
  };

  const handleAiGenerate = () => {
    setIsProcessing(true);
    setGeneratingProgress(0);
    setGeneratingStats({ total: 0, byLabel: {} });
    simulateGenerating();
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

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setUploadedFiles(prev => [...prev, ...files]);
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
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Smart Data Preparation</h3>
              <p className="text-sm text-gray-600">
                Based on your task type, the system has customized data acquisition solutions for you
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
        </CardContent>
      </Card>

      {/* Three source data tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 h-12">
          <TabsTrigger value="web-scraping" className="flex items-center gap-2">
            <Globe className="h-4 w-4" />
            Smart Collection
          </TabsTrigger>
          <TabsTrigger value="ai-generate" className="flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            AI Synthesis
          </TabsTrigger>
          <TabsTrigger value="file-upload" className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Local Upload
          </TabsTrigger>
        </TabsList>

        {/* Smart Collection */}
        <TabsContent value="web-scraping" className="space-y-4">
          <Card className="border-0 shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Smart Data Collection</CardTitle>
                  <p className="text-sm text-gray-500">AI automatically identifies and collects the most suitable data</p>
                </div>
                <Badge className="bg-green-100 text-green-800">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Recommended Plan
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Conversation area */}
              <div className="h-48 overflow-y-auto space-y-3 p-4 bg-gray-50 rounded-lg">
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
                  <CardTitle className="text-lg">AI Data Synthesis</CardTitle>
                  <p className="text-sm text-gray-500">Smartly generate training data that meets your needs</p>
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
              <div className="h-48 overflow-y-auto space-y-3 p-4 bg-gray-50 rounded-lg">
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
                  onClick={() => setShowDataPreview(true)}
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
