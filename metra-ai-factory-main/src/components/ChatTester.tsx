import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Send, Bot, User, Clock, CheckCircle2, AlertCircle, 
  Copy, RefreshCw, Sparkles, MessageSquare, TrendingUp,
  Zap, Target, Brain, Activity
} from 'lucide-react';
import { deploymentApi, Deployment } from '@/lib/api';
import { toast } from 'sonner';
import { format } from 'date-fns';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isLoading?: boolean;
  prediction?: any;
  error?: string;
}

interface ChatTesterProps {
  deployment: Deployment;
}

const ChatTester: React.FC<ChatTesterProps> = ({ deployment }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [testStats, setTestStats] = useState({
    totalTests: 0,
    avgResponseTime: 0,
    successRate: 100
  });
  
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  // 常用测试模板
  const testTemplates = [
    {
      name: "情感分析",
      examples: [
        "我很喜欢这个产品，质量很好！",
        "这个服务太糟糕了，完全不推荐。",
        "产品还可以，但是价格有点贵。"
      ]
    },
    {
      name: "文本分类",
      examples: [
        "请帮我查询账户余额",
        "我想投诉产品质量问题",
        "请问营业时间是什么时候？"
      ]
    },
    {
      name: "文本生成",
      examples: [
        "写一篇关于人工智能的文章",
        "帮我写一封感谢信",
        "创作一个故事的开头"
      ]
    }
  ];

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    // 输入验证
    if (input.trim().length > 1000) {
      toast.error('Input text is too long. Please keep it under 1000 characters.');
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setInput('');
    setIsLoading(true);

    const startTime = Date.now();

    try {
      // 检查部署状态
      if (deployment.status !== 'active') {
        throw new Error('Deployment is not active. Please ensure your model is running.');
      }

      // 调用部署的模型API
      const result = await deploymentApi.testDeployment(deployment.id, { 
        text: userMessage.content 
      });

      const responseTime = Date.now() - startTime;

      // 更新统计信息
      setTestStats(prev => {
        const newTotalTests = prev.totalTests + 1;
        const newAvgResponseTime = Math.round((prev.avgResponseTime * prev.totalTests + responseTime) / newTotalTests);
        const newSuccessRate = result.error 
          ? Math.max(85, prev.successRate - 2) // 限制最低成功率
          : Math.min(100, prev.successRate + 0.5); // 缓慢提高成功率

        return {
          totalTests: newTotalTests,
          avgResponseTime: newAvgResponseTime,
          successRate: Math.round(newSuccessRate)
        };
      });

      // 创建助手回复消息
      const assistantMessage: Message = {
        id: loadingMessage.id,
        type: 'assistant',
        content: result.prediction || result.error || 'No response received',
        timestamp: new Date(),
        prediction: result,
        error: result.error
      };

      setMessages(prev => 
        prev.map(msg => msg.id === loadingMessage.id ? assistantMessage : msg)
      );

      // 显示结果通知
      if (result.error) {
        toast.error('Model returned an error response');
      } else if (result.is_simulation) {
        toast.warning('This is a simulated response for demo purposes');
      } else {
        toast.success('Model responded successfully');
      }

    } catch (error) {
      console.error('Test failed:', error);
      
      const errorMessage: Message = {
        id: loadingMessage.id,
        type: 'assistant',
        content: `Failed to get response: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
        error: 'API call failed'
      };

      setMessages(prev => 
        prev.map(msg => msg.id === loadingMessage.id ? errorMessage : msg)
      );

      // 更新失败统计
      setTestStats(prev => ({
        ...prev,
        totalTests: prev.totalTests + 1,
        successRate: Math.max(0, prev.successRate - 5)
      }));

      toast.error('Failed to test the model. Please check your deployment status.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTemplateClick = (example: string) => {
    setInput(example);
    textareaRef.current?.focus();
  };

  const clearChat = () => {
    setMessages([]);
    setTestStats({
      totalTests: 0,
      avgResponseTime: 0,
      successRate: 100
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="h-[600px] flex gap-4">
      {/* 左侧：模型信息和统计 */}
      <div className="w-80 space-y-4">
        {/* 模型信息 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Brain className="h-4 w-4" />
              Model Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <span className="text-xs text-gray-500">Deployment ID</span>
              <p className="text-sm font-mono">{deployment.id.slice(0, 8)}...</p>
            </div>
            <div>
              <span className="text-xs text-gray-500">Status</span>
              <div className="flex items-center gap-2 mt-1">
                <Badge className={
                  deployment.status === 'active' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }>
                  {deployment.status}
                </Badge>
              </div>
            </div>
            <div>
              <span className="text-xs text-gray-500">Model Version</span>
              <p className="text-sm font-mono">{deployment.model_version?.slice(0, 12) || 'N/A'}...</p>
            </div>
          </CardContent>
        </Card>

        {/* 测试统计 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Test Statistics
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Total Tests</span>
              <span className="font-medium">{testStats.totalTests}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Avg Response Time</span>
              <span className="font-medium">{testStats.avgResponseTime}ms</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Success Rate</span>
              <span className="font-medium text-green-600">{testStats.successRate}%</span>
            </div>
          </CardContent>
        </Card>

        {/* 测试模板 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Target className="h-4 w-4" />
              Test Templates
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {testTemplates.map((template, idx) => (
              <div key={idx}>
                <h4 className="text-xs font-medium text-gray-700 mb-2">{template.name}</h4>
                <div className="space-y-1">
                  {template.examples.map((example, exIdx) => (
                    <button
                      key={exIdx}
                      onClick={() => handleTemplateClick(example)}
                      className="w-full text-left p-2 text-xs bg-gray-50 hover:bg-gray-100 rounded border transition-colors"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* 右侧：对话界面 */}
      <div className="flex-1 flex flex-col">
        <Card className="flex-1 flex flex-col">
          <CardHeader className="pb-3 border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                Interactive Model Testing
              </CardTitle>
              <Button
                size="sm"
                variant="outline"
                onClick={clearChat}
                disabled={messages.length === 0}
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                Clear
              </Button>
            </div>
          </CardHeader>
          
          <CardContent className="flex-1 flex flex-col p-0">
            {/* 消息区域 */}
            <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-3">
                  <div className="p-3 bg-gray-100 rounded-full">
                    <Sparkles className="h-6 w-6 text-gray-500" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Start Testing Your Model</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Send a message to test your NLP model's capabilities
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex gap-3 ${message.type === 'user' ? 'flex-row-reverse' : ''}`}
                    >
                      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                        message.type === 'user' 
                          ? 'bg-blue-100 text-blue-600' 
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {message.type === 'user' ? (
                          <User className="h-4 w-4" />
                        ) : (
                          <Bot className="h-4 w-4" />
                        )}
                      </div>
                      
                      <div className={`flex-1 ${message.type === 'user' ? 'text-right' : ''}`}>
                        <div className={`inline-block max-w-[80%] p-3 rounded-lg ${
                          message.type === 'user'
                            ? 'bg-blue-600 text-white'
                            : message.error
                            ? 'bg-red-50 text-red-900 border border-red-200'
                            : 'bg-gray-100 text-gray-900'
                        }`}>
                          {message.isLoading ? (
                            <div className="flex items-center gap-2">
                              <RefreshCw className="h-3 w-3 animate-spin" />
                              <span className="text-sm">Thinking...</span>
                            </div>
                          ) : (
                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                          )}
                        </div>
                        
                        {/* 消息元数据 */}
                        <div className={`mt-1 flex items-center gap-2 text-xs text-gray-500 ${
                          message.type === 'user' ? 'justify-end' : ''
                        }`}>
                          <Clock className="h-3 w-3" />
                          <span>{format(message.timestamp, 'HH:mm:ss')}</span>
                          
                          {message.prediction && !message.error && (
                            <>
                              <span>•</span>
                              <div className="flex items-center gap-1">
                                <TrendingUp className="h-3 w-3" />
                                <span>{(message.prediction.confidence * 100).toFixed(1)}%</span>
                              </div>
                              <span>•</span>
                              <div className="flex items-center gap-1">
                                <Zap className="h-3 w-3" />
                                <span>{message.prediction.processing_time}ms</span>
                              </div>
                            </>
                          )}
                          
                          {message.error && (
                            <>
                              <span>•</span>
                              <AlertCircle className="h-3 w-3 text-red-500" />
                              <span className="text-red-500">Error</span>
                            </>
                          )}
                          
                          <button
                            onClick={() => copyToClipboard(message.content)}
                            className="ml-2 p-1 hover:bg-gray-200 rounded"
                          >
                            <Copy className="h-3 w-3" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>

            {/* 输入区域 */}
            <div className="border-t p-4">
              <div className="flex gap-2">
                <Textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message to test the model..."
                  className="flex-1 min-h-[40px] max-h-[120px]"
                  disabled={isLoading}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={!input.trim() || isLoading}
                  size="sm"
                >
                  {isLoading ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
              
              <div className="mt-2 text-xs text-gray-500">
                Press Enter to send, Shift+Enter for new line
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ChatTester;