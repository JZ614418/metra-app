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
  setConversationCompleted: (conversationId: string) => void;
}

const INTRO_MESSAGE: Message = {
  id: 'intro-message',
  conversation_id: 'intro',
  role: 'assistant',
  content: "Hello! I'm Metra AI, your assistant for building custom AI models. You don't need any programming knowledge—just tell me what you're trying to achieve, and I'll guide you through the process of defining your task. So, what problem are you looking to solve?",
  created_at: new Date().toISOString()
};

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
      const conversation = await api.post<Conversation>('/conversations', { title });
      set(state => ({
        conversations: [conversation, ...state.conversations],
        currentConversation: { ...conversation, messages: [INTRO_MESSAGE] },
        isLoading: false
      }));
      return conversation;
    } catch (error: any) {
      set({ error: error.message || 'Failed to create conversation', isLoading: false });
      throw error;
    }
  },

  // Load all conversations
  loadConversations: async () => {
    set({ isLoading: true, error: null });
    try {
      const conversations = await api.request<ConversationList[]>('/conversations');
      set({ conversations, isLoading: false });
    } catch (error: any) {
      set({ error: error.message || 'Failed to load conversations', isLoading: false });
    }
  },

  // Load specific conversation
  loadConversation: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const conversation = await api.request<Conversation>(`/conversations/${id}`);
      set({ currentConversation: conversation, isLoading: false });
    } catch (error: any) {
      set({ error: error.message || 'Failed to load conversation', isLoading: false });
    }
  },

  // Send message (non-streaming)
  sendMessage: async (conversationId: string, content: string) => {
    set({ isLoading: true, error: null });
    try {
      const message = await api.post<Message>(`/conversations/${conversationId}/messages`, {
        content,
        role: 'user'
      });
      
      // Update current conversation with new message
      const currentConv = get().currentConversation;
      if (currentConv && currentConv.id === conversationId) {
        set({
          currentConversation: {
            ...currentConv,
            messages: [...currentConv.messages, message]
          },
          isLoading: false
        });
      }
      
      return message;
    } catch (error: any) {
      set({ error: error.message || 'Failed to send message', isLoading: false });
      throw error;
    }
  },

  // Send message with streaming
  sendMessageStream: async (conversationId: string, content: string) => {
    set({ isStreaming: true, error: null });
    
    try {
      // Add user message immediately
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
      
      const responseBody = await api.post<ReadableStream>(
        `/conversations/${conversationId}/messages/stream`,
        { content, role: 'user' },
        true
      );
      
      const reader = responseBody?.getReader();
      const decoder = new TextDecoder();
      
      let assistantMessageContent = "";
      const assistantMessageId = (Date.now() + 1).toString();
      
      // Add a placeholder for the assistant's message
      set(state => ({
        currentConversation: {
          ...state.currentConversation!,
          messages: [
            ...state.currentConversation!.messages,
            {
              id: assistantMessageId,
              role: 'assistant',
              content: '',
              conversation_id: conversationId,
              created_at: new Date().toISOString()
            }
          ]
        }
      }));

      if (reader) {
        const processStream = async () => {
          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              set({ isStreaming: false });
              break;
            }
            
            const rawData = decoder.decode(value, { stream: true });
            const chunks = rawData.split('data: ').filter(Boolean);

            for (const chunk of chunks) {
              if (chunk.trim() === '[DONE]') continue;
              
              try {
                const parsedChunk = JSON.parse(chunk);
                
                // Simulate typing effect by adding characters one by one with a small delay
                for (const char of parsedChunk) {
                  assistantMessageContent += char;

                  set(state => ({
                    currentConversation: {
                      ...state.currentConversation!,
                      messages: state.currentConversation!.messages.map(msg =>
                        msg.id === assistantMessageId
                          ? { ...msg, content: assistantMessageContent }
                          : msg
                      )
                    }
                  }));
                  
                  await new Promise(resolve => setTimeout(resolve, 5)); // 5ms delay between characters
                }

              } catch (e) {
                console.warn("Failed to parse stream chunk:", chunk);
              }
            }
          }
        };
        await processStream();
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
      const taskDefinition = await api.post<TaskDefinition>('/task-definitions', {
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
      
      return taskDefinition;
    } catch (error: any) {
      set({ error: error.message || 'Failed to create task definition', isLoading: false });
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
  }),

  setConversationCompleted: (conversationId: string) => {
    set(state => {
      if (state.currentConversation?.id === conversationId) {
        return { currentConversation: { ...state.currentConversation, is_completed: true } };
      }
      return {};
    });
  }
})); 