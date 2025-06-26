import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { MessageCircle, Send, User, Bot, ArrowRight, Sparkles, CheckCircle } from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface TaskSchema {
  taskType?: string;
  inputFields?: string[];
  outputFields?: string[];
  modelType?: string;
  dataRequirement?: string;
  successCriteria?: string;
}

const TaskBuilder = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m Metra AI assistant. Please describe in one sentence what kind of AI model you want to train. For example: "I want an AI that can determine if customer reviews are complaints."',
      timestamp: new Date()
    }
  ]);
  const [currentInput, setCurrentInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [taskSchema, setTaskSchema] = useState<TaskSchema>({});
  const [conversationStep, setConversationStep] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  const conversationFlow = [
    {
      extractInfo: (input: string) => {
        // Identify task type
        if (input.includes('classify') || input.includes('determine') || input.includes('identify') || input.includes('detect')) {
          setTaskSchema(prev => ({ ...prev, taskType: 'classification' }));
          return 'I understand, you need a classification model. What kind of input data will you use? For example: "customer review text", "product images", etc.';
        } else if (input.includes('generate') || input.includes('create') || input.includes('write')) {
          setTaskSchema(prev => ({ ...prev, taskType: 'generation' }));
          return 'I understand, you need a generation model. What kind of content do you want to generate?';
        } else {
          return 'Let me clarify: Do you want to classify/identify certain content, or generate/create new content?';
        }
      }
    },
    {
      extractInfo: (input: string) => {
        setTaskSchema(prev => ({ ...prev, inputFields: [input] }));
        return `Got it, the input is ${input}. What output do you expect? For example: "complaint or not (yes/no)", "sentiment (positive/negative/neutral)", etc.`;
      }
    },
    {
      extractInfo: (input: string) => {
        setTaskSchema(prev => ({ ...prev, outputFields: [input] }));
        return 'Understood. How much training data do you have approximately? If you don\'t have any, no worries - we can help generate or collect it.';
      }
    },
    {
      extractInfo: (input: string) => {
        setTaskSchema(prev => ({ ...prev, dataRequirement: input }));
        return 'Finally, do you have any requirements for model accuracy? For example: "accuracy above 90%".';
      }
    },
    {
      extractInfo: (input: string) => {
        setTaskSchema(prev => ({ ...prev, successCriteria: input }));
        setIsComplete(true);
        return 'Perfect! I\'ve understood your requirements. Generating task definition...';
      }
    }
  ];

  const handleSendMessage = () => {
    if (!currentInput.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: currentInput,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentInput('');

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
        content: conversationFlow[conversationStep]?.extractInfo(currentInput) || 'I understand. Let me process this information.',
          timestamp: new Date()
        };
        
      setMessages(prev => [...prev, aiResponse]);
      
      if (conversationStep < conversationFlow.length - 1) {
        setConversationStep(prev => prev + 1);
      }
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getTaskTypeLabel = (type: string) => {
    switch (type) {
      case 'classification':
        return 'Classification Task';
      case 'generation':
        return 'Generation Task';
      default:
        return 'Undefined';
    }
  };

  const proceedToModelRecommend = () => {
    // Navigate to next step (model recommendation)
    console.log('Task schema:', taskSchema);
  };

  return (
    <div className="p-8 space-y-6 max-w-5xl mx-auto">
      {/* Conversation area */}
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-lg">M</span>
            </div>
            <div>
                <CardTitle className="text-xl">Task Definition Dialogue</CardTitle>
                <p className="text-sm text-gray-500 mt-1">Let AI understand your needs through conversation</p>
              </div>
            </div>
            <Badge variant="outline" className="text-gray-600 border-gray-200">
              Step {conversationStep + 1} / 5
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {/* Chat messages */}
          <div className="h-96 overflow-y-auto space-y-4 mb-4 p-4 bg-gray-50 rounded-lg">
          {messages.map((message) => (
            <div key={message.id} className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex gap-3 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user' 
                      ? 'bg-gray-900' 
                      : 'bg-gray-900'
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
                      : 'bg-gray-100 border border-gray-200'
                }`}>
                  <p className="text-sm">{message.content}</p>
                </div>
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-gray-900 flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-bold text-sm">M</span>
              </div>
                <div className="bg-gray-100 border border-gray-200 p-3 rounded-lg">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>

          {/* Input area */}
          {!isComplete && (
        <div className="flex gap-3">
          <Input
                placeholder="Type your message..."
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            onKeyPress={handleKeyPress}
                className="flex-1"
            disabled={isTyping}
          />
          <Button 
            onClick={handleSendMessage}
            disabled={!currentInput.trim() || isTyping}
                className="bg-gray-900 hover:bg-gray-800"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
          )}
        </CardContent>
      </Card>

      {/* Task definition summary */}
      {isComplete && (
        <Card className="border-0 shadow-sm bg-green-50/30">
          <CardHeader>
          <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-green-600" />
              <CardTitle className="text-lg text-gray-900">Task Definition Complete!</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <p className="text-sm text-gray-500">Task Type</p>
                <p className="font-medium">{getTaskTypeLabel(taskSchema.taskType || '')}</p>
            </div>
              <div className="space-y-2">
                <p className="text-sm text-gray-500">Input Data</p>
                <p className="font-medium">{taskSchema.inputFields?.[0] || 'Not defined'}</p>
            </div>
              <div className="space-y-2">
                <p className="text-sm text-gray-500">Expected Output</p>
                <p className="font-medium">{taskSchema.outputFields?.[0] || 'Not defined'}</p>
            </div>
              <div className="space-y-2">
                <p className="text-sm text-gray-500">Data Status</p>
                <p className="font-medium">{taskSchema.dataRequirement || 'Not specified'}</p>
            </div>
          </div>
          
            <div className="pt-4 flex justify-end">
              <Button 
                onClick={proceedToModelRecommend}
                className="bg-gray-900 hover:bg-gray-800"
              >
                Next: Select Base Model
                <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default TaskBuilder;
