import { create } from 'zustand';

export interface ChatMessage {
    id: string;
    sender: string;
    role: 'user' | 'agent' | 'system';
    content: string;
    timestamp: number;
}

interface ChatStore {
    messages: ChatMessage[];
    isTyping: boolean;
    typingAgent: string | null;

    // Actions
    addMessage: (msg: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
    setTyping: (isTyping: boolean, agentName?: string) => void;
    clearHistory: () => void;
    clearMessages: () => void;  // Alias for clearHistory
}

export const useChatStore = create<ChatStore>((set) => ({
    messages: [
        {
            id: 'init-1',
            sender: 'System',
            role: 'system',
            content: 'Neural Link established. DCIS active.',
            timestamp: Date.now()
        }
    ],
    isTyping: false,
    typingAgent: null,

    addMessage: (msg) => set((state) => ({
        messages: [...state.messages, {
            ...msg,
            id: Math.random().toString(36).substring(7),
            timestamp: Date.now()
        }]
    })),

    setTyping: (isTyping, agentName) => set({
        isTyping,
        typingAgent: agentName || null
    }),

    clearHistory: () => set({ messages: [] }),

    clearMessages: () => set({ messages: [] })  // Alias for compatibility
}));
