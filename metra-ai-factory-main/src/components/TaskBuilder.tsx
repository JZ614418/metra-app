import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { MessageCircle, Send, User, Bot, ArrowRight, Sparkles, CheckCircle, AlertCircle, Loader2, ThumbsUp } from 'lucide-react';
import { useConversationStore } from '@/stores/conversationStore';
import { useNavigate } from 'react-router-dom';

const SchemaDisplay = ({ schema }: { schema: any }) => {
  if (!schema || typeof schema !== 'object') {
    return <pre className="text-xs">{JSON.stringify(schema, null, 2)}</pre>;
  }

  const renderValue = (value: any) => {
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    if (Array.isArray(value)) {
      return value.join(', ');
    }
    if (typeof value === 'object' && value !== null) {
      return (
        <ul className="list-disc list-inside pl-4">
          {Object.entries(value).map(([key, val]) => (
            <li key={key}>
              <span className="font-semibold capitalize">{key.replace(/_/g, ' ')}:</span> {renderValue(val)}
            </li>
          ))}
        </ul>
      );
    }
    return value;
  };

  return (
    <div className="space-y-2 text-sm">
      {Object.entries(schema).map(([key, value]) => (
        <div key={key}>
          <p className="font-semibold capitalize">{key.replace(/_/g, ' ')}:</p>
          <div className="pl-4 text-gray-700">{renderValue(value)}</div>
        </div>
      ))}
    </div>
  );
};

const MessageContent = ({ content }: { content: string }) => {
  const parts = content.split(/```json\s*([\s\S]*?)\s*```/);
  
  return (
    <div>
      {parts.map((part, index) => {
        if (index % 2 === 1) { // This is the JSON part
          try {
            const schema = JSON.parse(part);
            return <SchemaDisplay key={index} schema={schema} />;
          } catch (e) {
            return <pre key={index} className="text-xs bg-gray-200 p-2 rounded">{`\`\`\`json\n${part}\n\`\`\``}</pre>;
          }
        } else { // This is the text part
          return <span key={index}>{part}</span>;
        }
      })}
    </div>
  );
};

const TaskBuilder = () => {
  const navigate = useNavigate();
  const [currentInput, setCurrentInput] = useState('');
  const [taskName, setTaskName] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [showConfirmButton, setShowConfirmButton] = useState(false);
  const [confirmationOffered, setConfirmationOffered] = useState(false);
  const [schema, setSchema] = useState<any>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const {
    currentConversation,
    isLoading,
    isStreaming,
    error,
    createConversation,
    sendMessageStream,
    createTaskDefinition,
    setConversationCompleted,
    clearError
  } = useConversationStore();

  useEffect(() => {
    const initConversation = async () => {
      if (!currentConversation) {
        try {
          await createConversation();
        } catch (error) {
          console.error("Failed to initialize conversation:", error);
        }
      }
    };
    initConversation();
  }, [createConversation, currentConversation]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentConversation?.messages]);

  useEffect(() => {
    if (!currentConversation) return;

    const messages = currentConversation.messages;
    const lastMessage = messages?.[messages.length - 1];

    // Extract schema if present in the last message
    if (lastMessage?.role === 'assistant' && lastMessage.content.includes("```json")) {
      const jsonMatch = lastMessage.content.match(/```json\s*([\s\S]*?)\s*```/);
      if (jsonMatch) {
        try {
          const parsedSchema = JSON.parse(jsonMatch[1]);
          setSchema(parsedSchema);
        } catch (e) {
          console.error('Failed to parse JSON schema:', e);
        }
      }
    }
    
    // Check if the AI has offered the schema for confirmation
    if (lastMessage?.role === 'assistant' && lastMessage.content.includes("```json") && lastMessage.content.toLowerCase().includes("ok")) {
      setConfirmationOffered(true);
    }
    
    // Once confirmation is offered, we only check the user's response
    if (confirmationOffered) {
      const lastUserMessage = messages.filter(m => m.role === 'user').pop();
      if (lastUserMessage) {
        const confirmationText = lastUserMessage.content.toLowerCase();
        if (confirmationText.includes('ok') || confirmationText.includes('yes')) {
          setShowConfirmButton(true);
        }
      }
    }

    if (currentConversation.is_completed) {
      setShowTaskForm(true);
    }

  }, [currentConversation, currentConversation?.messages, confirmationOffered]);

  const handleConfirmSchema = () => {
    if (currentConversation) {
      setConversationCompleted(currentConversation.id);
    }
  };
  
  const handleSendMessage = async () => {
    if (!currentInput.trim() || !currentConversation || isStreaming) {
      console.warn("SendMessage cancelled: ", {
        input: !currentInput.trim(),
        conv: !currentConversation,
        streaming: isStreaming,
      });
      return;
    }

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
                Schema Confirmed
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {/* Chat messages */}
          <div className="h-96 overflow-y-auto space-y-4 mb-4 p-4 bg-gray-50 rounded-lg">
            {currentConversation?.messages.map((message, index) => {
              const isLastMessage = index === currentConversation.messages.length - 1;
              const isAiTyping = isStreaming && isLastMessage && message.role === 'assistant';

              return (
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
                      {isAiTyping && message.content.length === 0 ? (
                        <div className="flex gap-1 items-center h-5">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      ) : (
                        <div className="text-sm whitespace-pre-wrap">
                          <MessageContent content={message.content} />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Action buttons area */}
          {showConfirmButton && !currentConversation?.is_completed && (
            <div className="flex justify-center p-4 border-t">
              <Button onClick={handleConfirmSchema}>
                <ThumbsUp className="mr-2 h-4 w-4" />
                Finalize & Continue to Next Step
              </Button>
            </div>
          )}

          {/* Input area - always visible until task is confirmed */}
          {!currentConversation?.is_completed && !showConfirmButton && (
            <div className="flex gap-3 mt-4">
              <Input
                placeholder="Type your response..."
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isStreaming}
              />
              <Button onClick={handleSendMessage} disabled={isStreaming}>
                {isStreaming ? <Loader2 className="animate-spin" /> : <Send />}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Task definition form */}
      {showTaskForm && (
        <Card className="border-0 shadow-sm bg-green-50/30">
          <CardHeader>
            <CardTitle className="text-lg text-gray-900">Save Task Definition</CardTitle>
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
              <label className="text-sm font-medium">Generated Schema Summary</label>
              <div className="bg-gray-100 p-3 rounded-lg overflow-auto max-h-48">
                <SchemaDisplay schema={schema} />
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
