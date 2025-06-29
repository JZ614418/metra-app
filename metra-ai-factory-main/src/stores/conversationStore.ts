import { create } from 'zustand';
import { api } from '@/lib/api';

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string | null;
  is_completed: boolean;
  created_at: string;
  updated_at: string | null;
  messages: Message[];
}

export interface ConversationList {
  id: string;
  title: string | null;
  is_completed: boolean;
  created_at: string;
  message_count: number;
}

export interface TaskDefinition {
  id: string;
  conversation_id: string;
  user_id: string;
  name: string;
  description: string | null;
  json_schema: any;
  recommended_models: string[] | null;
  created_at: string;
  updated_at: string | null;
}

interface ConversationStore {
  // State
  conversations: ConversationList[];
  currentConversation: Conversation | null;
  isLoading: boolean;
  error: string | null;
  isStreaming: boolean;
  streamingMessage: string;

  // Actions
  createConversation: (title?: string) => Promise<Conversation>;
  loadConversations: () => Promise<void>;
  loadConversation: (id: string) => Promise<void>;
  sendMessage: (conversationId: string, content: string) => Promise<Message>;
  sendMessageStream: (conversationId: string, content: string) => Promise<void>;
  createTaskDefinition: (conversationId: string, name: string, description?: string) => Promise<TaskDefinition>;
  clearError: () => void;
  reset: () => void;
}

export const useConversationStore = create<ConversationStore>((set, get) => ({
  // Initial state
  conversations: [],
  currentConversation: null,
  isLoading: false,
  error: null,
  isStreaming: false,
  streamingMessage: '',

  // Create new conversation
  createConversation: async (title?: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post('/conversations', { title });
      const conversation = response.data;
      set(state => ({
        conversations: [conversation, ...state.conversations],
        currentConversation: conversation,
        isLoading: false
      }));
      return conversation;
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to create conversation', isLoading: false });
      throw error;
    }
  },

  // Load all conversations
  loadConversations: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get('/conversations');
      set({ conversations: response.data, isLoading: false });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to load conversations', isLoading: false });
    }
  },

  // Load specific conversation
  loadConversation: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get(`/conversations/${id}`);
      set({ currentConversation: response.data, isLoading: false });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to load conversation', isLoading: false });
    }
  },

  // Send message (non-streaming)
  sendMessage: async (conversationId: string, content: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post(`/conversations/${conversationId}/messages`, {
        content,
        role: 'user'
      });
      
      // Update current conversation with new message
      const currentConv = get().currentConversation;
      if (currentConv && currentConv.id === conversationId) {
        set({
          currentConversation: {
            ...currentConv,
            messages: [...currentConv.messages, response.data]
          },
          isLoading: false
        });
      }
      
      return response.data;
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to send message', isLoading: false });
      throw error;
    }
  },

  // Send message with streaming
  sendMessageStream: async (conversationId: string, content: string) => {
    set({ isStreaming: true, error: null, streamingMessage: '' });
    
    try {
      // First, add user message
      const userMessage: Message = {
        id: Date.now().toString(),
        conversation_id: conversationId,
        role: 'user',
        content,
        created_at: new Date().toISOString()
      };
      
      const currentConv = get().currentConversation;
      if (currentConv) {
        set({
          currentConversation: {
            ...currentConv,
            messages: [...currentConv.messages, userMessage]
          }
        });
      }
      
      // Create streaming response
      const responseBody = await api.post<ReadableStream>(
        `/conversations/${conversationId}/messages/stream`,
        { content, role: 'user' },
        true
      );
      
      const reader = responseBody?.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';
      
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') {
                // Streaming complete
                set({ isStreaming: false });
                
                // Add complete assistant message
                const aiMessage: Message = {
                  id: (Date.now() + 1).toString(),
                  conversation_id: conversationId,
                  role: 'assistant',
                  content: assistantMessage,
                  created_at: new Date().toISOString()
                };
                
                const conv = get().currentConversation;
                if (conv) {
                  set({
                    currentConversation: {
                      ...conv,
                      messages: [...conv.messages.slice(0, -1), userMessage, aiMessage],
                      is_completed: assistantMessage.includes('I now have enough information')
                    }
                  });
                }
              } else if (data.startsWith('ERROR: ')) {
                throw new Error(data.slice(7));
              } else {
                // Append to streaming message
                assistantMessage += data;
                set({ streamingMessage: assistantMessage });
              }
            }
          }
        }
      }
    } catch (error: any) {
      set({ error: error.message || 'Failed to send message', isStreaming: false });
      throw error;
    }
  },

  // Create task definition
  createTaskDefinition: async (conversationId: string, name: string, description?: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post('/task-definitions', {
        conversation_id: conversationId,
        name,
        description
      });
      
      // Update conversation status
      const currentConv = get().currentConversation;
      if (currentConv && currentConv.id === conversationId) {
        set({
          currentConversation: {
            ...currentConv,
            is_completed: true
          }
        });
      }
      
      return response.data;
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Failed to create task definition', isLoading: false });
      throw error;
    }
  },

  clearError: () => set({ error: null }),
  
  reset: () => set({
    conversations: [],
    currentConversation: null,
    isLoading: false,
    error: null,
    isStreaming: false,
    streamingMessage: ''
  })
})); 