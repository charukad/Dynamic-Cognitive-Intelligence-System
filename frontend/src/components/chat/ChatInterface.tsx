'use client';

/**
 * Real-time Chat Interface
 *
 * The component delegates chat session, message, typing, and delivery state to
 * the canonical chat store so HTTP and WebSocket flows reconcile the same way.
 */

import React, { useEffect, useId, useRef, useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import {
    Send,
    Activity,
    AlertCircle,
    BarChart3,
    Bot,
    Briefcase,
    Building2,
    Check,
    CheckCheck,
    Clock,
    Database,
    GitBranch,
    LoaderCircle,
    RotateCcw,
    ShieldAlert,
    Sparkles,
    ThumbsUp,
    ThumbsDown,
    PlusCircle,
    Users,
    Workflow,
    X
} from 'lucide-react';

import ChatHistorySidebar from './ChatHistorySidebar';
import {
    ChatMessageRecord,
    ChatSessionSummary,
    ChatWorkspaceResponse,
    createChatSession,
    getChatWorkspace,
    getChatSession,
    listChatMessages,
    listChatSessions,
    sendChatMessage,
    upsertChatFeedback
} from '@/lib/chatApi';
import { apiPath, wsUrl } from '@/lib/runtime';
import {
    ChatFeedbackType,
    ChatMessageState,
    selectCurrentMessages,
    useChatStore
} from '@/store/chatStore';

import './ChatInterface.css';

interface Agent {
    id: string;
    name: string;
    specialty: string;
    status: 'online' | 'busy' | 'offline';
    avatar_color: string;
}

interface RawAgent {
    id: string;
    name: string;
    description: string;
}

interface WebSocketPayload {
    type?: string;
    id?: string;
    agent_id?: string;
    agent_name?: string;
    content?: string;
    timestamp?: string;
    message_id?: string;
    chunk?: string;
    is_typing?: boolean;
    metadata?: Record<string, unknown>;
    data?: {
        is_typing?: boolean;
        message?: string;
        retry_after_seconds?: number;
    };
}

type ChatExecutionMode = 'balanced' | 'high_accuracy' | 'budget';
type ChatDisplayMode = 'simple' | 'executive' | 'full_simulation';
type WorkspacePanelTab = 'employees' | 'activity' | 'stats' | 'dag' | 'replay';
type OfficeRoomId =
    | 'strategy'
    | 'boss'
    | 'voting'
    | 'collaboration'
    | 'memory'
    | 'incubator'
    | 'execution';

interface RoutingMetadata {
    source?: string;
    reason?: string;
    inferredTaskType?: string;
    inferredAgentType?: string;
    mode?: ChatExecutionMode;
    startProjectMode?: boolean;
}

interface OfficeRoom {
    id: OfficeRoomId;
    title: string;
    label: string;
    status: 'active' | 'watching' | 'idle' | 'alert';
    detail: string;
    metric: string;
    description: string;
}

interface ActivityFeedItem {
    id: string;
    type: string;
    description: string;
    timestamp: Date;
    severity: 'info' | 'success' | 'warning' | 'critical';
}

interface TaskStage {
    id: string;
    title: string;
    status: 'done' | 'active' | 'waiting' | 'alert';
    detail: string;
}

export function ChatInterface({ embedded = false }: { embedded?: boolean }) {
    const prefersReducedMotion = useReducedMotion();
    const [inputText, setInputText] = useState('');
    const [availableAgents, setAvailableAgents] = useState<Agent[]>([]);
    const [executionMode, setExecutionMode] = useState<ChatExecutionMode>('balanced');
    const [displayMode, setDisplayMode] = useState<ChatDisplayMode>('full_simulation');
    const [startProjectMode, setStartProjectMode] = useState(false);
    const [activeWorkspaceTab, setActiveWorkspaceTab] = useState<WorkspacePanelTab>('activity');
    const [activeRoomId, setActiveRoomId] = useState<OfficeRoomId>('strategy');
    const [graphOverlayEnabled, setGraphOverlayEnabled] = useState(false);
    const [workflowState, setWorkflowState] = useState<'idle' | 'dispatching' | 'coordinating' | 'returning'>('idle');
    const [workspaceSnapshot, setWorkspaceSnapshot] = useState<ChatWorkspaceResponse | null>(null);
    const composerInputId = useId();
    const composerHintId = useId();
    const composerStatusId = useId();
    const agentSelectId = useId();

    const messages = useChatStore(selectCurrentMessages);
    const currentSessionId = useChatStore((state) => state.currentSessionId);
    const selectedAgentId = useChatStore((state) => state.selectedAgentId);
    const currentSessionAgentId = useChatStore((state) => state.currentSessionAgentId);
    const typing = useChatStore((state) => state.typing);
    const connectionStatus = useChatStore((state) => state.connectionStatus);
    const isBootstrapping = useChatStore((state) => state.isBootstrapping);
    const isSessionLoading = useChatStore((state) => state.isSessionLoading);
    const reconnectAttempt = useChatStore((state) => state.reconnectAttempt);
    const lastError = useChatStore((state) => state.lastError);

    const setBootstrapping = useChatStore((state) => state.setBootstrapping);
    const setSessionLoading = useChatStore((state) => state.setSessionLoading);
    const setConnectionStatus = useChatStore((state) => state.setConnectionStatus);
    const setReconnectAttempt = useChatStore((state) => state.setReconnectAttempt);
    const setError = useChatStore((state) => state.setError);
    const clearError = useChatStore((state) => state.clearError);
    const setTyping = useChatStore((state) => state.setTyping);
    const setSessions = useChatStore((state) => state.setSessions);
    const upsertSession = useChatStore((state) => state.upsertSession);
    const setCurrentSessionId = useChatStore((state) => state.setCurrentSessionId);
    const setSelectedAgentId = useChatStore((state) => state.setSelectedAgentId);
    const setCurrentSessionAgentId = useChatStore((state) => state.setCurrentSessionAgentId);
    const replaceMessages = useChatStore((state) => state.replaceMessages);
    const addOptimisticUserMessage = useChatStore((state) => state.addOptimisticUserMessage);
    const upsertMessage = useChatStore((state) => state.upsertMessage);
    const appendStreamChunk = useChatStore((state) => state.appendStreamChunk);
    const finalizeStreamMessage = useChatStore((state) => state.finalizeStreamMessage);
    const markMessageStatus = useChatStore((state) => state.markMessageStatus);
    const markLatestPendingUserMessage = useChatStore((state) => state.markLatestPendingUserMessage);

    const wsRef = useRef<WebSocket | null>(null);
    const activeStreamSessionIdRef = useRef<string | null>(null);
    const reconnectTimerRef = useRef<number | null>(null);
    const workflowTimerRef = useRef<number | null>(null);
    const reconnectAttemptRef = useRef(0);
    const shutdownRef = useRef(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const selectedAgent =
        availableAgents.find((agent) => agent.id === selectedAgentId)
        || availableAgents.find((agent) => agent.id === currentSessionAgentId)
        || availableAgents[0]
        || null;

    async function syncSessionSummary(sessionId: string) {
        try {
            const session = await getChatSession(sessionId);
            upsertSession(session);
            setCurrentSessionAgentId(session.selected_agent_id || null);
            if (session.selected_agent_id) {
                setSelectedAgentId(session.selected_agent_id);
            }
            void refreshWorkspace(sessionId);
            clearError();
        } catch (error) {
            console.error('Failed to refresh session summary:', error);
        }
    }

    async function refreshWorkspace(sessionId: string) {
        try {
            const workspace = await getChatWorkspace(sessionId);
            setWorkspaceSnapshot(workspace);
        } catch (error) {
            console.error('Failed to refresh chat workspace:', error);
        }
    }

    async function startNewChat() {
        setSessionLoading(true);
        try {
            const session = await createChatSession(selectedAgent?.id || null);
            upsertSession(session);
            setCurrentSessionId(session.id);
            setCurrentSessionAgentId(session.selected_agent_id || selectedAgent?.id || null);
            setSelectedAgentId(session.selected_agent_id || selectedAgent?.id || null);
            replaceMessages(session.id, []);
            setTyping(false);
            void refreshWorkspace(session.id);
            clearError();
            return session;
        } catch (error) {
            setError({
                code: 'session_create_failed',
                message: 'Failed to start a new conversation.',
                recoverable: true,
            });
            throw error;
        } finally {
            setSessionLoading(false);
        }
    }

    async function openSession(sessionId: string, existingSession?: ChatSessionSummary) {
        setSessionLoading(true);
        try {
            const [session, storedMessages] = await Promise.all([
                existingSession ? Promise.resolve(existingSession) : getChatSession(sessionId),
                listChatMessages(sessionId),
            ]);

            upsertSession(session);
            setCurrentSessionId(session.id);
            setCurrentSessionAgentId(session.selected_agent_id || null);
            setSelectedAgentId(session.selected_agent_id || null);
            replaceMessages(session.id, storedMessages.map(mapApiMessageToUiMessage));
            setTyping(false);
            void refreshWorkspace(session.id);
            clearError();
        } catch (error) {
            console.error('Failed to load session:', error);
            setError({
                code: 'session_load_failed',
                message: 'Failed to load the selected conversation.',
                recoverable: true,
            });
        } finally {
            setSessionLoading(false);
        }
    }

    async function bootstrapChat() {
        setBootstrapping(true);
        try {
            const sessions = await listChatSessions();
            setSessions(sessions);

            if (sessions.length > 0) {
                await openSession(sessions[0].id, sessions[0]);
                return;
            }

            await startNewChat();
            clearError();
        } catch (error) {
            console.error('Failed to bootstrap chat:', error);
            setError({
                code: 'bootstrap_failed',
                message: 'Failed to load chat sessions.',
                recoverable: true,
            });
        } finally {
            setBootstrapping(false);
        }
    }

    async function fetchAgents() {
        try {
            const response = await fetch(apiPath('/v1/agents'));
            const data = await response.json();
            const agents: Agent[] = Array.isArray(data)
                ? (data as RawAgent[]).map((agent) => ({
                    id: agent.id,
                    name: agent.name,
                    specialty: agent.description,
                    status: 'online' as const,
                    avatar_color: getAgentColor(agent.id),
                }))
                : [];

            setAvailableAgents(agents);

            const state = useChatStore.getState();
            if (!state.selectedAgentId && !state.currentSessionAgentId && agents[0]) {
                state.setSelectedAgentId(agents[0].id);
            }
        } catch (error) {
            console.error('Failed to fetch agents:', error);
            setError({
                code: 'agents_load_failed',
                message: 'Failed to load available agents.',
                recoverable: true,
            });
        }
    }

    function clearReconnectTimer() {
        if (reconnectTimerRef.current !== null) {
            window.clearTimeout(reconnectTimerRef.current);
            reconnectTimerRef.current = null;
        }
    }

    function clearWorkflowTimer() {
        if (workflowTimerRef.current !== null) {
            window.clearTimeout(workflowTimerRef.current);
            workflowTimerRef.current = null;
        }
    }

    function transitionWorkflow(
        nextState: 'idle' | 'dispatching' | 'coordinating' | 'returning',
        resetAfterMs?: number
    ) {
        clearWorkflowTimer();
        setWorkflowState(nextState);

        if (resetAfterMs) {
            workflowTimerRef.current = window.setTimeout(() => {
                setWorkflowState('idle');
                workflowTimerRef.current = null;
            }, resetAfterMs);
        }
    }

    function scheduleReconnect() {
        if (shutdownRef.current) {
            return;
        }

        clearReconnectTimer();
        reconnectAttemptRef.current += 1;
        const attempt = reconnectAttemptRef.current;
        const delayMs = Math.min(1000 * (2 ** (attempt - 1)), 10000);

        setReconnectAttempt(attempt);
        setConnectionStatus('connecting');
        setError({
            code: 'websocket_reconnect',
            message: `Realtime connection lost. Reconnecting${attempt > 1 ? ` (attempt ${attempt})` : ''}...`,
            recoverable: true,
        });

        reconnectTimerRef.current = window.setTimeout(() => {
            void connectWebSocket();
        }, delayMs);
    }

    function initializeWebSocket(): WebSocket {
        setConnectionStatus('connecting');
        const websocket = new WebSocket(wsUrl('/ws/ai-services'));

        websocket.onopen = () => {
            clearReconnectTimer();
            reconnectAttemptRef.current = 0;
            setReconnectAttempt(0);
            setConnectionStatus('connected');
            clearError();
        };

        websocket.onclose = () => {
            wsRef.current = null;
            setConnectionStatus('disconnected');
            transitionWorkflow('idle');
            if (!shutdownRef.current) {
                scheduleReconnect();
            }
        };

        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            setConnectionStatus('error');
            transitionWorkflow('idle');
            setError({
                code: 'websocket_error',
                message: 'Realtime connection failed. Chat will fall back to standard responses while reconnecting.',
                recoverable: true,
            });
        };

        websocket.onmessage = (event) => {
            const payload = JSON.parse(event.data) as WebSocketPayload;
            const data = payload.data ?? {};
            const sessionId = activeStreamSessionIdRef.current || useChatStore.getState().currentSessionId;
            if (!sessionId) {
                return;
            }

            if (payload.type === 'message') {
                transitionWorkflow('coordinating');
                upsertMessage(sessionId, {
                    id: payload.id || createClientMessageId(),
                    sessionId,
                    sender: 'agent',
                    role: 'assistant',
                    agentId: payload.agent_id,
                    agentName: payload.agent_name,
                    content: payload.content || '',
                    timestamp: new Date(payload.timestamp || Date.now()),
                    status: 'sent',
                    metadata: payload.metadata,
                    isStreaming: true,
                });
                markLatestPendingUserMessage(sessionId, 'delivered');
                setTyping(false);
            } else if (payload.type === 'typing') {
                setTyping(Boolean(data.is_typing ?? payload.is_typing), selectedAgent?.name || null);
                if (data.is_typing ?? payload.is_typing) {
                    transitionWorkflow('coordinating');
                }
            } else if (payload.type === 'stream_chunk' && payload.message_id && payload.chunk) {
                transitionWorkflow('coordinating');
                appendStreamChunk(
                    sessionId,
                    payload.message_id,
                    payload.chunk,
                    payload.agent_id,
                    payload.agent_name
                );
            } else if (payload.type === 'message_completed' && payload.message_id) {
                finalizeStreamMessage(sessionId, payload.message_id);
                markLatestPendingUserMessage(sessionId, 'delivered');
                setTyping(false);
                activeStreamSessionIdRef.current = null;
                transitionWorkflow('returning', 1800);
                void syncSessionSummary(sessionId);
            } else if (payload.type === 'error') {
                console.error('WebSocket chat error:', data.message || 'Unknown WebSocket error');
                markLatestPendingUserMessage(sessionId, 'error');
                setTyping(false);
                activeStreamSessionIdRef.current = null;
                transitionWorkflow('idle');
                setError({
                    code: 'websocket_message_error',
                    message: data.message || 'Chat response failed.',
                    recoverable: true,
                });
            }
        };

        wsRef.current = websocket;
        return websocket;
    }

    async function connectWebSocket() {
        const existing = wsRef.current;
        if (existing && (existing.readyState === WebSocket.OPEN || existing.readyState === WebSocket.CONNECTING)) {
            return existing;
        }

        return initializeWebSocket();
    }

    function scrollToBottom() {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }

    function resizeComposer() {
        const composer = inputRef.current;
        if (!composer) {
            return;
        }

        composer.style.height = 'auto';
        composer.style.height = `${Math.min(composer.scrollHeight, 180)}px`;
    }

    useEffect(() => {
        shutdownRef.current = false;
        const websocket = initializeWebSocket();
        const startupHandle = window.setTimeout(() => {
            void fetchAgents();
            void bootstrapChat();
        }, 0);

        return () => {
            shutdownRef.current = true;
            window.clearTimeout(startupHandle);
            clearReconnectTimer();
            clearWorkflowTimer();
            activeStreamSessionIdRef.current = null;
            websocket.close();
        };
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        if (prefersReducedMotion) {
            setDisplayMode('simple');
        }
    }, [prefersReducedMotion]);

    useEffect(() => {
        scrollToBottom();
    }, [messages, typing.isTyping]);

    useEffect(() => {
        resizeComposer();
    }, [inputText, currentSessionId]);

    useEffect(() => {
        if (!isBootstrapping && !isSessionLoading) {
            inputRef.current?.focus();
        }
    }, [currentSessionId, isBootstrapping, isSessionLoading]);

    useEffect(() => {
        if (!currentSessionId) {
            setWorkspaceSnapshot(null);
        }
    }, [currentSessionId]);

    async function ensureActiveSession() {
        if (currentSessionId) {
            return currentSessionId;
        }

        const session = await startNewChat();
        return session.id;
    }

    async function sendMessage(messageOverride?: string) {
        const messageText = (messageOverride ?? inputText).trim();
        if (!messageText) {
            return;
        }

        const userMessageId = createClientMessageId();
        if (!messageOverride) {
            setInputText('');
        }

        try {
            const sessionId = await ensureActiveSession();
            const nextSelectedAgentId = selectedAgent?.id || null;
            const requestMetadata = {
                mode: executionMode,
                start_project_mode: startProjectMode,
                display_mode: displayMode,
            };

            if (nextSelectedAgentId) {
                setSelectedAgentId(nextSelectedAgentId);
                setCurrentSessionAgentId(nextSelectedAgentId);
            }

            clearError();
            transitionWorkflow('dispatching');
            addOptimisticUserMessage(sessionId, {
                id: userMessageId,
                sessionId,
                sender: 'user',
                role: 'user',
                content: messageText,
                timestamp: new Date(),
                status: 'sending',
                metadata: requestMetadata,
            });

            const websocket = wsRef.current;
            const websocketReady = Boolean(
                websocket && websocket.readyState === WebSocket.OPEN && nextSelectedAgentId
            );
            if (websocketReady && websocket) {
                activeStreamSessionIdRef.current = sessionId;
                setTyping(true, selectedAgent?.name || null);
                transitionWorkflow('coordinating');
                websocket.send(JSON.stringify({
                    type: 'chat',
                    data: {
                        agent_id: nextSelectedAgentId,
                        message: messageText,
                        message_id: userMessageId,
                        session_id: sessionId,
                        metadata: requestMetadata,
                    },
                }));
                markMessageStatus(sessionId, userMessageId, 'sent');
            } else {
                const result = await sendChatMessage(sessionId, {
                    id: userMessageId,
                    content: messageText,
                    agent_id: nextSelectedAgentId,
                    stream: false,
                    metadata: requestMetadata,
                });

                upsertSession(result.session);
                setCurrentSessionAgentId(result.session.selected_agent_id || nextSelectedAgentId);
                upsertMessage(sessionId, mapApiMessageToUiMessage(result.user_message));
                upsertMessage(sessionId, mapApiMessageToUiMessage(result.assistant_message));
                void refreshWorkspace(sessionId);
                clearError();
                transitionWorkflow('returning', 1800);
            }
        } catch (error) {
            console.error('Failed to send message:', error);
            const activeSessionId = useChatStore.getState().currentSessionId;
            if (activeSessionId) {
                markMessageStatus(activeSessionId, userMessageId, 'error', String(error));
            }
            setTyping(false);
            transitionWorkflow('idle');
            setError({
                code: 'message_send_failed',
                message: 'Failed to send message. You can retry it.',
                recoverable: false,
            });
        }

        if (!messageOverride) {
            inputRef.current?.focus();
        }
    }

    async function handleSessionSelect(sessionId: string) {
        await openSession(sessionId);
    }

    async function handleNewChat() {
        try {
            await startNewChat();
        } catch (error) {
            console.error('Error starting new chat:', error);
            alert('Failed to start new chat. Please try again.');
        }
    }

    function handleComposerKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
        if (event.nativeEvent.isComposing) {
            return;
        }

        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            void sendMessage();
        }
    }

    function handleRecoverError() {
        if (!lastError?.recoverable) {
            return;
        }

        if (lastError.code.startsWith('websocket')) {
            clearError();
            reconnectAttemptRef.current = 0;
            setReconnectAttempt(0);
            clearReconnectTimer();
            void connectWebSocket();
            return;
        }

        if (lastError.code === 'bootstrap_failed' || lastError.code === 'agents_load_failed') {
            clearError();
            void fetchAgents();
            void bootstrapChat();
            return;
        }

        if (lastError.code === 'session_load_failed' && currentSessionId) {
            clearError();
            void openSession(currentSessionId);
            return;
        }

        if (lastError.code === 'session_load_failed') {
            clearError();
            void bootstrapChat();
            return;
        }

        if (lastError.code === 'session_create_failed') {
            clearError();
            void startNewChat();
        }
    }

    function getComposerStatusMessage() {
        if (isBootstrapping) {
            return 'Loading the conversation workspace.';
        }

        if (isSessionLoading) {
            return 'Loading the selected conversation.';
        }

        if (typing.isTyping) {
            return `${typing.agentName || selectedAgent?.name || 'Agent'} is typing.`;
        }

        if (connectionStatus !== 'connected') {
            return reconnectAttempt > 0
                ? `Realtime connection reconnecting. Attempt ${reconnectAttempt}.`
                : 'Realtime connection unavailable. Messages will use standard delivery.';
        }

        if (lastError) {
            return lastError.message;
        }

        return selectedAgent
            ? `Ready to message ${selectedAgent.name}. Press Enter to send and Shift plus Enter for a new line.`
            : 'Select an agent to begin chatting.';
    }

    const latestUserMessage = findLatestMessage(messages, 'user');
    const latestAssistantMessage = findLatestMessage(messages, 'agent');
    const fallbackRouting = extractRoutingMetadata(latestAssistantMessage?.metadata)
        || extractRoutingMetadata(latestUserMessage?.metadata);
    const latestRouting = workspaceSnapshot?.route
        ? mapWorkspaceRoute(workspaceSnapshot.route)
        : fallbackRouting;
    const localActivityFeed = buildActivityFeed({
        messages,
        selectedAgent,
        latestRouting,
        connectionStatus,
        reconnectAttempt,
        lastError,
        typing,
        workflowState,
    });
    const fallbackOfficeRooms = buildOfficeRooms({
        selectedAgent,
        latestRouting,
        latestUserMessage,
        latestAssistantMessage,
        connectionStatus,
        typing,
        workflowState,
        lastError,
        startProjectMode,
    });
    const officeRooms = workspaceSnapshot?.rooms.length
        ? workspaceSnapshot.rooms.map(mapWorkspaceRoom)
        : fallbackOfficeRooms;
    const activityFeed = workspaceSnapshot?.activity_feed.length
        ? mergeWorkspaceActivityFeed(
            workspaceSnapshot.activity_feed.map(mapWorkspaceActivityItem),
            localActivityFeed,
        )
        : localActivityFeed;
    const activeRoom = officeRooms.find((room) => room.id === activeRoomId) ?? fallbackOfficeRooms[0]!;
    const activeAgentCount = availableAgents.filter((agent) => agent.status !== 'offline').length;
    const resolvedDisplayMode = prefersReducedMotion ? 'simple' : displayMode;
    const feedbackMessages = messages.filter((message) => message.sender === 'agent' && message.feedback);
    const thumbsUpCount = feedbackMessages.filter((message) => message.feedback === 'thumbs_up').length;
    const failureCount = messages.filter((message) => message.status === 'error').length;
    const localOfficeStats = [
        {
            label: 'Active Employees',
            value: `${activeAgentCount}/${availableAgents.length || 0}`,
            hint: availableAgents.length ? 'Connected roster' : 'Awaiting roster',
        },
        {
            label: 'Requests',
            value: `${messages.filter((message) => message.sender === 'user').length}`,
            hint: 'User turns in this session',
        },
        {
            label: 'Retries',
            value: `${failureCount + reconnectAttempt}`,
            hint: 'Transport and message recovery',
        },
        {
            label: 'Feedback Score',
            value: feedbackMessages.length ? `${Math.round((thumbsUpCount / feedbackMessages.length) * 100)}%` : 'No data',
            hint: 'Positive response ratio',
        },
        {
            label: 'Execution Mode',
            value: formatExecutionMode(executionMode),
            hint: startProjectMode ? 'Project mode enabled' : 'Direct response path',
        },
        {
            label: 'Route Source',
            value: latestRouting?.source ? formatRouteSource(latestRouting.source) : 'Awaiting first route',
            hint: latestRouting?.inferredTaskType ? `Task: ${latestRouting.inferredTaskType}` : 'No routed task yet',
        },
    ];
    const officeStats = workspaceSnapshot?.office_stats.length
        ? mergeOfficeStats(localOfficeStats, workspaceSnapshot.office_stats.map(mapWorkspaceStat))
        : localOfficeStats;
    const fallbackTaskStages = buildTaskStages({
        workflowState,
        latestRouting,
        latestAssistantMessage,
        typing,
        lastError,
        startProjectMode,
        selectedAgent,
    });
    const taskStages = workspaceSnapshot?.task_stages.length
        ? workspaceSnapshot.task_stages.map(mapWorkspaceTaskStage)
        : fallbackTaskStages;
    const replayItems = workspaceSnapshot?.replay.length
        ? workspaceSnapshot.replay.map(mapWorkspaceReplayItem)
        : activityFeed.map((item) => ({
            id: item.id,
            type: item.type,
            description: item.description,
            timestamp: item.timestamp,
        }));

    return (
        <>
            {!embedded && (
                <ChatHistorySidebar
                    onSessionSelect={handleSessionSelect}
                    onNewChat={() => {
                        void handleNewChat();
                    }}
                />
            )}
            <div className={`chat-interface dcis-chat ${embedded ? 'embedded' : ''}`}>
                <div className="chat-shell">
                    <section className="front-desk-panel">
                        <div className="front-desk-header">
                            <div className="front-desk-title">
                                <span className="front-desk-eyebrow">Front Desk</span>
                                <h1>Living AI Organization Interface</h1>
                                <p>
                                    Submit work, observe orchestration, and track exactly how the office routes it.
                                </p>
                            </div>
                            <button
                                type="button"
                                onClick={() => {
                                    void handleNewChat();
                                }}
                                className="new-chat-btn"
                                title="Start New Chat"
                            >
                                <PlusCircle size={20} />
                                <span>New Chat</span>
                            </button>
                        </div>

                        <div className="front-desk-toolbar">
                            <div className="front-desk-control-group">
                                <label htmlFor={agentSelectId} className="chat-visually-hidden">
                                    Active agent
                                </label>
                                <div className="agent-selector">
                                    <Bot className="bot-icon" size={20} />
                                    <select
                                        id={agentSelectId}
                                        value={selectedAgent?.id || ''}
                                        onChange={(event) => {
                                            const nextAgentId = event.target.value || null;
                                            setSelectedAgentId(nextAgentId);
                                            setCurrentSessionAgentId(nextAgentId);
                                        }}
                                        className="agent-dropdown"
                                        aria-label="Select active agent"
                                    >
                                        <option value="">Select Agent...</option>
                                        {availableAgents.map((agent) => (
                                            <option key={agent.id} value={agent.id}>
                                                {agent.name} - {agent.specialty}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                {selectedAgent && (
                                    <div className="front-desk-context-chip">
                                        <span className={`chat-status-dot ${selectedAgent.status}`} />
                                        <span>{selectedAgent.name}</span>
                                    </div>
                                )}
                            </div>

                            <div className="front-desk-mode-stack">
                                <div className="mode-segment" role="tablist" aria-label="Execution mode">
                                    {([
                                        ['balanced', 'Balanced'],
                                        ['high_accuracy', 'High Accuracy'],
                                        ['budget', 'Budget Mode'],
                                    ] as Array<[ChatExecutionMode, string]>).map(([modeId, label]) => (
                                        <button
                                            key={modeId}
                                            type="button"
                                            role="tab"
                                            aria-selected={executionMode === modeId}
                                            className={`mode-chip ${executionMode === modeId ? 'active' : ''}`}
                                            onClick={() => setExecutionMode(modeId)}
                                        >
                                            {label}
                                        </button>
                                    ))}
                                </div>
                                <button
                                    type="button"
                                    className={`project-mode-toggle ${startProjectMode ? 'active' : ''}`}
                                    aria-pressed={startProjectMode}
                                    onClick={() => setStartProjectMode((current) => !current)}
                                >
                                    <Workflow size={14} />
                                    Start Project Mode
                                </button>
                            </div>
                        </div>

                        <div className="front-desk-signal-row">
                            <div className="front-desk-signal-card">
                                <span className="signal-label">Current Context</span>
                                <strong>{selectedAgent ? `${selectedAgent.name} leading intake` : 'Orchestrator awaiting agent selection'}</strong>
                                <span>{latestRouting?.reason || 'Messages will route through the live office workflow.'}</span>
                            </div>
                            <div className="front-desk-signal-card">
                                <span className="signal-label">Session State</span>
                                <strong>{currentSessionId ? 'Live conversation active' : 'Preparing new conversation'}</strong>
                                <span>{getComposerStatusMessage()}</span>
                            </div>
                        </div>

                        {connectionStatus !== 'connected' && (
                            <div
                                className="chat-banner chat-banner-warning"
                                role="status"
                                aria-live="polite"
                            >
                                <div className="chat-banner-copy">
                                    <AlertCircle size={16} />
                                    <span>
                                        {connectionStatus === 'connecting'
                                            ? `Realtime reconnecting${reconnectAttempt > 0 ? ` (attempt ${reconnectAttempt})` : ''}. Messages still send over HTTP.`
                                            : 'Realtime connection unavailable. Messages still send over HTTP.'}
                                    </span>
                                </div>
                                <button
                                    type="button"
                                    className="chat-banner-action"
                                    onClick={() => {
                                        reconnectAttemptRef.current = 0;
                                        setReconnectAttempt(0);
                                        clearReconnectTimer();
                                        void connectWebSocket();
                                    }}
                                >
                                    Reconnect
                                </button>
                            </div>
                        )}

                        {lastError && !lastError.code.startsWith('websocket') && (
                            <div
                                className={`chat-banner ${lastError.recoverable ? 'chat-banner-warning' : 'chat-banner-error'}`}
                                role="alert"
                            >
                                <div className="chat-banner-copy">
                                    <AlertCircle size={16} />
                                    <span>{lastError.message}</span>
                                </div>
                                <div className="chat-banner-actions">
                                    {lastError.recoverable && (
                                        <button
                                            type="button"
                                            className="chat-banner-action"
                                            onClick={handleRecoverError}
                                        >
                                            Retry
                                        </button>
                                    )}
                                    <button
                                        type="button"
                                        className="chat-banner-dismiss"
                                        onClick={clearError}
                                        aria-label="Dismiss chat error"
                                    >
                                        <X size={14} />
                                    </button>
                                </div>
                            </div>
                        )}

                        <div
                            className="messages-container"
                            role="log"
                            aria-live="polite"
                            aria-relevant="additions text"
                            aria-busy={isBootstrapping || isSessionLoading}
                            aria-describedby={composerHintId}
                            tabIndex={0}
                        >
                            {(isBootstrapping || isSessionLoading) && (
                                <div className="chat-loading-state" role="status" aria-live="polite">
                                    <LoaderCircle size={24} className="chat-loading-icon" />
                                    <p className="chat-loading-text">
                                        {isBootstrapping ? 'Loading conversation workspace...' : 'Loading conversation...'}
                                    </p>
                                </div>
                            )}
                            {!isBootstrapping && !isSessionLoading && messages.length === 0 && !typing.isTyping && (
                                <div className="chat-empty-state">
                                    <Sparkles size={32} className="chat-empty-icon" />
                                    <p className="chat-empty-text">
                                        {selectedAgent
                                            ? `Start a conversation with ${selectedAgent.name}`
                                            : 'Select an agent above to begin chatting'}
                                    </p>
                                </div>
                            )}
                            <AnimatePresence initial={false}>
                                {messages.map((message) => (
                                    <MessageBubble
                                        key={message.id}
                                        message={message}
                                        sessionId={currentSessionId}
                                        onRetry={(content) => {
                                            void sendMessage(content);
                                        }}
                                    />
                                ))}
                            </AnimatePresence>

                            {typing.isTyping && <TypingIndicator agentName={typing.agentName || selectedAgent?.name} />}

                            <div ref={messagesEndRef} />
                        </div>

                        <form
                            className="input-container"
                            onSubmit={(event) => {
                                event.preventDefault();
                                void sendMessage();
                            }}
                        >
                            <label htmlFor={composerInputId} className="chat-visually-hidden">
                                Message composer
                            </label>
                            <textarea
                                id={composerInputId}
                                ref={inputRef}
                                value={inputText}
                                onChange={(event) => setInputText(event.target.value)}
                                onKeyDown={handleComposerKeyDown}
                                disabled={isBootstrapping || isSessionLoading}
                                placeholder={
                                    selectedAgent
                                        ? `Message ${selectedAgent.name}...`
                                        : 'Select an agent above to start chatting...'
                                }
                                className="message-input"
                                rows={1}
                                aria-describedby={`${composerHintId} ${composerStatusId}`}
                                aria-label="Message composer"
                            />

                            <motion.button
                                type="submit"
                                disabled={!inputText.trim() || isBootstrapping || isSessionLoading}
                                className="send-button"
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                aria-label={selectedAgent ? `Send message to ${selectedAgent.name}` : 'Send message'}
                            >
                                <Send size={20} />
                                <span className="chat-visually-hidden">Send message</span>
                            </motion.button>
                            <div className="chat-composer-meta">
                                <p id={composerHintId} className="chat-composer-hint">
                                    Enter to send. Shift + Enter for a new line.
                                </p>
                                <div className="chat-composer-chip-row">
                                    <span className="chat-composer-chip">{formatExecutionMode(executionMode)}</span>
                                    <span className="chat-composer-chip">{startProjectMode ? 'Project flow' : 'Direct response'}</span>
                                    <span className="chat-composer-chip">{formatDisplayMode(resolvedDisplayMode)}</span>
                                </div>
                                <div id={composerStatusId} className="chat-visually-hidden" aria-live="polite">
                                    {getComposerStatusMessage()}
                                </div>
                            </div>
                        </form>
                    </section>

                    <section className="workspace-column">
                        <div className="workspace-topbar">
                            <div className="workspace-title-block">
                                <span className="workspace-eyebrow">Interactive Office Workspace</span>
                                <h2>Operational floor in view</h2>
                                <p>
                                    Strategy, collaboration, memory recall, and delivery stay visible while the response is produced.
                                </p>
                            </div>
                            <div className="workspace-controls">
                                <div className="display-mode-switch" role="tablist" aria-label="Workspace display mode">
                                    {([
                                        ['simple', 'Simple'],
                                        ['executive', 'Executive'],
                                        ['full_simulation', 'Full Simulation'],
                                    ] as Array<[ChatDisplayMode, string]>).map(([modeId, label]) => (
                                        <button
                                            key={modeId}
                                            type="button"
                                            role="tab"
                                            aria-selected={resolvedDisplayMode === modeId}
                                            className={`display-mode-chip ${resolvedDisplayMode === modeId ? 'active' : ''}`}
                                            onClick={() => {
                                                if (prefersReducedMotion && modeId !== 'simple') {
                                                    return;
                                                }
                                                setDisplayMode(modeId);
                                            }}
                                            disabled={Boolean(prefersReducedMotion && modeId !== 'simple')}
                                        >
                                            {label}
                                        </button>
                                    ))}
                                </div>
                                <button
                                    type="button"
                                    className={`overlay-toggle ${graphOverlayEnabled ? 'active' : ''}`}
                                    aria-pressed={graphOverlayEnabled}
                                    onClick={() => setGraphOverlayEnabled((current) => !current)}
                                >
                                    <GitBranch size={14} />
                                    Live Office Graph
                                </button>
                            </div>
                        </div>

                        <OfficeWorkspace
                            rooms={officeRooms}
                            activeRoom={activeRoom}
                            activeRoomId={activeRoomId}
                            onRoomSelect={setActiveRoomId}
                            workflowState={workflowState}
                            graphOverlayEnabled={graphOverlayEnabled}
                            displayMode={resolvedDisplayMode}
                            selectedAgent={selectedAgent}
                            latestRouting={latestRouting}
                            latestAssistantMessage={latestAssistantMessage}
                            lastErrorMessage={lastError?.message || null}
                            typingAgentName={typing.agentName}
                        />

                        <AnalyticsPanel
                            activeTab={activeWorkspaceTab}
                            onTabChange={setActiveWorkspaceTab}
                            availableAgents={availableAgents}
                            selectedAgentId={selectedAgent?.id || null}
                            selectedAgentName={selectedAgent?.name || null}
                            typing={typing}
                            activityFeed={activityFeed}
                            officeStats={officeStats}
                            taskStages={taskStages}
                            replayItems={replayItems}
                            latestAssistantMessage={latestAssistantMessage}
                        />
                    </section>
                </div>
            </div>
        </>
    );
}

interface OfficeWorkspaceProps {
    rooms: OfficeRoom[];
    activeRoom: OfficeRoom;
    activeRoomId: OfficeRoomId;
    onRoomSelect: (roomId: OfficeRoomId) => void;
    workflowState: 'idle' | 'dispatching' | 'coordinating' | 'returning';
    graphOverlayEnabled: boolean;
    displayMode: ChatDisplayMode;
    selectedAgent: Agent | null;
    latestRouting: RoutingMetadata | null;
    latestAssistantMessage: ChatMessageState | undefined;
    lastErrorMessage: string | null;
    typingAgentName: string | null;
}

function OfficeWorkspace({
    rooms,
    activeRoom,
    activeRoomId,
    onRoomSelect,
    workflowState,
    graphOverlayEnabled,
    displayMode,
    selectedAgent,
    latestRouting,
    latestAssistantMessage,
    lastErrorMessage,
    typingAgentName,
}: OfficeWorkspaceProps) {
    return (
        <div className={`office-workspace display-${displayMode}`}>
            <div className={`workflow-rail workflow-${workflowState}`}>
                <span className="workflow-rail-label">Front Desk</span>
                <div className="workflow-rail-track">
                    <span className="workflow-rail-pulse" />
                </div>
                <span className="workflow-rail-label">Strategy Center</span>
                <div className="workflow-rail-track">
                    <span className="workflow-rail-pulse" />
                </div>
                <span className="workflow-rail-label">Delivery</span>
            </div>

            <div className="office-stage">
                <div className="office-stage-grid">
                    {rooms.map((room) => (
                        <button
                            key={room.id}
                            type="button"
                            className={`office-room-card status-${room.status} ${room.id === activeRoomId ? 'active' : ''}`}
                            onClick={() => onRoomSelect(room.id)}
                            aria-pressed={room.id === activeRoomId}
                        >
                            <div className="office-room-header">
                                <div className="office-room-icon">{getRoomIcon(room.id)}</div>
                                <div>
                                    <span className="office-room-label">{room.label}</span>
                                    <h3>{room.title}</h3>
                                </div>
                            </div>
                            <p>{room.detail}</p>
                            <div className="office-room-footer">
                                <span className="office-room-metric">{room.metric}</span>
                                <span className={`office-room-status status-${room.status}`}>{room.status}</span>
                            </div>
                        </button>
                    ))}
                </div>

                {graphOverlayEnabled && (
                    <div className="office-graph-overlay" aria-hidden="true">
                        {rooms.map((room, index) => (
                            <div
                                key={room.id}
                                className={`graph-node status-${room.status}`}
                                style={{
                                    left: `${14 + (index % 3) * 30}%`,
                                    top: `${16 + Math.floor(index / 3) * 28}%`,
                                }}
                            >
                                <span>{room.title}</span>
                            </div>
                        ))}
                        <div className="graph-link graph-link-a" />
                        <div className="graph-link graph-link-b" />
                        <div className="graph-link graph-link-c" />
                    </div>
                )}

                <div className="office-detail-panel">
                    <div className="office-detail-heading">
                        <span className="office-detail-kicker">Room Focus</span>
                        <h3>{activeRoom.title}</h3>
                        <p>{activeRoom.description}</p>
                    </div>
                    <div className="office-detail-grid">
                        <div className="office-detail-card">
                            <span className="office-detail-label">Current Motion</span>
                            <strong>{formatWorkflowState(workflowState)}</strong>
                            <p>
                                {workflowState === 'dispatching'
                                    ? 'Request packet is moving from the front desk to planning.'
                                    : workflowState === 'coordinating'
                                        ? 'Specialists are actively working the current turn.'
                                        : workflowState === 'returning'
                                            ? 'Validated response is returning to the front desk.'
                                            : 'The office is ready for the next assignment.'}
                            </p>
                        </div>
                        <div className="office-detail-card">
                            <span className="office-detail-label">Assigned Lead</span>
                            <strong>{latestAssistantMessage?.agentName || selectedAgent?.name || 'Executive Orchestrator'}</strong>
                            <p>{typingAgentName ? `${typingAgentName} is currently typing.` : latestRouting?.reason || 'No active specialist response yet.'}</p>
                        </div>
                        <div className="office-detail-card">
                            <span className="office-detail-label">Routing Context</span>
                            <strong>{latestRouting?.inferredTaskType || 'general'}</strong>
                            <p>{latestRouting?.source ? `${formatRouteSource(latestRouting.source)} path` : 'Route will resolve on the next message.'}</p>
                        </div>
                        <div className="office-detail-card">
                            <span className="office-detail-label">Escalation Monitor</span>
                            <strong>{lastErrorMessage ? 'Attention required' : 'Nominal'}</strong>
                            <p>{lastErrorMessage || 'Boss office remains on standby until a retry or failure occurs.'}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

interface AnalyticsPanelProps {
    activeTab: WorkspacePanelTab;
    onTabChange: (tab: WorkspacePanelTab) => void;
    availableAgents: Agent[];
    selectedAgentId: string | null;
    selectedAgentName: string | null;
    typing: { isTyping: boolean; agentName: string | null };
    activityFeed: ActivityFeedItem[];
    officeStats: Array<{ label: string; value: string; hint: string }>;
    taskStages: TaskStage[];
    replayItems: Array<{ id: string; type: string; description: string; timestamp: Date }>;
    latestAssistantMessage: ChatMessageState | undefined;
}

function AnalyticsPanel({
    activeTab,
    onTabChange,
    availableAgents,
    selectedAgentId,
    selectedAgentName,
    typing,
    activityFeed,
    officeStats,
    taskStages,
    replayItems,
    latestAssistantMessage,
}: AnalyticsPanelProps) {
    const tabs: Array<{ id: WorkspacePanelTab; label: string; icon: React.ReactNode }> = [
        { id: 'employees', label: 'Active Employees', icon: <Users size={14} /> },
        { id: 'activity', label: 'Activity Feed', icon: <Activity size={14} /> },
        { id: 'stats', label: 'Office Stats', icon: <BarChart3 size={14} /> },
        { id: 'dag', label: 'Task DAG Viewer', icon: <GitBranch size={14} /> },
        { id: 'replay', label: 'Replay', icon: <Workflow size={14} /> },
    ];

    return (
        <div className="analytics-panel">
            <div className="analytics-tabs" role="tablist" aria-label="Workspace analytics tabs">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        type="button"
                        role="tab"
                        aria-selected={activeTab === tab.id}
                        className={`analytics-tab ${activeTab === tab.id ? 'active' : ''}`}
                        onClick={() => onTabChange(tab.id)}
                    >
                        {tab.icon}
                        <span>{tab.label}</span>
                    </button>
                ))}
            </div>

            <div className="analytics-content">
                {activeTab === 'employees' && (
                    <div className="analytics-grid analytics-grid-employees">
                        {availableAgents.length === 0 ? (
                            <div className="analytics-empty">No active roster has been loaded yet.</div>
                        ) : (
                            availableAgents.map((agent) => {
                                const isSelected = agent.id === selectedAgentId;
                                const status = typing.isTyping && (typing.agentName === agent.name || isSelected)
                                    ? 'Working'
                                    : isSelected
                                        ? 'Assigned'
                                        : 'Available';
                                return (
                                    <div key={agent.id} className={`employee-card ${isSelected ? 'selected' : ''}`}>
                                        <div className="employee-card-top">
                                            <span
                                                className="employee-avatar"
                                                style={{ background: getAgentColor(agent.id) }}
                                            >
                                                {agent.name.slice(0, 1).toUpperCase()}
                                            </span>
                                            <div>
                                                <strong>{agent.name}</strong>
                                                <p>{agent.specialty}</p>
                                            </div>
                                        </div>
                                        <div className="employee-metrics">
                                            <span>{status}</span>
                                            <span>{isSelected ? 'Current assignment' : 'Standby'}</span>
                                            <span>{typing.isTyping && isSelected ? 'Streaming response' : 'Ready'}</span>
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>
                )}

                {activeTab === 'activity' && (
                    <div className="activity-feed">
                        {activityFeed.map((item) => (
                            <div key={item.id} className={`activity-feed-item severity-${item.severity}`}>
                                <div className="activity-feed-header">
                                    <strong>{item.type}</strong>
                                    <span>{formatRelativeTime(item.timestamp)}</span>
                                </div>
                                <p>{item.description}</p>
                            </div>
                        ))}
                    </div>
                )}

                {activeTab === 'stats' && (
                    <div className="analytics-grid analytics-grid-stats">
                        {officeStats.map((stat) => (
                            <div key={stat.label} className="stat-card">
                                <span>{stat.label}</span>
                                <strong>{stat.value}</strong>
                                <p>{stat.hint}</p>
                            </div>
                        ))}
                    </div>
                )}

                {activeTab === 'dag' && (
                    <div className="task-dag">
                        {taskStages.map((stage) => (
                            <div key={stage.id} className={`task-stage status-${stage.status}`}>
                                <div className="task-stage-dot" />
                                <div>
                                    <strong>{stage.title}</strong>
                                    <p>{stage.detail}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {activeTab === 'replay' && (
                    <div className="replay-panel">
                        <div className="replay-card">
                            <span className="office-detail-label">Latest Delivery</span>
                            <strong>{latestAssistantMessage?.agentName || selectedAgentName || 'Waiting for first response'}</strong>
                            <p>{latestAssistantMessage?.content || 'Replay becomes available after the first completed assistant response.'}</p>
                        </div>
                        <div className="activity-feed">
                            {replayItems.map((item) => (
                                <div key={`${item.id}-replay`} className="activity-feed-item severity-info">
                                    <div className="activity-feed-header">
                                        <strong>{item.type}</strong>
                                        <span>{formatRelativeTime(item.timestamp)}</span>
                                    </div>
                                    <p>{item.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

interface MessageBubbleProps {
    message: ChatMessageState;
    sessionId: string | null;
    onRetry: (content: string) => void;
}

function MessageBubble({ message, sessionId, onRetry }: MessageBubbleProps) {
    const isUser = message.sender === 'user';
    const applyFeedback = useChatStore((state) => state.applyFeedback);

    async function handleFeedback(type: Exclude<ChatFeedbackType, null>) {
        if (!sessionId || message.feedback === type) {
            return;
        }

        const previousFeedback = message.feedback || null;
        applyFeedback(sessionId, message.id, type);

        try {
            await upsertChatFeedback({
                session_id: sessionId,
                message_id: message.id,
                agent_id: message.agentId || undefined,
                feedback_type: type,
                rating: type === 'thumbs_up' ? 5 : 1,
            });
        } catch (error) {
            console.error('Failed to submit feedback:', error);
            applyFeedback(sessionId, message.id, previousFeedback);
        }
    }

    return (
        <motion.div
            className={`message-wrapper ${isUser ? 'user' : 'agent'}`}
            data-role={isUser ? 'USER' : 'DCID'}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
        >
            {!isUser && (
                <div
                    className="message-avatar"
                    style={{
                        background: `linear-gradient(135deg, ${message.agentName ? getAgentColor(message.agentId || '') : '#667eea'} 0%, #764ba2 100%)`,
                    }}
                >
                    <Bot size={20} />
                </div>
            )}

            <div className={`message-bubble ${isUser ? 'user' : 'agent'}`}>
                {!isUser && message.agentName && (
                    <div className="agent-name">{message.agentName}</div>
                )}

                <div className="message-content">
                    {isUser ? (
                        <p>{message.content}</p>
                    ) : (
                        <ReactMarkdown
                            components={{
                                code({ inline, className, children, ...rest }: React.ComponentPropsWithoutRef<'code'> & { inline?: boolean }) {
                                    const match = /language-(\w+)/.exec(className || '');
                                    return !inline && match ? (
                                        <SyntaxHighlighter
                                            style={vscDarkPlus}
                                            language={match[1]}
                                            PreTag="div"
                                            {...rest}
                                        >
                                            {String(children).replace(/\n$/, '')}
                                        </SyntaxHighlighter>
                                    ) : (
                                        <code className={className} {...rest}>
                                            {children}
                                        </code>
                                    );
                                },
                            }}
                        >
                            {message.content}
                        </ReactMarkdown>
                    )}
                </div>

                <div className="message-meta">
                    <span className="timestamp">
                        {message.timestamp.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                        })}
                    </span>

                    {isUser && (
                        <span className="status-icon">
                            {message.status === 'sending' && <Clock size={14} />}
                            {message.status === 'sent' && <Check size={14} />}
                            {message.status === 'delivered' && <CheckCheck size={14} />}
                        </span>
                    )}
                </div>

                {isUser && message.status === 'error' && (
                    <div className="message-error-row">
                        <span className="message-error-text">
                            {message.errorMessage || 'Message failed to send.'}
                        </span>
                        <button
                            type="button"
                            className="message-retry-button"
                            onClick={() => onRetry(message.content)}
                            aria-label="Retry failed message"
                        >
                            <RotateCcw size={12} />
                            Retry
                        </button>
                    </div>
                )}

                {!isUser && (
                    <div className="message-feedback">
                        <motion.button
                            onClick={() => {
                                void handleFeedback('thumbs_up');
                            }}
                            className={`feedback-btn ${message.feedback === 'thumbs_up' ? 'active' : ''}`}
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            title="Helpful"
                            aria-label="Mark assistant response as helpful"
                            aria-pressed={message.feedback === 'thumbs_up'}
                        >
                            <ThumbsUp size={14} />
                        </motion.button>
                        <motion.button
                            onClick={() => {
                                void handleFeedback('thumbs_down');
                            }}
                            className={`feedback-btn ${message.feedback === 'thumbs_down' ? 'active' : ''}`}
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            title="Not helpful"
                            aria-label="Mark assistant response as not helpful"
                            aria-pressed={message.feedback === 'thumbs_down'}
                        >
                            <ThumbsDown size={14} />
                        </motion.button>
                    </div>
                )}
            </div>
        </motion.div>
    );
}

function TypingIndicator({ agentName }: { agentName?: string | null }) {
    return (
        <motion.div
            className="typing-indicator"
            role="status"
            aria-live="polite"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
        >
            <div className="typing-avatar">
                <Bot size={16} />
            </div>

            <div className="typing-bubble">
                <span className="agent-typing">
                    {agentName || 'Agent'} is typing
                </span>
                <div className="typing-dots">
                    <motion.span
                        animate={{ y: [0, -8, 0] }}
                        transition={{ repeat: Infinity, duration: 0.6, delay: 0 }}
                    />
                    <motion.span
                        animate={{ y: [0, -8, 0] }}
                        transition={{ repeat: Infinity, duration: 0.6, delay: 0.2 }}
                    />
                    <motion.span
                        animate={{ y: [0, -8, 0] }}
                        transition={{ repeat: Infinity, duration: 0.6, delay: 0.4 }}
                    />
                </div>
            </div>
        </motion.div>
    );
}

function mapApiMessageToUiMessage(message: ChatMessageRecord): ChatMessageState {
    return {
        id: message.id,
        sessionId: message.session_id,
        sender: message.sender === 'user' ? 'user' : 'agent',
        role: message.role === 'user' ? 'user' : 'assistant',
        agentId: message.agent_id || undefined,
        agentName: message.agent_name || undefined,
        content: message.content,
        timestamp: new Date(message.created_at),
        status: message.status === 'failed' ? 'error' : 'delivered',
        metadata: message.metadata,
        isStreaming: message.status === 'streaming',
        sequenceNumber: message.sequence_number,
        feedback: message.feedback?.feedback_type || null,
        errorMessage: message.error_message || null,
    };
}

function mapWorkspaceRoute(route: ChatWorkspaceResponse['route']): RoutingMetadata {
    return {
        source: route.source || undefined,
        reason: route.reason || undefined,
        inferredTaskType: route.inferred_task_type || undefined,
        inferredAgentType: route.inferred_agent_type || undefined,
        mode: route.mode === 'balanced' || route.mode === 'high_accuracy' || route.mode === 'budget'
            ? route.mode
            : undefined,
        startProjectMode: route.start_project_mode,
    };
}

function mapWorkspaceRoom(room: ChatWorkspaceResponse['rooms'][number]): OfficeRoom {
    return {
        id: room.id as OfficeRoomId,
        title: room.title,
        label: room.label,
        status: normalizeRoomStatus(room.status),
        detail: room.detail,
        metric: room.metric,
        description: room.description,
    };
}

function mapWorkspaceActivityItem(
    item: ChatWorkspaceResponse['activity_feed'][number]
): ActivityFeedItem {
    return {
        id: item.id,
        type: item.type,
        description: item.description,
        timestamp: new Date(item.timestamp),
        severity: normalizeSeverity(item.severity),
    };
}

function mapWorkspaceStat(item: ChatWorkspaceResponse['office_stats'][number]) {
    return {
        label: item.label,
        value: item.value,
        hint: item.hint,
    };
}

function mapWorkspaceTaskStage(
    item: ChatWorkspaceResponse['task_stages'][number]
): TaskStage {
    return {
        id: item.id,
        title: item.title,
        status: normalizeTaskStageStatus(item.status),
        detail: item.detail,
    };
}

function mapWorkspaceReplayItem(item: ChatWorkspaceResponse['replay'][number]) {
    return {
        id: item.id,
        type: item.type,
        description: item.description,
        timestamp: new Date(item.timestamp),
    };
}

function mergeWorkspaceActivityFeed(
    workspaceFeed: ActivityFeedItem[],
    localFeed: ActivityFeedItem[]
): ActivityFeedItem[] {
    const merged = [...workspaceFeed];
    for (const item of localFeed) {
        if (!merged.some((candidate) => candidate.id === item.id)) {
            merged.push(item);
        }
    }

    return merged
        .sort((left, right) => right.timestamp.getTime() - left.timestamp.getTime())
        .slice(0, 12);
}

function mergeOfficeStats(
    localStats: Array<{ label: string; value: string; hint: string }>,
    workspaceStats: Array<{ label: string; value: string; hint: string }>
) {
    const merged = [...workspaceStats];
    for (const stat of localStats) {
        if (!merged.some((candidate) => candidate.label === stat.label)) {
            merged.unshift(stat);
        }
    }
    return merged;
}

function normalizeRoomStatus(value: string): OfficeRoom['status'] {
    return value === 'active' || value === 'watching' || value === 'idle' || value === 'alert'
        ? value
        : 'idle';
}

function normalizeSeverity(value: string): ActivityFeedItem['severity'] {
    return value === 'info' || value === 'success' || value === 'warning' || value === 'critical'
        ? value
        : 'info';
}

function normalizeTaskStageStatus(value: string): TaskStage['status'] {
    return value === 'done' || value === 'active' || value === 'waiting' || value === 'alert'
        ? value
        : 'waiting';
}

function createClientMessageId(): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
    }

    return `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
}

function getAgentColor(agentId: string): string {
    const colors = [
        '#667eea',
        '#764ba2',
        '#f093fb',
        '#4facfe',
        '#43e97b',
        '#fa709a',
        '#feca57',
        '#48dbfb',
    ];

    if (!agentId || typeof agentId !== 'string') {
        return colors[0];
    }

    const hash = agentId.split('').reduce((accumulator, char) => {
        return char.charCodeAt(0) + ((accumulator << 5) - accumulator);
    }, 0);

    return colors[Math.abs(hash) % colors.length];
}

function findLatestMessage(
    messages: ChatMessageState[],
    sender: ChatMessageState['sender']
): ChatMessageState | undefined {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
        if (messages[index].sender === sender) {
            return messages[index];
        }
    }

    return undefined;
}

function extractRoutingMetadata(metadata?: Record<string, unknown>): RoutingMetadata | null {
    if (!metadata || typeof metadata !== 'object') {
        return null;
    }

    const routing = metadata.routing;
    if (!routing || typeof routing !== 'object' || Array.isArray(routing)) {
        return null;
    }

    const data = routing as Record<string, unknown>;
    const normalizedMode = data.mode;
    return {
        source: typeof data.source === 'string' ? data.source : undefined,
        reason: typeof data.reason === 'string' ? data.reason : undefined,
        inferredTaskType: typeof data.inferred_task_type === 'string' ? data.inferred_task_type : undefined,
        inferredAgentType: typeof data.inferred_agent_type === 'string' ? data.inferred_agent_type : undefined,
        mode: normalizedMode === 'balanced' || normalizedMode === 'high_accuracy' || normalizedMode === 'budget'
            ? normalizedMode
            : undefined,
        startProjectMode: typeof data.start_project_mode === 'boolean' ? data.start_project_mode : undefined,
    };
}

function buildActivityFeed({
    messages,
    selectedAgent,
    latestRouting,
    connectionStatus,
    reconnectAttempt,
    lastError,
    typing,
    workflowState,
}: {
    messages: ChatMessageState[];
    selectedAgent: Agent | null;
    latestRouting: RoutingMetadata | null;
    connectionStatus: string;
    reconnectAttempt: number;
    lastError: { message: string; code: string } | null;
    typing: { isTyping: boolean; agentName: string | null };
    workflowState: 'idle' | 'dispatching' | 'coordinating' | 'returning';
}): ActivityFeedItem[] {
    const items: ActivityFeedItem[] = [];

    if (connectionStatus !== 'connected') {
        items.push({
            id: `transport-${connectionStatus}`,
            type: 'TRANSPORT',
            description: connectionStatus === 'connecting'
                ? `Realtime reconnect in progress${reconnectAttempt > 0 ? `, attempt ${reconnectAttempt}` : ''}.`
                : 'Realtime channel degraded; HTTP fallback remains active.',
            timestamp: new Date(),
            severity: connectionStatus === 'error' ? 'critical' : 'warning',
        });
    }

    if (workflowState !== 'idle') {
        items.push({
            id: `workflow-${workflowState}`,
            type: 'WORKFLOW',
            description: formatWorkflowState(workflowState),
            timestamp: new Date(),
            severity: workflowState === 'returning' ? 'success' : 'info',
        });
    }

    if (typing.isTyping) {
        items.push({
            id: 'typing-active',
            type: 'AGENT_ASSIGNED',
            description: `${typing.agentName || selectedAgent?.name || 'Assigned agent'} is actively producing a response.`,
            timestamp: new Date(),
            severity: 'info',
        });
    }

    if (latestRouting?.source || latestRouting?.inferredTaskType) {
        items.push({
            id: 'routing-latest',
            type: 'ROUTE_DECIDED',
            description: `${formatRouteSource(latestRouting?.source || 'manual')} path selected${latestRouting?.inferredTaskType ? ` for ${latestRouting.inferredTaskType}` : ''}.`,
            timestamp: new Date(),
            severity: 'info',
        });
    }

    if (lastError) {
        items.push({
            id: `error-${lastError.code}`,
            type: 'RETRY_TRIGGERED',
            description: lastError.message,
            timestamp: new Date(),
            severity: 'critical',
        });
    }

    messages.slice(-8).forEach((message) => {
        if (message.sender === 'user') {
            items.push({
                id: `${message.id}-user`,
                type: 'TASK_STARTED',
                description: `User request entered the office${selectedAgent ? ` via ${selectedAgent.name}` : ''}.`,
                timestamp: message.timestamp,
                severity: message.status === 'error' ? 'warning' : 'info',
            });
            return;
        }

        items.push({
            id: `${message.id}-assistant`,
            type: message.status === 'error' ? 'VALIDATION_FAILED' : 'FINAL_RESPONSE_SENT',
            description: `${message.agentName || 'Assistant'} ${message.status === 'error' ? 'reported a failed turn.' : 'returned a completed response.'}`,
            timestamp: message.timestamp,
            severity: message.status === 'error' ? 'critical' : 'success',
        });
    });

    return items
        .sort((left, right) => right.timestamp.getTime() - left.timestamp.getTime())
        .slice(0, 10);
}

function buildOfficeRooms({
    selectedAgent,
    latestRouting,
    latestUserMessage,
    latestAssistantMessage,
    connectionStatus,
    typing,
    workflowState,
    lastError,
    startProjectMode,
}: {
    selectedAgent: Agent | null;
    latestRouting: RoutingMetadata | null;
    latestUserMessage: ChatMessageState | undefined;
    latestAssistantMessage: ChatMessageState | undefined;
    connectionStatus: string;
    typing: { isTyping: boolean; agentName: string | null };
    workflowState: 'idle' | 'dispatching' | 'coordinating' | 'returning';
    lastError: { message: string } | null;
    startProjectMode: boolean;
}): OfficeRoom[] {
    return [
        {
            id: 'strategy',
            title: 'Strategy Center',
            label: 'Planning Room',
            status: workflowState === 'dispatching' || workflowState === 'coordinating' ? 'active' : 'watching',
            detail: latestRouting?.reason || 'Incoming work is decomposed and routed here first.',
            metric: latestRouting?.inferredTaskType || 'general intake',
            description: 'Central planning room for orchestration, task decomposition, and outward assignment.',
        },
        {
            id: 'boss',
            title: "Boss's Office",
            label: 'Executive Oversight',
            status: lastError ? 'alert' : connectionStatus !== 'connected' ? 'watching' : 'idle',
            detail: lastError?.message || 'Escalation, retries, and guardrails remain visible here.',
            metric: lastError ? 'attention required' : 'nominal',
            description: 'Executive oversight surface for retries, interventions, and risk conditions.',
        },
        {
            id: 'voting',
            title: 'Voting Chamber',
            label: 'Governance',
            status: startProjectMode && latestRouting?.source === 'executive_router' ? 'active' : 'idle',
            detail: startProjectMode
                ? 'Project mode enables richer debate and governance paths for complex work.'
                : 'Waiting for a debate or approval event.',
            metric: startProjectMode ? 'project governance ready' : 'standby',
            description: 'Structured decision space for approval, conflict resolution, and policy votes.',
        },
        {
            id: 'collaboration',
            title: 'Collaboration Hub',
            label: 'Shared Pod Space',
            status: workflowState === 'coordinating' ? 'active' : 'idle',
            detail: typing.isTyping
                ? `${typing.agentName || selectedAgent?.name || 'Assigned specialist'} is cross-checking the current turn.`
                : 'Specialists gather here when tasks require visible coordination.',
            metric: typing.isTyping ? 'live exchange' : 'single-threaded',
            description: 'Shared workspace where parallel specialists exchange signals and validate output.',
        },
        {
            id: 'memory',
            title: 'Memory Vault',
            label: 'Context Core',
            status: latestUserMessage && latestAssistantMessage ? 'watching' : 'idle',
            detail: latestAssistantMessage
                ? 'Long-term context and recent turns are available to the responding agent.'
                : 'Persistent context will illuminate after the first completed turn.',
            metric: latestAssistantMessage ? 'session memory engaged' : 'awaiting recall',
            description: 'Persistent memory surface for session continuity, user context, and retrieval traces.',
        },
        {
            id: 'incubator',
            title: 'Specialist Incubator',
            label: 'Capability Lab',
            status: startProjectMode && !selectedAgent ? 'watching' : 'idle',
            detail: latestRouting?.inferredAgentType
                ? `Current route is leaning toward ${latestRouting.inferredAgentType}.`
                : 'The incubator remains on standby until a capability gap is detected.',
            metric: latestRouting?.inferredAgentType || 'no hiring event',
            description: 'Area reserved for onboarding or comparing specialist capabilities when new coverage is needed.',
        },
        {
            id: 'execution',
            title: 'Active Pods',
            label: 'Execution Floor',
            status: typing.isTyping || workflowState === 'returning' ? 'active' : 'watching',
            detail: latestAssistantMessage?.agentName
                ? `${latestAssistantMessage.agentName} owns the most recent completed response.`
                : 'Tool execution and specialist output will surface here.',
            metric: latestAssistantMessage?.agentName || selectedAgent?.name || 'standby',
            description: 'Specialized work pods for deep execution, validation, and delivery preparation.',
        },
    ];
}

function buildTaskStages({
    workflowState,
    latestRouting,
    latestAssistantMessage,
    typing,
    lastError,
    startProjectMode,
    selectedAgent,
}: {
    workflowState: 'idle' | 'dispatching' | 'coordinating' | 'returning';
    latestRouting: RoutingMetadata | null;
    latestAssistantMessage: ChatMessageState | undefined;
    typing: { isTyping: boolean; agentName: string | null };
    lastError: { message: string } | null;
    startProjectMode: boolean;
    selectedAgent: Agent | null;
}): TaskStage[] {
    return [
        {
            id: 'intake',
            title: 'Front Desk Intake',
            status: latestAssistantMessage || workflowState !== 'idle' ? 'done' : 'waiting',
            detail: selectedAgent ? `${selectedAgent.name} is configured as the intake specialist.` : 'Awaiting agent selection or first request.',
        },
        {
            id: 'routing',
            title: 'Routing and Planning',
            status: workflowState === 'dispatching' || workflowState === 'coordinating'
                ? 'active'
                : latestRouting
                    ? 'done'
                    : 'waiting',
            detail: latestRouting?.reason || 'Planner will resolve route and task type on the next send.',
        },
        {
            id: 'execution',
            title: startProjectMode ? 'Collaborative Execution' : 'Specialist Execution',
            status: typing.isTyping ? 'active' : latestAssistantMessage ? 'done' : 'waiting',
            detail: typing.isTyping
                ? `${typing.agentName || selectedAgent?.name || 'Assigned specialist'} is generating the current answer.`
                : 'Execution pod remains ready for the next live turn.',
        },
        {
            id: 'validation',
            title: 'Validation and Risk Check',
            status: lastError ? 'alert' : workflowState === 'returning' ? 'active' : latestAssistantMessage ? 'done' : 'waiting',
            detail: lastError ? lastError.message : 'Response quality and policy checks settle here before delivery.',
        },
        {
            id: 'delivery',
            title: 'Front Desk Delivery',
            status: latestAssistantMessage ? 'done' : 'waiting',
            detail: latestAssistantMessage
                ? `${latestAssistantMessage.agentName || 'Assistant'} completed the most recent response.`
                : 'Delivery remains pending until the office finishes the first turn.',
        },
    ];
}

function formatExecutionMode(mode: ChatExecutionMode): string {
    if (mode === 'high_accuracy') {
        return 'High Accuracy';
    }
    if (mode === 'budget') {
        return 'Budget Mode';
    }
    return 'Balanced';
}

function formatDisplayMode(mode: ChatDisplayMode): string {
    if (mode === 'full_simulation') {
        return 'Full Simulation';
    }
    if (mode === 'executive') {
        return 'Executive';
    }
    return 'Simple';
}

function formatRouteSource(source: string): string {
    if (source === 'executive_router') {
        return 'Executive Router';
    }
    if (source === 'auto') {
        return 'Auto Router';
    }
    if (source === 'explicit') {
        return 'Manual Selection';
    }
    if (source === 'session') {
        return 'Session Preference';
    }
    return 'Live Route';
}

function formatWorkflowState(
    workflowState: 'idle' | 'dispatching' | 'coordinating' | 'returning'
): string {
    if (workflowState === 'dispatching') {
        return 'Request moving into strategy center.';
    }
    if (workflowState === 'coordinating') {
        return 'Office actively coordinating specialist work.';
    }
    if (workflowState === 'returning') {
        return 'Response package returning to the front desk.';
    }
    return 'Office floor is stable and awaiting the next turn.';
}

function formatRelativeTime(value: Date): string {
    const diffMs = Date.now() - value.getTime();
    if (diffMs < 60_000) {
        return 'just now';
    }
    if (diffMs < 3_600_000) {
        return `${Math.round(diffMs / 60_000)}m ago`;
    }
    if (diffMs < 86_400_000) {
        return `${Math.round(diffMs / 3_600_000)}h ago`;
    }
    return value.toLocaleDateString();
}

function getRoomIcon(roomId: OfficeRoomId): React.ReactNode {
    if (roomId === 'strategy') {
        return <Building2 size={18} />;
    }
    if (roomId === 'boss') {
        return <ShieldAlert size={18} />;
    }
    if (roomId === 'voting') {
        return <Users size={18} />;
    }
    if (roomId === 'collaboration') {
        return <Workflow size={18} />;
    }
    if (roomId === 'memory') {
        return <Database size={18} />;
    }
    if (roomId === 'incubator') {
        return <Sparkles size={18} />;
    }
    return <Briefcase size={18} />;
}
