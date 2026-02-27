import { create } from 'zustand';

import type { ChatSessionSummary } from '@/lib/chatApi';

export type ChatConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';
export type ChatMessageStatus = 'sending' | 'sent' | 'delivered' | 'error';
export type ChatFeedbackType = 'thumbs_up' | 'thumbs_down' | null;

export interface ChatMessageState {
    id: string;
    sessionId: string;
    sender: 'user' | 'agent';
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
    status: ChatMessageStatus;
    metadata?: Record<string, unknown>;
    isStreaming?: boolean;
    sequenceNumber?: number;
    agentId?: string;
    agentName?: string;
    feedback?: ChatFeedbackType;
    errorMessage?: string | null;
}

interface ChatTypingState {
    isTyping: boolean;
    agentName: string | null;
}

interface ChatErrorState {
    code: string;
    message: string;
    recoverable: boolean;
}

interface ChatStore {
    sessions: ChatSessionSummary[];
    messagesBySession: Record<string, ChatMessageState[]>;
    currentSessionId: string | null;
    selectedAgentId: string | null;
    currentSessionAgentId: string | null;
    typing: ChatTypingState;
    connectionStatus: ChatConnectionStatus;
    isBootstrapping: boolean;
    isSessionLoading: boolean;
    reconnectAttempt: number;
    lastError: ChatErrorState | null;

    reset: () => void;
    setBootstrapping: (value: boolean) => void;
    setSessionLoading: (value: boolean) => void;
    setConnectionStatus: (status: ChatConnectionStatus) => void;
    setReconnectAttempt: (attempt: number) => void;
    setError: (error: ChatErrorState | null) => void;
    clearError: () => void;
    setTyping: (isTyping: boolean, agentName?: string | null) => void;
    setSessions: (sessions: ChatSessionSummary[]) => void;
    upsertSession: (session: ChatSessionSummary) => void;
    removeSession: (sessionId: string) => void;
    setCurrentSessionId: (sessionId: string | null) => void;
    setSelectedAgentId: (agentId: string | null) => void;
    setCurrentSessionAgentId: (agentId: string | null) => void;
    replaceMessages: (sessionId: string, messages: ChatMessageState[]) => void;
    addOptimisticUserMessage: (sessionId: string, message: ChatMessageState) => void;
    upsertMessage: (sessionId: string, message: ChatMessageState) => void;
    appendStreamChunk: (
        sessionId: string,
        messageId: string,
        chunk: string,
        agentId?: string,
        agentName?: string
    ) => void;
    finalizeStreamMessage: (sessionId: string, messageId: string) => void;
    markMessageStatus: (
        sessionId: string,
        messageId: string,
        status: ChatMessageStatus,
        errorMessage?: string | null
    ) => void;
    markLatestPendingUserMessage: (sessionId: string, status: ChatMessageStatus) => void;
    applyFeedback: (sessionId: string, messageId: string, feedback: ChatFeedbackType) => void;
}

const initialState = {
    sessions: [] as ChatSessionSummary[],
    messagesBySession: {} as Record<string, ChatMessageState[]>,
    currentSessionId: null as string | null,
    selectedAgentId: null as string | null,
    currentSessionAgentId: null as string | null,
    typing: {
        isTyping: false,
        agentName: null,
    },
    connectionStatus: 'disconnected' as ChatConnectionStatus,
    isBootstrapping: false,
    isSessionLoading: false,
    reconnectAttempt: 0,
    lastError: null as ChatErrorState | null,
};

const EMPTY_MESSAGES: ChatMessageState[] = [];

function sortSessions(sessions: ChatSessionSummary[]): ChatSessionSummary[] {
    return [...sessions].sort((left, right) => {
        const leftDate = Date.parse(left.last_message_at || left.updated_at || left.created_at);
        const rightDate = Date.parse(right.last_message_at || right.updated_at || right.created_at);
        return rightDate - leftDate;
    });
}

