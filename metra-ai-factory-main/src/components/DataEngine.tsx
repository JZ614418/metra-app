import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Zap, 
  Activity, 
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Info,
  Sparkles,
  Database,
  FileText,
  Bot,
  Eye,
  Download,
  Search,
  Link2,
  Shuffle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface IntegratedData {
  id: string;
  text: string;
  label: string;
  source: string;
  originalField?: string;
  mappedField?: string;
  confidence?: number;
  isGenerated?: boolean;
  timestamp?: string;
}

interface ProcessingStep {
  id: string;
  title: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  message?: string;
}

const DataEngine = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [showDataPreview, setShowDataPreview] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterSource, setFilterSource] = useState('all');
  const [filterLabel, setFilterLabel] = useState('all');
  const [showFieldMapping, setShowFieldMapping] = useState(false);
  const [allStepsCompleted, setAllStepsCompleted] = useState(false);

  // Processing step states
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([
    { id: 'analyze', title: 'Analyze Data Structure', status: 'pending' },
    { id: 'align', title: 'Smart Field Alignment', status: 'pending' },
    { id: 'clean', title: 'Data Cleaning Optimization', status: 'pending' },
    { id: 'validate', title: 'Data Quality Validation', status: 'pending' }
  ]);

  // Simulated integrated data
  const [integratedData] = useState<IntegratedData[]>([
    { id: '1', text: 'The product broke after just two days, very disappointed!', label: 'Complaint', source: 'E-commerce Review', confidence: 0.95, timestamp: '2024-03-15 10:23:45' },
    { id: '2', text: 'Great product, exactly what I was looking for', label: 'Not Complaint', source: 'AI Generated', confidence: 0.98, timestamp: '2024-03-15 10:24:12' },
    { id: '3', text: 'The shipping took too long', label: 'Complaint', source: 'Customer Service', confidence: 0.85, timestamp: '2024-03-15 10:24:36' },
    { id: '4', text: 'Customer service was very patient and solved my problem, kudos!', label: 'Not Complaint', source: 'Social Media', confidence: 0.89, timestamp: '2024-03-15 10:25:03' },
    { id: 'g1', text: 'The ordered product is already damaged, packaging is poor, requesting return and refund', label: 'Complaint', source: 'AI Generated', isGenerated: true, confidence: 1.0, timestamp: '2024-03-15 10:30:15' },
    { id: 'g2', text: 'Product is fully functional, easy to use, meets expectations', label: 'Not Complaint', source: 'AI Generated', isGenerated: true, confidence: 1.0, timestamp: '2024-03-15 10:30:45' },
    { id: 'u1', text: 'Spent a lot of money on the product, it broke in less than a week, terrible!', label: 'Complaint', source: 'User Upload', originalField: 'feedback', mappedField: 'text', timestamp: '2024-03-15 10:35:22' },
    { id: 'u2', text: 'Great value for money, highly recommend', label: 'Not Complaint', source: 'User Upload', originalField: 'comment', mappedField: 'text', timestamp: '2024-03-15 10:35:58' }
  ]);

  // Data statistics
  const dataStats = {
    total: integratedData.length,
    webScraping: integratedData.filter(d => d.source.includes('Review') || d.source.includes('Social')).length,
    aiGenerated: integratedData.filter(d => d.isGenerated).length,
    userUpload: integratedData.filter(d => d.source.includes('Upload')).length,
    valid: integratedData.filter(d => d.confidence && d.confidence > 0.8).length,
    needsReview: integratedData.filter(d => d.confidence && d.confidence <= 0.8).length
  };

  // Field mappings
  const fieldMappings = [
    { from: 'Comment Content', to: 'text', confidence: 95 },
    { from: 'User Feedback', to: 'text', confidence: 92 },
    { from: 'Sentiment', to: 'label', confidence: 88 },
    { from: 'Emotion', to: 'label', confidence: 90 },
    { from: 'Feeling', to: 'label', confidence: 87 }
  ];

  // Filter data
  const filteredData = integratedData.filter(item => {
    const matchesSearch = searchQuery === '' || 
      item.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.label.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesSource = filterSource === 'all' || item.source === filterSource;
    const matchesLabel = filterLabel === 'all' || item.label === filterLabel;
    
    return matchesSearch && matchesSource && matchesLabel;
  });

  const handleStartProcessing = () => {
    setIsProcessing(true);
    
    // Simulated processing process
    const steps = [...processingSteps];
    let currentStep = 0;

    const processNextStep = () => {
      if (currentStep < steps.length) {
        steps[currentStep].status = 'processing';
        setProcessingSteps([...steps]);

        setTimeout(() => {
          steps[currentStep].status = 'completed';
          steps[currentStep].message = getStepMessage(steps[currentStep].id);
          currentStep++;
          setProcessingSteps([...steps]);
          processNextStep();
        }, 1500);
      } else {
        setIsProcessing(false);
        setAllStepsCompleted(true);
      }
    };

    processNextStep();
  };

  const getStepMessage = (stepId: string) => {
    const messages: { [key: string]: string } = {
      analyze: 'Identified 3 data sources, 12 fields',
      align: 'Automatically aligned 10 fields, 2 need confirmation',
      clean: 'Removed 123 duplicates, filled 155 missing values',
      validate: 'Data quality score: 96/100'
    };
    return messages[stepId];
  };

  const getSourceIcon = (source: string) => {
    if (source.includes('AI')) return <Bot className="h-3 w-3" />;
    if (source.includes('Upload')) return <FileText className="h-3 w-3" />;
    return <Database className="h-3 w-3" />;
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'processing':
        return <Activity className="h-5 w-5 text-indigo-500 animate-spin" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <div className="h-5 w-5 rounded-full border-2 border-gray-300" />;
    }
  };

  const getUniqueValues = (field: keyof IntegratedData) => {
    return Array.from(new Set(integratedData.map(item => item[field])));
  };

  const alignmentExamples = [
    {
      source: ['sentiment', 'emotion', 'feeling'],
      target: 'sentiment',
      description: 'AI recognizes these as synonyms'
    },
    {
      source: ['customer_feedback', 'user_comment', 'review'],
      target: 'content',
      description: 'Maps different field names to unified content'
    },
    {
      source: ['0/1', 'yes/no', 'true/false'],
      target: 'boolean',
      description: 'Automatically converts to standard format'
    }
  ];

  const qualityMetrics = [
    { name: 'Completeness', value: 92, color: 'bg-green-600', description: 'Data field coverage' },
    { name: 'Consistency', value: 88, color: 'bg-blue-600', description: 'Format uniformity' },
    { name: 'Accuracy', value: 95, color: 'bg-purple-600', description: 'Label accuracy' },
    { name: 'Balance', value: 76, color: 'bg-orange-600', description: 'Category distribution balance' }
  ];

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      {/* DFE Title Card */}
      <Card className="border-0 shadow-sm bg-indigo-50/30">
        <CardContent className="p-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-4 bg-indigo-600 rounded-xl">
                <Zap className="h-8 w-8 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900 mb-1">Metra Data Fusion Engine (DFE)</h3>
                <p className="text-gray-600">Automatic data alignment and quality optimization</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500 mb-1">Ready</p>
              <p className="text-2xl font-bold text-gray-900">{dataStats.total.toLocaleString()}</p>
              <p className="text-sm text-gray-500">Training Data Points</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Source Statistics */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <Database className="h-8 w-8 text-gray-500" />
              <Badge className="bg-gray-100 text-gray-800 gap-1">Web Scraping</Badge>
            </div>
            <p className="text-3xl font-bold text-gray-900">{dataStats.webScraping.toLocaleString()}</p>
            <p className="text-sm text-gray-500 mt-1">From E-commerce Platforms and Social Media</p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <Sparkles className="h-8 w-8 text-purple-500/50" />
              <Badge className="bg-gray-100 text-gray-800 gap-1">AI Generated</Badge>
            </div>
            <p className="text-3xl font-bold text-gray-900">{dataStats.aiGenerated.toLocaleString()}</p>
            <p className="text-sm text-gray-500 mt-1">High-Quality Synthetic Data</p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <FileText className="h-8 w-8 text-green-500/50" />
              <Badge className="bg-gray-100 text-gray-800 gap-1">User Upload</Badge>
            </div>
            <p className="text-3xl font-bold text-gray-900">{dataStats.userUpload.toLocaleString()}</p>
            <p className="text-sm text-gray-500 mt-1">User-Owned Data</p>
          </CardContent>
        </Card>
      </div>

      {/* Processing Panel */}
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Smart Data Processing</CardTitle>
              <p className="text-sm text-gray-500 mt-1">DFE will automatically complete all data integration work</p>
            </div>
            {!isProcessing && !allStepsCompleted && (
              <Button 
                onClick={handleStartProcessing}
                className="bg-indigo-600 hover:bg-indigo-700"
              >
                <Zap className="h-4 w-4 mr-2" />
                Start Processing
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Processing Steps */}
          <div className="space-y-3">
            {processingSteps.map((step, index) => (
              <div key={step.id} className="flex items-center gap-4">
                {getStepIcon(step.status)}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className={`font-medium ${
                      step.status === 'completed' ? 'text-gray-900' : 
                      step.status === 'processing' ? 'text-indigo-600' : 'text-gray-400'
                    }`}>
                      {step.title}
                    </span>
                    {step.message && (
                      <span className="text-sm text-gray-500">{step.message}</span>
                    )}
                  </div>
                  {step.status === 'processing' && (
                    <Progress value={60} className="h-1 mt-2" />
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Result after processing */}
          {allStepsCompleted && (
            <div className="mt-6 space-y-4">
              <Alert className="border-green-200 bg-green-50/30">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  Data processing completed! Integrated {dataStats.total} data points, of which {dataStats.valid} can be directly used for training
                </AlertDescription>
              </Alert>

              {/* Quick Preview */}
              <div className="grid grid-cols-2 gap-4">
                <Card className="border border-indigo-200/50 bg-indigo-50/30">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Link2 className="h-4 w-4 text-indigo-600" />
                        <span className="font-medium">Field Alignment</span>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => setShowFieldMapping(true)}
                        className="text-indigo-600 hover:bg-indigo-100/50"
                      >
                        View Details
                      </Button>
                    </div>
                    <p className="text-sm text-gray-600">
                      AI automatically identifies synonyms and similar fields
                    </p>
                  </CardContent>
                </Card>

                <Card className="border border-purple-200/50 bg-purple-50/30">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Shuffle className="h-4 w-4 text-purple-600" />
                        <span className="font-medium">Data Distribution</span>
                      </div>
                      <Badge className="bg-gray-100 text-gray-800 gap-1">
                        Balanced
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600">
                      Complaint: 48% | Not Complaint: 52%
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 justify-end pt-4">
                <Button 
                  variant="outline"
                  onClick={() => setShowDataPreview(true)}
                  className="border-indigo-200/50 text-indigo-600 hover:bg-indigo-50/30"
                >
                  <Eye className="h-4 w-4 mr-2" />
                  View All Data
                </Button>
                <Button className="bg-indigo-600 hover:bg-indigo-700">
                  Next: Model Training
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Field Mapping Dialog */}
      <Dialog open={showFieldMapping} onOpenChange={setShowFieldMapping}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Smart Field Alignment Details</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 mt-4">
            <p className="text-sm text-gray-600 mb-4">
              DFE uses semantic understanding technology to automatically identify different field names with the same meaning
            </p>
            {fieldMappings.map((mapping, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-600">{mapping.from}</span>
                  <ArrowRight className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-900">{mapping.to}</span>
                </div>
                <Badge className="bg-gray-100 text-gray-800 gap-1">
                  {mapping.confidence}% Match
                </Badge>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Data Preview Dialog */}
      <Dialog open={showDataPreview} onOpenChange={setShowDataPreview}>
        <DialogContent className="max-w-6xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Integrated Data Overview</DialogTitle>
          </DialogHeader>
          
          {/* Search and Filter */}
          <div className="flex gap-4 mt-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search content..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterSource} onValueChange={setFilterSource}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Data Source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                {getUniqueValues('source').map(source => (
                  <SelectItem key={source} value={source as string}>
                    {source}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterLabel} onValueChange={setFilterLabel}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Label" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Labels</SelectItem>
                {getUniqueValues('label').map(label => (
                  <SelectItem key={label} value={label as string}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <ScrollArea className="h-[450px] mt-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]">No.</TableHead>
                  <TableHead>Content</TableHead>
                  <TableHead className="w-[100px]">Label</TableHead>
                  <TableHead className="w-[120px]">Source</TableHead>
                  <TableHead className="w-[150px]">Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredData.map((item, index) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">{index + 1}</TableCell>
                    <TableCell className="max-w-[400px]">
                      <p className="text-sm line-clamp-2">{item.text}</p>
                    </TableCell>
                    <TableCell>
                      <Badge className={item.label === 'Complaint' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}>
                        {item.label}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {getSourceIcon(item.source)}
                        <span className="text-sm">{item.source}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {item.timestamp || '-'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ScrollArea>

          <div className="mt-4 flex justify-between items-center">
            <p className="text-sm text-gray-500">
              Showing {filteredData.length} / {integratedData.length} data points
            </p>
            <div className="flex gap-2">
              <Button variant="outline" className="text-indigo-600 border-indigo-200">
                <Download className="h-4 w-4 mr-2" />
                Export Data
              </Button>
              <Button onClick={() => setShowDataPreview(false)}>
                Close
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DataEngine; 