import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { 
  X,
  Search,
  Filter,
  Download,
  MessageCircle,
  Send,
  Trash2,
  Edit,
  CheckCircle,
  AlertCircle,
  BarChart,
  Bot
} from 'lucide-react';
import { dataBuilderAPI } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface DataSample {
  id: string;
  content: string;
  title?: string;
  url?: string;
  label?: string;
  source: string;
  confidence?: number;
  timestamp?: string;
}

interface DataStats {
  label_distribution: Record<string, number>;
  source_distribution: Record<string, number>;
  average_confidence: number;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

const DataViewer = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  // Data state
  const [data, setData] = useState<DataSample[]>([]);
  const [filteredData, setFilteredData] = useState<DataSample[]>([]);
  const [stats, setStats] = useState<DataStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(100);
  
  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [labelFilter, setLabelFilter] = useState<string>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hello! I'm Data AI, your assistant for data analysis and optimization. I can help you:
• Analyze data quality and distribution
• Filter and clean your dataset
• Balance label distribution
• Generate more samples for specific categories
• Answer questions about your data

What would you like to do?`,
      timestamp: new Date()
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // Edit dialog
  const [editingSample, setEditingSample] = useState<DataSample | null>(null);
  const [editContent, setEditContent] = useState('');
  const [editLabel, setEditLabel] = useState('');
  
  // Load data on mount
  useEffect(() => {
    if (jobId) {
      loadData();
    }
  }, [jobId, currentPage, labelFilter, sourceFilter]);
  
  // Apply search filter
  useEffect(() => {
    if (searchQuery) {
      const filtered = data.filter(sample => 
        sample.content.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredData(filtered);
    } else {
      setFilteredData(data);
    }
  }, [searchQuery, data]);
  
  const handleClose = () => {
    // Navigate back to DataBuilder instead of using browser history
    navigate('/dashboard?section=data-builder');
  };
  
  const loadData = async () => {
    if (!jobId) return;
    
    setLoading(true);
    try {
      const response = await dataBuilderAPI.getCollectedData(
        jobId,
        currentPage * pageSize,
        pageSize,
        labelFilter !== 'all' ? labelFilter : undefined,
        sourceFilter !== 'all' ? sourceFilter : undefined
      );
      
      // Transform backend data format to frontend format
      const transformedData = response.data.map((item: any, index: number) => ({
        id: item.id || `${jobId}-${index}`,
        content: item.text || item.content || '',
        title: item.title || '',
        url: item.url || '',
        label: item.label || 'unknown',
        source: item.source || 'unknown',
        confidence: item.confidence || 0,
        timestamp: item.created_at || item.timestamp
      }));
      
      setData(transformedData);
      setFilteredData(transformedData);
      setStats(response.statistics);
      setTotalCount(response.total);
    } catch (error) {
      console.error('Failed to load data:', error);
      toast({
        title: "Failed to load data",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleChat = async () => {
    if (!chatInput.trim()) return;
    
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: chatInput,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setIsAnalyzing(true);
    
    try {
      const response = await dataBuilderAPI.analyzeData(jobId!, {
        query: chatInput
      });
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.analysis,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Handle suggested actions
      if (response.suggested_actions && response.suggested_actions.length > 0) {
        const actionMessage: ChatMessage = {
          id: (Date.now() + 2).toString(),
          role: 'system',
          content: `Suggested actions:\n${response.suggested_actions.map((action: any) => 
            `• ${action.description}`
          ).join('\n')}\n\nWould you like me to perform any of these?`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, actionMessage]);
      }
    } catch (error) {
      console.error('Failed to analyze:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error while analyzing your request. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  const handleEdit = async () => {
    if (!editingSample) return;
    
    // In real implementation, call API to update
    const updatedData = data.map(sample => 
      sample.id === editingSample.id 
        ? { ...sample, content: editContent, label: editLabel }
        : sample
    );
    
    setData(updatedData);
    setFilteredData(updatedData);
    setEditingSample(null);
    
    toast({
      title: "Sample updated",
      description: "The data sample has been updated successfully.",
    });
  };
  
  const handleDelete = async (id: string) => {
    // In real implementation, call API to delete
    const updatedData = data.filter(sample => sample.id !== id);
    setData(updatedData);
    setFilteredData(updatedData);
    
    toast({
      title: "Sample deleted",
      description: "The data sample has been removed.",
    });
  };
  
  const exportData = async () => {
    try {
      // In real implementation, call API to export
      const blob = new Blob([JSON.stringify(filteredData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `metra-data-${jobId}.json`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast({
        title: "Data exported",
        description: `Exported ${filteredData.length} samples successfully.`,
      });
    } catch (error) {
      toast({
        title: "Export failed",
        description: "Failed to export data.",
        variant: "destructive",
      });
    }
  };

  return (
    <Dialog open={true} onOpenChange={handleClose}>
      <DialogContent className="max-w-7xl h-[90vh] p-0">
        <div className="flex h-full overflow-hidden">
          {/* Main Content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <DialogHeader className="p-6 pb-4 border-b">
              <div className="flex items-center justify-between">
                <DialogTitle className="text-xl">Data Collection Results</DialogTitle>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-green-600 border-green-200">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    {totalCount} samples
                  </Badge>
                  <Button variant="ghost" size="icon" onClick={handleClose}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </DialogHeader>
            
            {/* Filters */}
            <div className="p-4 border-b bg-gray-50 space-y-3">
              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search in content..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
                
                <Select value={labelFilter} onValueChange={setLabelFilter}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="All labels" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All labels</SelectItem>
                    {stats && Object.keys(stats.label_distribution).map(label => (
                      <SelectItem key={label} value={label}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                <Select value={sourceFilter} onValueChange={setSourceFilter}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="All sources" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All sources</SelectItem>
                    {stats && Object.keys(stats.source_distribution).map(source => (
                      <SelectItem key={source} value={source}>{source}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                <Button onClick={exportData} variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
              </div>
              
              {/* Statistics */}
              {stats && (
                <div className="grid grid-cols-3 gap-4 pt-2">
                  <div className="text-sm">
                    <p className="text-gray-500">Label Distribution</p>
                    <div className="space-y-1 mt-1">
                      {Object.entries(stats.label_distribution).map(([label, count]) => (
                        <div key={label} className="flex justify-between">
                          <span>{label}:</span>
                          <span className="font-medium">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="text-sm">
                    <p className="text-gray-500">Source Distribution</p>
                    <div className="space-y-1 mt-1">
                      {Object.entries(stats.source_distribution).map(([source, count]) => (
                        <div key={source} className="flex justify-between">
                          <span>{source}:</span>
                          <span className="font-medium">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="text-sm">
                    <p className="text-gray-500">Data Quality</p>
                    <div className="mt-1">
                      <p className="text-2xl font-semibold text-green-600">
                        {(stats.average_confidence * 100).toFixed(1)}%
                      </p>
                      <p className="text-xs text-gray-500">Average confidence</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* Data List */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-2">
                {loading ? (
                  <div className="text-center py-8 text-gray-500">Loading data...</div>
                ) : filteredData.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">No data found</div>
                ) : (
                  filteredData.map((sample) => (
                    <Card key={sample.id} className="p-3">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 overflow-hidden">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant="outline">{sample.label}</Badge>
                            <Badge variant="secondary" className="text-xs">
                              {sample.source}
                            </Badge>
                            {sample.confidence && (
                              <span className="text-xs text-gray-500">
                                {(sample.confidence * 100).toFixed(0)}% confidence
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-700 truncate">
                            {sample.content}
                          </p>
                        </div>
                        
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              setEditingSample(sample);
                              setEditContent(sample.content);
                              setEditLabel(sample.label || '');
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(sample.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))
                )}
              </div>
              
              {/* Pagination */}
              {totalCount > pageSize && (
                <div className="flex justify-center gap-2 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(p => Math.max(0, p - 1))}
                    disabled={currentPage === 0}
                  >
                    Previous
                  </Button>
                  <span className="px-3 py-1 text-sm">
                    Page {currentPage + 1} of {Math.ceil(totalCount / pageSize)}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(p => p + 1)}
                    disabled={(currentPage + 1) * pageSize >= totalCount}
                  >
                    Next
                  </Button>
                </div>
              )}
            </ScrollArea>
            
            {/* Action Footer */}
            <div className="p-4 border-t bg-gray-50">
              <div className="flex justify-between items-center">
                <p className="text-sm text-gray-600">
                  Showing {filteredData.length} of {totalCount} samples
                </p>
                <Button
                  size="lg"
                  onClick={() => {
                    // Navigate to model builder for training
                    navigate(`/dashboard?section=model-builder&data_task=${jobId}&processed_count=${totalCount}`);
                  }}
                >
                  Continue to Training
                </Button>
              </div>
            </div>
          </div>
          
          {/* Chat Sidebar */}
          <div className="w-96 border-l flex flex-col bg-gray-50 flex-shrink-0">
            <div className="p-4 border-b bg-white">
              <h3 className="font-semibold flex items-center gap-2">
                <Bot className="h-5 w-5 text-purple-600" />
                Data AI Assistant
              </h3>
            </div>
            
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-lg p-3 ${
                        message.role === 'user'
                          ? 'bg-purple-600 text-white'
                          : message.role === 'system'
                          ? 'bg-amber-100 text-amber-900'
                          : 'bg-white text-gray-800'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      <p className="text-xs opacity-70 mt-1">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
                {isAnalyzing && (
                  <div className="flex justify-start">
                    <div className="bg-white rounded-lg p-3">
                      <p className="text-sm text-gray-500">Analyzing...</p>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
            
            <div className="p-4 border-t bg-white">
              <div className="flex gap-2">
                <Input
                  placeholder="Ask about your data..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleChat()}
                  disabled={isAnalyzing}
                />
                <Button onClick={handleChat} disabled={isAnalyzing || !chatInput.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
        
        {/* Edit Dialog */}
        {editingSample && (
          <Dialog open={!!editingSample} onOpenChange={() => setEditingSample(null)}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Edit Sample</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Content</Label>
                  <Textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={4}
                  />
                </div>
                <div>
                  <Label>Label</Label>
                  <Input
                    value={editLabel}
                    onChange={(e) => setEditLabel(e.target.value)}
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setEditingSample(null)}>
                    Cancel
                  </Button>
                  <Button onClick={handleEdit}>
                    Save Changes
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default DataViewer; 