function upsertSessionList(
    sessions: ChatSessionSummary[],
    nextSession: ChatSessionSummary
): ChatSessionSummary[] {
    const remaining = sessions.filter((session) => session.id !== nextSession.id);
    return sortSessions([nextSession, ...remaining]);
}

function syncSessionPreview(
    sessions: ChatSessionSummary[],
    sessionId: string,
    messages: ChatMessageState[]
): ChatSessionSummary[] {
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage) {
        return sessions;
    }

    return sortSessions(
        sessions.map((session) => {
            if (session.id !== sessionId) {
                return session;
            }

            const timestamp = lastMessage.timestamp.toISOString();
            return {
                ...session,
                last_message: lastMessage.content,
                last_message_at: timestamp,
                updated_at: timestamp,
                message_count: Math.max(session.message_count, messages.length),
            };
        })
    );
}

export const useChatStore = create<ChatStore>((set) => ({
    ...initialState,

    reset: () => set(initialState),

    setBootstrapping: (value) => set({ isBootstrapping: value }),

    setSessionLoading: (value) => set({ isSessionLoading: value }),

    setConnectionStatus: (status) => set({ connectionStatus: status }),

    setReconnectAttempt: (attempt) => set({ reconnectAttempt: attempt }),

    setError: (error) => set({ lastError: error }),

    clearError: () => set({ lastError: null }),

    setTyping: (isTyping, agentName) =>
        set({
            typing: {
                isTyping,
                agentName: isTyping ? agentName || null : null,
            },
        }),

    setSessions: (sessions) =>
        set((state) => {
            const sortedSessions = sortSessions(sessions);
            return {
            sessions: sortedSessions,
            currentSessionId: state.currentSessionId && sessions.some((session) => session.id === state.currentSessionId)
                ? state.currentSessionId
                : sortedSessions[0]?.id || null,
        };
        }),

    upsertSession: (session) =>
        set((state) => ({
            sessions: upsertSessionList(state.sessions, session),
        })),

    removeSession: (sessionId) =>
        set((state) => {
            const nextSessions = state.sessions.filter((session) => session.id !== sessionId);
            const nextMessagesBySession = { ...state.messagesBySession };
            delete nextMessagesBySession[sessionId];

            const isCurrent = state.currentSessionId === sessionId;
            const nextCurrentSessionId = isCurrent ? (nextSessions[0]?.id || null) : state.currentSessionId;
            const nextCurrentSessionAgentId = isCurrent
                ? (nextSessions[0]?.selected_agent_id || null)
                : state.currentSessionAgentId;

            return {
                sessions: nextSessions,
                messagesBySession: nextMessagesBySession,
                currentSessionId: nextCurrentSessionId,
                currentSessionAgentId: nextCurrentSessionAgentId,
                selectedAgentId: isCurrent ? nextCurrentSessionAgentId : state.selectedAgentId,
            };
        }),

    setCurrentSessionId: (sessionId) => set({ currentSessionId: sessionId }),

    setSelectedAgentId: (agentId) => set({ selectedAgentId: agentId }),

    setCurrentSessionAgentId: (agentId) => set({ currentSessionAgentId: agentId }),

    replaceMessages: (sessionId, messages) =>
        set((state) => ({
            messagesBySession: {
                ...state.messagesBySession,
                [sessionId]: messages,
            },
            sessions: syncSessionPreview(state.sessions, sessionId, messages),
        })),

    addOptimisticUserMessage: (sessionId, message) =>
        set((state) => {
            const existing = state.messagesBySession[sessionId] || [];
            const nextMessages = [...existing, message];

            return {
                messagesBySession: {
                    ...state.messagesBySession,
                    [sessionId]: nextMessages,
                },
                sessions: syncSessionPreview(state.sessions, sessionId, nextMessages),
            };
        }),

    upsertMessage: (sessionId, message) =>
        set((state) => {
            const existing = state.messagesBySession[sessionId] || [];
            const index = existing.findIndex((candidate) => candidate.id === message.id);
            const nextMessages = [...existing];

            if (index === -1) {
                nextMessages.push(message);
            } else {
                nextMessages[index] = {
                    ...nextMessages[index],
                    ...message,
                };
            }

            return {
                messagesBySession: {
                    ...state.messagesBySession,
                    [sessionId]: nextMessages,
                },
                sessions: syncSessionPreview(state.sessions, sessionId, nextMessages),
            };
        }),

    appendStreamChunk: (sessionId, messageId, chunk, agentId, agentName) =>
        set((state) => {
            const existing = state.messagesBySession[sessionId] || [];
            const index = existing.findIndex((candidate) => candidate.id === messageId);
            const nextMessages = [...existing];

            if (index === -1) {
                nextMessages.push({
                    id: messageId,
                    sessionId,
                    sender: 'agent',
                    role: 'assistant',
                    content: chunk,
                    timestamp: new Date(),
                    status: 'sent',
                    isStreaming: true,
                    agentId,
                    agentName,
                });
            } else {
                nextMessages[index] = {
                    ...nextMessages[index],
                    content: nextMessages[index].content + chunk,
                    status: 'sent',
                    isStreaming: true,
                    agentId: agentId || nextMessages[index].agentId,
                    agentName: agentName || nextMessages[index].agentName,
                };
            }

            return {
                messagesBySession: {
                    ...state.messagesBySession,
                    [sessionId]: nextMessages,
                },
                sessions: syncSessionPreview(state.sessions, sessionId, nextMessages),
            };
        }),

    finalizeStreamMessage: (sessionId, messageId) =>
        set((state) => {
            const existing = state.messagesBySession[sessionId] || [];
            const nextMessages = existing.map((message) =>
                message.id === messageId
                    ? { ...message, status: 'delivered' as const, isStreaming: false }
                    : message
            );

            return {
                messagesBySession: {
                    ...state.messagesBySession,
                    [sessionId]: nextMessages,
                },
                sessions: syncSessionPreview(state.sessions, sessionId, nextMessages),
            };
        }),

    markMessageStatus: (sessionId, messageId, status, errorMessage) =>
        set((state) => ({
            messagesBySession: {
                ...state.messagesBySession,
                [sessionId]: (state.messagesBySession[sessionId] || []).map((message) =>
                    message.id === messageId
                        ? {
                            ...message,
                            status,
                            errorMessage: errorMessage ?? message.errorMessage ?? null,
                        }
                        : message
                ),
            },
        })),

    markLatestPendingUserMessage: (sessionId, status) =>
        set((state) => {
            const existing = state.messagesBySession[sessionId] || [];
            const nextMessages = [...existing];

            for (let index = nextMessages.length - 1; index >= 0; index -= 1) {
                const candidate = nextMessages[index];
                if (candidate.sender === 'user' && (candidate.status === 'sending' || candidate.status === 'sent')) {
                    nextMessages[index] = {
                        ...candidate,
                        status,
                    };
                    break;
                }
            }

            return {
                messagesBySession: {
                    ...state.messagesBySession,
                    [sessionId]: nextMessages,
                },
            };
        }),

    applyFeedback: (sessionId, messageId, feedback) =>
        set((state) => ({
            messagesBySession: {
                ...state.messagesBySession,
                [sessionId]: (state.messagesBySession[sessionId] || []).map((message) =>
                    message.id === messageId
                        ? {
                            ...message,
                            feedback,
                        }
                        : message
                ),
            },
        })),
}));

export function selectCurrentMessages(state: ChatStore): ChatMessageState[] {
    if (!state.currentSessionId) {
        return EMPTY_MESSAGES;
    }

    return state.messagesBySession[state.currentSessionId] || EMPTY_MESSAGES;
}
