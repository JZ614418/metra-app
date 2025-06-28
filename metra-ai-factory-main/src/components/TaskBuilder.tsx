import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { MessageCircle, Send, User, Bot, ArrowRight, Sparkles, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useConversationStore } from '@/stores/conversationStore';
import { useNavigate } from 'react-router-dom';

const TaskBuilder = () => {
  const navigate = useNavigate();
  const [currentInput, setCurrentInput] = useState('');
  const [taskName, setTaskName] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [extractedSchema, setExtractedSchema] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const {
    currentConversation,
    isLoading,
    isStreaming,
    streamingMessage,
    error,
    createConversation,
    sendMessageStream,
    createTaskDefinition,
    clearError
  } = useConversationStore();

  // Create conversation on mount
  useEffect(() => {
    const initConversation = async () => {
      if (!currentConversation) {
        await createConversation();
      }
    };
    initConversation();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentConversation?.messages, streamingMessage]);

  // Extract JSON schema from AI message
  useEffect(() => {
    if (currentConversation?.is_completed) {
      const lastAiMessage = [...(currentConversation.messages || [])]
        .reverse()
        .find(m => m.role === 'assistant');
      
      if (lastAiMessage) {
        const jsonMatch = lastAiMessage.content.match(/```json\s*([\s\S]*?)\s*```/);
        if (jsonMatch) {
          try {
            const schema = JSON.parse(jsonMatch[1]);
            setExtractedSchema(schema);
            setShowTaskForm(true);
          } catch (e) {
            console.error('Failed to parse JSON schema:', e);
          }
        }
      }
    }
  }, [currentConversation]);

  const handleSendMessage = async () => {
    if (!currentInput.trim() || !currentConversation || isStreaming) return;

    const message = currentInput;
    setCurrentInput('');
    
    try {
      await sendMessageStream(currentConversation.id, message);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSaveTaskDefinition = async () => {
    if (!currentConversation || !taskName.trim()) return;

    try {
      await createTaskDefinition(
        currentConversation.id,
        taskName,
        taskDescription || undefined
      );
      // Navigate to next step
      navigate('/model-recommend');
    } catch (error) {
      console.error('Failed to save task definition:', error);
    }
  };

  const formatMessage = (content: string) => {
    // Convert markdown code blocks to formatted display
    return content.split('\n').map((line, i) => (
      <span key={i}>
        {line}
        <br />
      </span>
    ));
  };

  return (
    <div className="p-8 space-y-6 max-w-5xl mx-auto">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error}
            <Button
              variant="link"
              size="sm"
              className="ml-2 p-0 h-auto"
              onClick={clearError}
            >
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

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
            {currentConversation?.is_completed && (
              <Badge className="bg-green-100 text-green-700 border-green-200">
                <CheckCircle className="h-3 w-3 mr-1" />
                Schema Generated
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {/* Chat messages */}
          <div className="h-96 overflow-y-auto space-y-4 mb-4 p-4 bg-gray-50 rounded-lg">
            {currentConversation?.messages.map((message) => (
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
                    <div className="text-sm whitespace-pre-wrap">
                      {formatMessage(message.content)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Streaming message */}
            {isStreaming && streamingMessage && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-gray-900 flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-bold text-sm">M</span>
                </div>
                <div className="bg-gray-100 border border-gray-200 p-3 rounded-lg">
                  <div className="text-sm whitespace-pre-wrap">
                    {formatMessage(streamingMessage)}
                  </div>
                </div>
              </div>
            )}
            
            {/* Typing indicator */}
            {isStreaming && !streamingMessage && (
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
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          {!currentConversation?.is_completed && (
            <div className="flex gap-3">
              <Input
                placeholder="Type your message..."
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                onKeyPress={handleKeyPress}
                className="flex-1"
                disabled={isStreaming || isLoading}
              />
              <Button 
                onClick={handleSendMessage}
                disabled={!currentInput.trim() || isStreaming || isLoading}
                className="bg-gray-900 hover:bg-gray-800"
              >
                {isStreaming ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Task definition form */}
      {showTaskForm && extractedSchema && (
        <Card className="border-0 shadow-sm bg-green-50/30">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-green-600" />
              <CardTitle className="text-lg text-gray-900">Save Task Definition</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Task Name *</label>
              <Input
                placeholder="e.g., Customer Review Sentiment Analysis"
                value={taskName}
                onChange={(e) => setTaskName(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Description (Optional)</label>
              <Input
                placeholder="Brief description of your task"
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Generated Schema</label>
              <div className="bg-gray-100 p-3 rounded-lg overflow-auto max-h-48">
                <pre className="text-xs">{JSON.stringify(extractedSchema, null, 2)}</pre>
              </div>
            </div>
            
            <div className="pt-4 flex justify-end gap-3">
              <Button
                variant="outline"
                onClick={() => setShowTaskForm(false)}
              >
                Cancel
              </Button>
              <Button 
                onClick={handleSaveTaskDefinition}
                disabled={!taskName.trim() || isLoading}
                className="bg-gray-900 hover:bg-gray-800"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    Save & Continue
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default TaskBuilder;
