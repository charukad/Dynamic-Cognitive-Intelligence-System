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
    Pause,
    Play,
    RotateCcw,
    ShieldAlert,
    SkipBack,
    SkipForward,
    Sparkles,
    Maximize2,
    Minimize2,
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
    ChatWorkspaceDagResponse,
    ChatWorkspaceReplayResponse,
    ChatWorkspaceResponse,
    ChatWorkspaceRoomDetailResponse,
    createChatSession,
    getChatWorkspaceDag,
    getChatWorkspaceReplay,
    getChatWorkspace,
    getChatWorkspaceRoom,
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
type FullscreenWorkspaceView = 'live_graph' | 'workspace' | 'analytics';
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

interface GraphNodeState {
    id: string;
    label: string;
    kind: string;
    status: 'active' | 'watching' | 'idle' | 'alert';
    x: number;
    y: number;
}

interface GraphEdgeState {
    id: string;
    fromId: string;
    toId: string;
    label: string;
    status: 'info' | 'success' | 'warning' | 'critical';
}

interface RoomTimelineItemState {
    id: string;
    roomId: string;
    roomTitle: string | null;
    type: string;
    description: string;
    timestamp: Date;
    severity: 'info' | 'success' | 'warning' | 'critical';
}

interface RoomDetailMessageState {
    id: string;
    role: string;
    sender: string;
    content: string;
    status: string;
    agentName: string | null;
    createdAt: Date;
}

interface RoomDetailState {
    room: OfficeRoom;
    summary: string;
    metrics: Array<{ label: string; value: string; hint: string }>;
    highlights: string[];
    recentEvents: RoomTimelineItemState[];
    relatedMessages: RoomDetailMessageState[];
    actions: string[];
}

interface DagNodeState {
    id: string;
    title: string;
    roomId: string | null;
    status: 'done' | 'active' | 'waiting' | 'alert';
    detail: string;
    dependencies: string[];
    startedAt: Date | null;
    completedAt: Date | null;
    executionTimeMs: number | null;
    assignedAgent: string | null;
    evaluationScore: number | null;
    retryCount: number;
    modelUsed: string | null;
    eventIds: string[];
}

interface DagEdgeState {
    id: string;
    fromId: string;
    toId: string;
    label: string;
    status: 'info' | 'success' | 'warning' | 'critical';
}

interface DagSnapshotState {
    sessionId: string;
    summary: string;
    latestNodeId: string | null;
    totalDurationMs: number | null;
    nodes: DagNodeState[];
    edges: DagEdgeState[];
}

interface ReplayFrameState {
    id: string;
    index: number;
    type: string;
    description: string;
    timestamp: Date;
    severity: 'info' | 'success' | 'warning' | 'critical';
    roomId: string | null;
    roomTitle: string | null;
    agentName: string | null;
    relatedMessageId: string | null;
    focusNodeIds: string[];
    focusEdgeId: string | null;
}

interface ReplaySnapshotState {
    sessionId: string;
    summary: string;
    currentIndex: number;
    startedAt: Date | null;
    endedAt: Date | null;
    totalDurationMs: number | null;
    frames: ReplayFrameState[];
}

interface FullscreenCapableElement extends HTMLElement {
    webkitRequestFullscreen?: () => Promise<void> | void;
}

interface FullscreenCapableDocument extends Document {
    webkitExitFullscreen?: () => Promise<void> | void;
    webkitFullscreenElement?: Element | null;
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
    const [fullscreenWorkspaceView, setFullscreenWorkspaceView] = useState<FullscreenWorkspaceView>('live_graph');
    const [isRoomDetailOpen, setIsRoomDetailOpen] = useState(false);
    const [roomDetail, setRoomDetail] = useState<RoomDetailState | null>(null);
    const [isRoomDetailLoading, setIsRoomDetailLoading] = useState(false);
    const [roomDetailError, setRoomDetailError] = useState<string | null>(null);
    const [dagSnapshot, setDagSnapshot] = useState<DagSnapshotState | null>(null);
    const [isDagLoading, setIsDagLoading] = useState(false);
    const [dagError, setDagError] = useState<string | null>(null);
    const [replaySnapshot, setReplaySnapshot] = useState<ReplaySnapshotState | null>(null);
    const [isReplayLoading, setIsReplayLoading] = useState(false);
    const [replayError, setReplayError] = useState<string | null>(null);
    const [isFullscreenSupported, setIsFullscreenSupported] = useState(true);
    const [isFullscreen, setIsFullscreen] = useState(false);
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
    const chatInterfaceRef = useRef<HTMLDivElement>(null);

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
            if (isRoomDetailOpen && currentSessionId === sessionId) {
                void refreshRoomDetail(sessionId, activeRoomId);
            }
            if (currentSessionId === sessionId && activeWorkspaceTab === 'dag') {
                void refreshDag(sessionId);
            }
            if (currentSessionId === sessionId && activeWorkspaceTab === 'replay') {
                void refreshReplay(sessionId);
            }
        } catch (error) {
            console.error('Failed to refresh chat workspace:', error);
        }
    }

    async function refreshRoomDetail(sessionId: string, roomId: OfficeRoomId) {
        setIsRoomDetailLoading(true);
        setRoomDetailError(null);
        try {
            const detail = await getChatWorkspaceRoom(sessionId, roomId);
            setRoomDetail(mapWorkspaceRoomDetail(detail));
        } catch (error) {
            console.error('Failed to refresh room detail:', error);
            setRoomDetail(null);
            setRoomDetailError('Failed to load room details.');
        } finally {
            setIsRoomDetailLoading(false);
        }
    }

    async function refreshDag(sessionId: string) {
        setIsDagLoading(true);
        setDagError(null);
        try {
            const snapshot = await getChatWorkspaceDag(sessionId);
            setDagSnapshot(mapWorkspaceDagSnapshot(snapshot));
        } catch (error) {
            console.error('Failed to refresh task DAG:', error);
            setDagError('Failed to load task DAG.');
            setDagSnapshot(null);
        } finally {
            setIsDagLoading(false);
        }
    }

    async function refreshReplay(sessionId: string) {
        setIsReplayLoading(true);
        setReplayError(null);
        try {
            const snapshot = await getChatWorkspaceReplay(sessionId);
            setReplaySnapshot(mapWorkspaceReplaySnapshot(snapshot));
        } catch (error) {
            console.error('Failed to refresh replay view:', error);
            setReplayError('Failed to load replay timeline.');
            setReplaySnapshot(null);
        } finally {
            setIsReplayLoading(false);
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
            setIsRoomDetailOpen(false);
            setRoomDetail(null);
            setRoomDetailError(null);
            setDagSnapshot(null);
            setDagError(null);
            setReplaySnapshot(null);
            setReplayError(null);
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
            setIsRoomDetailOpen(false);
            setRoomDetail(null);
            setRoomDetailError(null);
            setDagSnapshot(null);
            setDagError(null);
            setReplaySnapshot(null);
            setReplayError(null);
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
            setIsRoomDetailOpen(false);
            setRoomDetail(null);
            setRoomDetailError(null);
            setDagSnapshot(null);
            setDagError(null);
            setReplaySnapshot(null);
            setReplayError(null);
        }
    }, [currentSessionId]);

    useEffect(() => {
        if (!currentSessionId || !isRoomDetailOpen) {
            return;
        }

        void refreshRoomDetail(currentSessionId, activeRoomId);
    }, [activeRoomId, currentSessionId, isRoomDetailOpen]);

    useEffect(() => {
        if (!currentSessionId) {
            return;
        }

        if (activeWorkspaceTab === 'dag') {
            void refreshDag(currentSessionId);
        }
        if (activeWorkspaceTab === 'replay') {
            void refreshReplay(currentSessionId);
        }
    }, [activeWorkspaceTab, currentSessionId]);

    function handleRoomSelect(roomId: OfficeRoomId) {
        setActiveRoomId(roomId);
        setIsRoomDetailOpen(true);
    }

    function handleReplayFocusRoom(roomId: OfficeRoomId) {
        setActiveRoomId(roomId);
    }

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
    const graphNodes = workspaceSnapshot?.graph_nodes.length
        ? workspaceSnapshot.graph_nodes.map(mapWorkspaceGraphNode)
        : buildFallbackGraphNodes(officeRooms, selectedAgent?.name || latestAssistantMessage?.agentName || null);
    const graphEdges = workspaceSnapshot?.graph_edges.length
        ? workspaceSnapshot.graph_edges.map(mapWorkspaceGraphEdge)
        : buildFallbackGraphEdges(latestRouting);
    const roomTimeline = workspaceSnapshot?.room_timeline.length
        ? workspaceSnapshot.room_timeline.map(mapWorkspaceRoomTimelineItem)
        : activityFeed
            .slice(0, 8)
            .map((item) => ({
                id: item.id,
                roomId: activeRoom.id,
                roomTitle: activeRoom.title,
                type: item.type,
                description: item.description,
                timestamp: item.timestamp,
                severity: item.severity,
            }));
    const effectiveGraphOverlayEnabled = isFullscreen && fullscreenWorkspaceView === 'live_graph'
        ? true
        : graphOverlayEnabled;

    const getFullscreenElement = () => {
        const fullscreenDocument = document as FullscreenCapableDocument;
        return fullscreenDocument.fullscreenElement ?? fullscreenDocument.webkitFullscreenElement ?? null;
    };

    useEffect(() => {
        const targetElement = chatInterfaceRef.current as FullscreenCapableElement | null;
        if (!targetElement) {
            setIsFullscreenSupported(false);
            return;
        }

        const canRequestFullscreen = typeof targetElement.requestFullscreen === 'function'
            || typeof targetElement.webkitRequestFullscreen === 'function';
        setIsFullscreenSupported(canRequestFullscreen);

        const syncFullscreenState = () => {
            setIsFullscreen(getFullscreenElement() === targetElement);
        };

        syncFullscreenState();
        document.addEventListener('fullscreenchange', syncFullscreenState);
        document.addEventListener('webkitfullscreenchange', syncFullscreenState);

        return () => {
            document.removeEventListener('fullscreenchange', syncFullscreenState);
            document.removeEventListener('webkitfullscreenchange', syncFullscreenState);
        };
    }, []);

    const toggleFullscreen = async () => {
        const targetElement = chatInterfaceRef.current as FullscreenCapableElement | null;
        if (!targetElement) {
            return;
        }

        const fullscreenDocument = document as FullscreenCapableDocument;
        try {
            if (getFullscreenElement() === targetElement) {
                if (typeof fullscreenDocument.exitFullscreen === 'function') {
                    await fullscreenDocument.exitFullscreen();
                    return;
                }
                if (typeof fullscreenDocument.webkitExitFullscreen === 'function') {
                    await fullscreenDocument.webkitExitFullscreen();
                    return;
                }
                return;
            }

            if (typeof targetElement.requestFullscreen === 'function') {
                await targetElement.requestFullscreen();
                return;
            }
            if (typeof targetElement.webkitRequestFullscreen === 'function') {
                await targetElement.webkitRequestFullscreen();
            }
        } catch (error) {
            console.error('Failed to toggle fullscreen mode:', error);
        }
    };

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
            <div
                ref={chatInterfaceRef}
                className={`chat-interface dcis-chat ${embedded ? 'embedded' : ''} ${isFullscreen ? 'is-fullscreen' : ''}`}
            >
                <div className="chat-floating-controls">
                    <button
                        type="button"
                        className={`fullscreen-toggle ${isFullscreen ? 'active' : ''}`}
                        aria-label={isFullscreen ? 'Exit full screen' : 'Enter full screen'}
                        aria-pressed={isFullscreen}
                        onClick={() => {
                            void toggleFullscreen();
                        }}
                        disabled={!isFullscreenSupported}
                        title={isFullscreenSupported ? 'Toggle full screen' : 'Full screen is not supported in this browser'}
                    >
                        {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                        {isFullscreen ? 'Exit Full Screen' : 'Full Screen'}
                    </button>
                </div>
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
                            <div className="front-desk-header-actions">
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
                                {isFullscreen && (
                                    <div className="fullscreen-view-switch" role="tablist" aria-label="Fullscreen right panel view">
                                        {([
                                            ['live_graph', 'Live Office Graph'],
                                            ['workspace', 'Workspace'],
                                            ['analytics', 'Analytics'],
                                        ] as Array<[FullscreenWorkspaceView, string]>).map(([viewId, label]) => (
                                            <button
                                                key={viewId}
                                                type="button"
                                                role="tab"
                                                aria-selected={fullscreenWorkspaceView === viewId}
                                                className={`fullscreen-view-chip ${fullscreenWorkspaceView === viewId ? 'active' : ''}`}
                                                onClick={() => {
                                                    setFullscreenWorkspaceView(viewId);
                                                    setIsRoomDetailOpen(false);
                                                }}
                                            >
                                                {label}
                                            </button>
                                        ))}
                                    </div>
                                )}
                                {(!isFullscreen || fullscreenWorkspaceView !== 'analytics') && (
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
                                )}
                                {(!isFullscreen || fullscreenWorkspaceView === 'workspace') && (
                                    <button
                                        type="button"
                                        className={`overlay-toggle ${graphOverlayEnabled ? 'active' : ''}`}
                                        aria-pressed={graphOverlayEnabled}
                                        onClick={() => setGraphOverlayEnabled((current) => !current)}
                                    >
                                        <GitBranch size={14} />
                                        Live Office Graph
                                    </button>
                                )}
                            </div>
                        </div>

                        {isFullscreen ? (
                            <div className={`fullscreen-right-content ${fullscreenWorkspaceView.replace('_', '-')}`}>
                                {fullscreenWorkspaceView === 'analytics' ? (
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
                                        dagSnapshot={dagSnapshot}
                                        isDagLoading={isDagLoading}
                                        dagError={dagError}
                                        replaySnapshot={replaySnapshot}
                                        isReplayLoading={isReplayLoading}
                                        replayError={replayError}
                                        onReplayFocusRoom={handleReplayFocusRoom}
                                    />
                                ) : (
                                    <OfficeWorkspace
                                        rooms={officeRooms}
                                        activeRoom={activeRoom}
                                        activeRoomId={activeRoomId}
                                        onRoomSelect={handleRoomSelect}
                                        workflowState={workflowState}
                                        graphOverlayEnabled={effectiveGraphOverlayEnabled}
                                        displayMode={resolvedDisplayMode}
                                        selectedAgent={selectedAgent}
                                        latestRouting={latestRouting}
                                        latestAssistantMessage={latestAssistantMessage}
                                        lastErrorMessage={lastError?.message || null}
                                        typingAgentName={typing.agentName}
                                        graphNodes={graphNodes}
                                        graphEdges={graphEdges}
                                        roomTimeline={roomTimeline}
                                        onRoomInspect={() => setIsRoomDetailOpen(true)}
                                        onCloseRoomDetail={() => setIsRoomDetailOpen(false)}
                                        isRoomDetailOpen={isRoomDetailOpen}
                                        roomDetail={roomDetail}
                                        isRoomDetailLoading={isRoomDetailLoading}
                                        roomDetailError={roomDetailError}
                                    />
                                )}
                            </div>
                        ) : (
                            <>
                                <OfficeWorkspace
                                    rooms={officeRooms}
                                    activeRoom={activeRoom}
                                    activeRoomId={activeRoomId}
                                    onRoomSelect={handleRoomSelect}
                                    workflowState={workflowState}
                                    graphOverlayEnabled={graphOverlayEnabled}
                                    displayMode={resolvedDisplayMode}
                                    selectedAgent={selectedAgent}
                                    latestRouting={latestRouting}
                                    latestAssistantMessage={latestAssistantMessage}
                                    lastErrorMessage={lastError?.message || null}
                                    typingAgentName={typing.agentName}
                                    graphNodes={graphNodes}
                                    graphEdges={graphEdges}
                                    roomTimeline={roomTimeline}
                                    onRoomInspect={() => setIsRoomDetailOpen(true)}
                                    onCloseRoomDetail={() => setIsRoomDetailOpen(false)}
                                    isRoomDetailOpen={isRoomDetailOpen}
                                    roomDetail={roomDetail}
                                    isRoomDetailLoading={isRoomDetailLoading}
                                    roomDetailError={roomDetailError}
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
                                    dagSnapshot={dagSnapshot}
                                    isDagLoading={isDagLoading}
                                    dagError={dagError}
                                    replaySnapshot={replaySnapshot}
                                    isReplayLoading={isReplayLoading}
                                    replayError={replayError}
                                    onReplayFocusRoom={handleReplayFocusRoom}
                                />
                            </>
                        )}
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
    graphNodes: GraphNodeState[];
    graphEdges: GraphEdgeState[];
    roomTimeline: RoomTimelineItemState[];
    onRoomInspect: () => void;
    onCloseRoomDetail: () => void;
    isRoomDetailOpen: boolean;
    roomDetail: RoomDetailState | null;
    isRoomDetailLoading: boolean;
    roomDetailError: string | null;
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
    graphNodes,
    graphEdges,
    roomTimeline,
    onRoomInspect,
    onCloseRoomDetail,
    isRoomDetailOpen,
    roomDetail,
    isRoomDetailLoading,
    roomDetailError,
}: OfficeWorkspaceProps) {
    const visibleTimeline = roomTimeline.filter((item) => item.roomId === activeRoom.id).slice(0, 6);
    const graphNodeMap = new Map(graphNodes.map((node) => [node.id, node]));
    const activeRoomDetail = roomDetail?.room.id === activeRoom.id ? roomDetail : null;

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
                        {graphEdges.map((edge) => {
                            const fromNode = graphNodeMap.get(edge.fromId);
                            const toNode = graphNodeMap.get(edge.toId);
                            if (!fromNode || !toNode) {
                                return null;
                            }

                            return (
                                <div
                                    key={edge.id}
                                    className={`graph-link status-${edge.status}`}
                                    style={buildGraphEdgeStyle(fromNode, toNode)}
                                >
                                    <span>{edge.label}</span>
                                </div>
                            );
                        })}
                        {graphNodes.map((node) => (
                            <div
                                key={node.id}
                                className={`graph-node status-${node.status} kind-${node.kind}`}
                                style={{
                                    left: `${node.x * 100}%`,
                                    top: `${node.y * 100}%`,
                                }}
                            >
                                <span>{node.label}</span>
                            </div>
                        ))}
                    </div>
                )}

                <div className="office-detail-panel">
                    <div className="office-detail-heading">
                        <span className="office-detail-kicker">Room Focus</span>
                        <h3>{activeRoom.title}</h3>
                        <p>{activeRoom.description}</p>
                        <button
                            type="button"
                            className="room-detail-trigger"
                            onClick={onRoomInspect}
                        >
                            {isRoomDetailOpen ? 'Refresh room panel' : 'Open room panel'}
                        </button>
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
                    <div className="room-timeline">
                        <div className="room-timeline-header">
                            <span className="office-detail-label">Room Timeline</span>
                            <strong>{activeRoom.title}</strong>
                        </div>
                        {visibleTimeline.length === 0 ? (
                            <div className="room-timeline-empty">
                                No persisted room events yet for this area.
                            </div>
                        ) : (
                            visibleTimeline.map((item) => (
                                <div key={item.id} className={`room-timeline-item severity-${item.severity}`}>
                                    <div className="room-timeline-meta">
                                        <strong>{item.type}</strong>
                                        <span>{formatRelativeTime(item.timestamp)}</span>
                                    </div>
                                    <p>{item.description}</p>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                <AnimatePresence initial={false}>
                    {isRoomDetailOpen && (
                        <motion.aside
                            className="room-detail-drawer"
                            role="dialog"
                            aria-modal="false"
                            aria-label={`${activeRoom.title} detail panel`}
                            initial={{ opacity: 0, x: 28 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 28 }}
                            transition={{ duration: 0.24 }}
                        >
                            <div className="room-detail-drawer-header">
                                <div>
                                    <span className="office-detail-kicker">Deep Inspection</span>
                                    <h4>{activeRoom.title}</h4>
                                    <p>{activeRoom.label}</p>
                                </div>
                                <button
                                    type="button"
                                    className="room-detail-close"
                                    onClick={onCloseRoomDetail}
                                    aria-label={`Close ${activeRoom.title} detail panel`}
                                >
                                    <X size={16} />
                                </button>
                            </div>

                            {isRoomDetailLoading ? (
                                <div className="room-detail-state" role="status" aria-live="polite">
                                    <LoaderCircle size={18} className="chat-loading-icon" />
                                    <span>Loading room detail...</span>
                                </div>
                            ) : roomDetailError ? (
                                <div className="room-detail-state room-detail-state-error" role="alert">
                                    <AlertCircle size={16} />
                                    <span>{roomDetailError}</span>
                                </div>
                            ) : activeRoomDetail ? (
                                <div className="room-detail-drawer-body">
                                    <div className="room-detail-section">
                                        <span className="office-detail-label">Summary</span>
                                        <p>{activeRoomDetail.summary}</p>
                                    </div>

                                    <div className="room-detail-section">
                                        <span className="office-detail-label">Room Metrics</span>
                                        <div className="room-detail-metrics">
                                            {activeRoomDetail.metrics.map((metric) => (
                                                <div key={metric.label} className="room-detail-metric-card">
                                                    <strong>{metric.value}</strong>
                                                    <span>{metric.label}</span>
                                                    <p>{metric.hint}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="room-detail-section">
                                        <span className="office-detail-label">Operational Highlights</span>
                                        <div className="room-detail-list">
                                            {activeRoomDetail.highlights.map((highlight) => (
                                                <div key={highlight} className="room-detail-list-item">
                                                    {highlight}
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="room-detail-section">
                                        <span className="office-detail-label">Available Actions</span>
                                        <div className="room-detail-list">
                                            {activeRoomDetail.actions.map((action) => (
                                                <div key={action} className="room-detail-list-item action-item">
                                                    {action}
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="room-detail-section">
                                        <span className="office-detail-label">Recent Events</span>
                                        <div className="room-detail-events">
                                            {activeRoomDetail.recentEvents.length === 0 ? (
                                                <div className="room-detail-empty">No persisted room events yet.</div>
                                            ) : (
                                                activeRoomDetail.recentEvents.slice(0, 6).map((event) => (
                                                    <div key={event.id} className={`room-detail-event severity-${event.severity}`}>
                                                        <div className="room-detail-event-meta">
                                                            <strong>{event.type}</strong>
                                                            <span>{formatRelativeTime(event.timestamp)}</span>
                                                        </div>
                                                        <p>{event.description}</p>
                                                    </div>
                                                ))
                                            )}
                                        </div>
                                    </div>

                                    <div className="room-detail-section">
                                        <span className="office-detail-label">Related Messages</span>
                                        <div className="room-detail-messages">
                                            {activeRoomDetail.relatedMessages.length === 0 ? (
                                                <div className="room-detail-empty">No related messages recorded for this room.</div>
                                            ) : (
                                                activeRoomDetail.relatedMessages.map((message) => (
                                                    <div key={message.id} className="room-detail-message">
                                                        <div className="room-detail-message-meta">
                                                            <strong>
                                                                {message.sender === 'agent'
                                                                    ? (message.agentName || 'Assistant')
                                                                    : 'User'}
                                                            </strong>
                                                            <span>{formatRelativeTime(message.createdAt)}</span>
                                                        </div>
                                                        <p>{message.content || 'No stored content.'}</p>
                                                    </div>
                                                ))
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="room-detail-empty">Select a room to inspect deeper operational context.</div>
                            )}
                        </motion.aside>
                    )}
                </AnimatePresence>
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
    dagSnapshot: DagSnapshotState | null;
    isDagLoading: boolean;
    dagError: string | null;
    replaySnapshot: ReplaySnapshotState | null;
    isReplayLoading: boolean;
    replayError: string | null;
    onReplayFocusRoom: (roomId: OfficeRoomId) => void;
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
    dagSnapshot,
    isDagLoading,
    dagError,
    replaySnapshot,
    isReplayLoading,
    replayError,
    onReplayFocusRoom,
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
                    <TaskDagViewer
                        dagSnapshot={dagSnapshot}
                        taskStages={taskStages}
                        isLoading={isDagLoading}
                        error={dagError}
                    />
                )}

                {activeTab === 'replay' && (
                    <ReplayViewer
                        replaySnapshot={replaySnapshot}
                        replayItems={replayItems}
                        latestAssistantMessage={latestAssistantMessage}
                        selectedAgentName={selectedAgentName}
                        isLoading={isReplayLoading}
                        error={replayError}
                        onReplayFocusRoom={onReplayFocusRoom}
                    />
                )}
            </div>
        </div>
    );
}

interface TaskDagViewerProps {
    dagSnapshot: DagSnapshotState | null;
    taskStages: TaskStage[];
    isLoading: boolean;
    error: string | null;
}

function TaskDagViewer({ dagSnapshot, taskStages, isLoading, error }: TaskDagViewerProps) {
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

    const defaultSelectedNodeId = dagSnapshot?.latestNodeId
        || dagSnapshot?.nodes.find((node) => node.status === 'active' || node.status === 'alert')?.id
        || dagSnapshot?.nodes[0]?.id
        || null;
    const effectiveSelectedNodeId = selectedNodeId && dagSnapshot?.nodes.some((node) => node.id === selectedNodeId)
        ? selectedNodeId
        : defaultSelectedNodeId;
    const selectedNode = dagSnapshot?.nodes.find((node) => node.id === effectiveSelectedNodeId)
        || dagSnapshot?.nodes[0]
        || null;

    if (isLoading) {
        return (
            <div className="analytics-empty" role="status" aria-live="polite">
                Loading task DAG...
            </div>
        );
    }

    if (error) {
        return (
            <div className="analytics-empty" role="alert">
                {error}
            </div>
        );
    }

    if (!dagSnapshot) {
        return (
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
        );
    }

    return (
        <div className="task-dag-viewer">
            <div className="task-dag-summary">
                <div className="task-dag-stat">
                    <span>Flow Summary</span>
                    <strong>{dagSnapshot.summary}</strong>
                </div>
                <div className="task-dag-stat">
                    <span>Total Runtime</span>
                    <strong>{formatDurationMs(dagSnapshot.totalDurationMs) || 'Not captured'}</strong>
                </div>
                <div className="task-dag-stat">
                    <span>Tracked Nodes</span>
                    <strong>{dagSnapshot.nodes.length}</strong>
                </div>
            </div>

            <div className="task-dag-layout">
                <div className="task-dag-graph">
                    {dagSnapshot.nodes.map((node) => (
                        <button
                            key={node.id}
                            type="button"
                            className={`task-dag-node status-${node.status} ${selectedNode?.id === node.id ? 'selected' : ''}`}
                            onClick={() => setSelectedNodeId(node.id)}
                            aria-pressed={selectedNode?.id === node.id}
                        >
                            <div className="task-dag-node-header">
                                <strong>{node.title}</strong>
                                <span>{node.status}</span>
                            </div>
                            <p>{node.detail}</p>
                            <div className="task-dag-node-meta">
                                <span>{node.assignedAgent || 'No assignee'}</span>
                                <span>{node.retryCount ? `${node.retryCount} retries` : 'No retries'}</span>
                            </div>
                            {node.dependencies.length > 0 && (
                                <div className="task-dag-dependencies">
                                    {node.dependencies.map((dependency) => (
                                        <span key={`${node.id}-${dependency}`} className="dependency-chip">
                                            {dependency}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </button>
                    ))}
                </div>

                <div className="task-dag-detail">
                    <span className="office-detail-label">Selected Node</span>
                    <strong>{selectedNode?.title || 'No node selected'}</strong>
                    <p>{selectedNode?.detail || 'Select a node to inspect its persisted execution details.'}</p>
                    {selectedNode && (
                        <div className="task-dag-detail-grid">
                            <div className="task-dag-detail-card">
                                <span>Status</span>
                                <strong>{selectedNode.status}</strong>
                                <p>Latest persisted phase state</p>
                            </div>
                            <div className="task-dag-detail-card">
                                <span>Assigned Agent</span>
                                <strong>{selectedNode.assignedAgent || 'Not captured'}</strong>
                                <p>Latest assignee associated with this phase</p>
                            </div>
                            <div className="task-dag-detail-card">
                                <span>Execution Time</span>
                                <strong>{formatDurationMs(selectedNode.executionTimeMs) || 'Not captured'}</strong>
                                <p>Measured from first to last event in this phase</p>
                            </div>
                            <div className="task-dag-detail-card">
                                <span>Evaluation Score</span>
                                <strong>{formatEvaluationScore(selectedNode.evaluationScore)}</strong>
                                <p>User or delivery quality signal, if available</p>
                            </div>
                            <div className="task-dag-detail-card">
                                <span>Retry History</span>
                                <strong>{selectedNode.retryCount}</strong>
                                <p>Persisted recovery events linked to this phase</p>
                            </div>
                            <div className="task-dag-detail-card">
                                <span>Model Used</span>
                                <strong>{selectedNode.modelUsed || 'Not captured'}</strong>
                                <p>Model metadata captured on the persisted response</p>
                            </div>
                        </div>
                    )}
                    {dagSnapshot.edges.length > 0 && (
                        <div className="task-dag-edge-list">
                            {dagSnapshot.edges
                                .filter((edge) => edge.toId === selectedNode?.id || edge.fromId === selectedNode?.id)
                                .map((edge) => (
                                    <div key={edge.id} className={`task-dag-edge-item status-${edge.status}`}>
                                        <strong>{edge.fromId}</strong>
                                        <span>{edge.label}</span>
                                        <strong>{edge.toId}</strong>
                                    </div>
                                ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

interface ReplayViewerProps {
    replaySnapshot: ReplaySnapshotState | null;
    replayItems: Array<{ id: string; type: string; description: string; timestamp: Date }>;
    latestAssistantMessage: ChatMessageState | undefined;
    selectedAgentName: string | null;
    isLoading: boolean;
    error: string | null;
    onReplayFocusRoom: (roomId: OfficeRoomId) => void;
}

function ReplayViewer({
    replaySnapshot,
    replayItems,
    latestAssistantMessage,
    selectedAgentName,
    isLoading,
    error,
    onReplayFocusRoom,
}: ReplayViewerProps) {
    const [manualReplayIndex, setManualReplayIndex] = useState<number | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const replayIndex = typeof manualReplayIndex === 'number' && replaySnapshot?.frames[manualReplayIndex]
        ? manualReplayIndex
        : (replaySnapshot?.currentIndex || 0);

    useEffect(() => {
        if (!replaySnapshot || !isPlaying || replaySnapshot.frames.length === 0) {
            return;
        }

        if (replayIndex >= replaySnapshot.frames.length - 1) {
            return;
        }

        const timer = window.setTimeout(() => {
            setManualReplayIndex((current) => {
                const baseIndex = typeof current === 'number' && replaySnapshot.frames[current]
                    ? current
                    : (replaySnapshot.currentIndex || 0);
                const nextIndex = Math.min(baseIndex + 1, replaySnapshot.frames.length - 1);
                if (nextIndex >= replaySnapshot.frames.length - 1) {
                    setIsPlaying(false);
                }
                return nextIndex;
            });
        }, 1100);

        return () => window.clearTimeout(timer);
    }, [isPlaying, replayIndex, replaySnapshot]);

    useEffect(() => {
        if (!replaySnapshot) {
            return;
        }

        const frame = replaySnapshot.frames[replayIndex];
        if (frame && isOfficeRoomId(frame.roomId)) {
            onReplayFocusRoom(frame.roomId);
        }
    }, [onReplayFocusRoom, replayIndex, replaySnapshot]);

    if (isLoading) {
        return (
            <div className="analytics-empty" role="status" aria-live="polite">
                Loading replay timeline...
            </div>
        );
    }

    if (error) {
        return (
            <div className="analytics-empty" role="alert">
                {error}
            </div>
        );
    }

    if (!replaySnapshot || replaySnapshot.frames.length === 0) {
        return (
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
        );
    }

    const currentFrame = replaySnapshot.frames[replayIndex] || replaySnapshot.frames[replaySnapshot.currentIndex] || replaySnapshot.frames[0];

    return (
        <div className="replay-viewer">
            <div className="replay-card replay-card-featured">
                <span className="office-detail-label">Current Replay Frame</span>
                <strong>{currentFrame.type}</strong>
                <p>{currentFrame.description}</p>
                <div className="replay-frame-meta">
                    <span>{currentFrame.agentName || currentFrame.roomTitle || 'Workspace event'}</span>
                    <span>{formatRelativeTime(currentFrame.timestamp)}</span>
                    <span>{replayIndex + 1}/{replaySnapshot.frames.length}</span>
                </div>
                <div className="replay-focus-chips">
                    {currentFrame.roomTitle && <span>{currentFrame.roomTitle}</span>}
                    {currentFrame.agentName && <span>{currentFrame.agentName}</span>}
                    {currentFrame.focusNodeIds.map((focusNodeId) => (
                        <span key={`${currentFrame.id}-${focusNodeId}`}>{focusNodeId}</span>
                    ))}
                </div>
            </div>

            <div className="replay-controls">
                <button
                    type="button"
                    className="replay-control-button"
                    onClick={() => {
                        setIsPlaying(false);
                        setManualReplayIndex(0);
                    }}
                    aria-label="Rewind replay to the first frame"
                >
                    <SkipBack size={14} />
                    Rewind
                </button>
                <button
                    type="button"
                    className="replay-control-button"
                    onClick={() => {
                        setIsPlaying(false);
                        setManualReplayIndex((current) => {
                            const baseIndex = typeof current === 'number'
                                ? current
                                : (replaySnapshot.currentIndex || 0);
                            return Math.max(baseIndex - 1, 0);
                        });
                    }}
                    aria-label="Step backward in replay"
                >
                    <RotateCcw size={14} />
                    Step Back
                </button>
                <button
                    type="button"
                    className="replay-control-button primary"
                    onClick={() => {
                        if (replayIndex >= replaySnapshot.frames.length - 1) {
                            setManualReplayIndex(0);
                            setIsPlaying(true);
                            return;
                        }
                        setIsPlaying((current) => !current);
                    }}
                    aria-label={isPlaying ? 'Pause replay playback' : 'Play replay playback'}
                >
                    {isPlaying ? <Pause size={14} /> : <Play size={14} />}
                    {isPlaying ? 'Pause' : 'Play'}
                </button>
                <button
                    type="button"
                    className="replay-control-button"
                    onClick={() => {
                        setIsPlaying(false);
                        setManualReplayIndex((current) => {
                            const baseIndex = typeof current === 'number'
                                ? current
                                : (replaySnapshot.currentIndex || 0);
                            return Math.min(baseIndex + 1, replaySnapshot.frames.length - 1);
                        });
                    }}
                    aria-label="Step forward in replay"
                >
                    <SkipForward size={14} />
                    Step Forward
                </button>
                <input
                    type="range"
                    min={0}
                    max={Math.max(replaySnapshot.frames.length - 1, 0)}
                    value={replayIndex}
                    onChange={(event) => {
                        setIsPlaying(false);
                        setManualReplayIndex(Number(event.target.value));
                    }}
                    className="replay-scrubber"
                    aria-label="Replay frame scrubber"
                />
            </div>

            <div className="replay-timeline">
                {replaySnapshot.frames.map((frame) => (
                    <button
                        key={frame.id}
                        type="button"
                        className={`replay-timeline-item severity-${frame.severity} ${frame.index === replayIndex ? 'active' : ''}`}
                        onClick={() => {
                            setIsPlaying(false);
                            setManualReplayIndex(frame.index);
                        }}
                    >
                        <div className="replay-timeline-header">
                            <strong>{frame.type}</strong>
                            <span>{frame.index + 1}</span>
                        </div>
                        <p>{frame.description}</p>
                    </button>
                ))}
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

function mapWorkspaceRoomDetail(
    detail: ChatWorkspaceRoomDetailResponse
): RoomDetailState {
    return {
        room: mapWorkspaceRoom(detail.room),
        summary: detail.summary,
        metrics: detail.metrics.map(mapWorkspaceStat),
        highlights: detail.highlights,
        recentEvents: detail.recent_events.map(mapWorkspaceRoomTimelineItem),
        relatedMessages: detail.related_messages.map((message) => ({
            id: message.id,
            role: message.role,
            sender: message.sender,
            content: message.content,
            status: message.status,
            agentName: message.agent_name || null,
            createdAt: new Date(message.created_at),
        })),
        actions: detail.actions,
    };
}

function mapWorkspaceDagSnapshot(snapshot: ChatWorkspaceDagResponse): DagSnapshotState {
    return {
        sessionId: snapshot.session_id,
        summary: snapshot.summary,
        latestNodeId: snapshot.latest_node_id || null,
        totalDurationMs: snapshot.total_duration_ms ?? null,
        nodes: snapshot.nodes.map((node) => ({
            id: node.id,
            title: node.title,
            roomId: node.room_id || null,
            status: normalizeTaskStageStatus(node.status),
            detail: node.detail,
            dependencies: node.dependencies,
            startedAt: node.started_at ? new Date(node.started_at) : null,
            completedAt: node.completed_at ? new Date(node.completed_at) : null,
            executionTimeMs: node.execution_time_ms ?? null,
            assignedAgent: node.assigned_agent || null,
            evaluationScore: typeof node.evaluation_score === 'number' ? node.evaluation_score : null,
            retryCount: node.retry_count,
            modelUsed: node.model_used || null,
            eventIds: node.event_ids,
        })),
        edges: snapshot.edges.map((edge) => ({
            id: edge.id,
            fromId: edge.from_id,
            toId: edge.to_id,
            label: edge.label,
            status: normalizeSeverity(edge.status),
        })),
    };
}

function mapWorkspaceReplaySnapshot(snapshot: ChatWorkspaceReplayResponse): ReplaySnapshotState {
    return {
        sessionId: snapshot.session_id,
        summary: snapshot.summary,
        currentIndex: snapshot.current_index,
        startedAt: snapshot.started_at ? new Date(snapshot.started_at) : null,
        endedAt: snapshot.ended_at ? new Date(snapshot.ended_at) : null,
        totalDurationMs: snapshot.total_duration_ms ?? null,
        frames: snapshot.frames.map((frame) => ({
            id: frame.id,
            index: frame.index,
            type: frame.type,
            description: frame.description,
            timestamp: new Date(frame.timestamp),
            severity: normalizeSeverity(frame.severity),
            roomId: frame.room_id || null,
            roomTitle: frame.room_title || null,
            agentName: frame.agent_name || null,
            relatedMessageId: frame.related_message_id || null,
            focusNodeIds: frame.focus_node_ids,
            focusEdgeId: frame.focus_edge_id || null,
        })),
    };
}

function mapWorkspaceGraphNode(
    node: ChatWorkspaceResponse['graph_nodes'][number]
): GraphNodeState {
    return {
        id: node.id,
        label: node.label,
        kind: node.kind,
        status: normalizeRoomStatus(node.status),
        x: clampGraphCoordinate(node.x),
        y: clampGraphCoordinate(node.y),
    };
}

function mapWorkspaceGraphEdge(
    edge: ChatWorkspaceResponse['graph_edges'][number]
): GraphEdgeState {
    return {
        id: edge.id,
        fromId: edge.from_id,
        toId: edge.to_id,
        label: edge.label,
        status: normalizeSeverity(edge.status),
    };
}

function mapWorkspaceRoomTimelineItem(
    item: ChatWorkspaceResponse['room_timeline'][number]
): RoomTimelineItemState {
    return {
        id: item.id,
        roomId: item.room_id,
        roomTitle: item.room_title || null,
        type: item.type,
        description: item.description,
        timestamp: new Date(item.timestamp),
        severity: normalizeSeverity(item.severity),
    };
}

function buildFallbackGraphNodes(
    rooms: OfficeRoom[],
    assignedAgentLabel: string | null
): GraphNodeState[] {
    const positions: Record<string, { x: number; y: number; kind: string }> = {
        front_desk: { x: 0.08, y: 0.18, kind: 'intake' },
        strategy: { x: 0.34, y: 0.2, kind: 'room' },
        boss: { x: 0.74, y: 0.12, kind: 'room' },
        voting: { x: 0.74, y: 0.38, kind: 'room' },
        collaboration: { x: 0.5, y: 0.48, kind: 'room' },
        memory: { x: 0.26, y: 0.68, kind: 'room' },
        incubator: { x: 0.74, y: 0.7, kind: 'room' },
        execution: { x: 0.48, y: 0.76, kind: 'room' },
        assigned_agent: { x: 0.5, y: 0.9, kind: 'agent' },
    };

    return [
        {
            id: 'front_desk',
            label: 'Front Desk',
            kind: 'intake',
            status: 'active',
            x: positions.front_desk.x,
            y: positions.front_desk.y,
        },
        ...rooms.map((room) => ({
            id: room.id,
            label: room.title,
            kind: positions[room.id]?.kind || 'room',
            status: room.status,
            x: positions[room.id]?.x ?? 0.5,
            y: positions[room.id]?.y ?? 0.5,
        })),
        {
            id: 'assigned_agent',
            label: assignedAgentLabel || 'Assigned Agent',
            kind: 'agent',
            status: rooms.find((room) => room.id === 'execution')?.status || 'watching',
            x: positions.assigned_agent.x,
            y: positions.assigned_agent.y,
        },
    ];
}

function buildFallbackGraphEdges(latestRouting: RoutingMetadata | null): GraphEdgeState[] {
    const edges: GraphEdgeState[] = [
        {
            id: 'edge:intake',
            fromId: 'front_desk',
            toId: 'strategy',
            label: 'TASK_STARTED',
            status: 'success',
        },
        {
            id: 'edge:route',
            fromId: 'strategy',
            toId: 'execution',
            label: 'AGENT_ASSIGNED',
            status: 'success',
        },
    ];

    if (latestRouting?.startProjectMode) {
        edges.push({
            id: 'edge:project',
            fromId: 'strategy',
            toId: 'collaboration',
            label: 'PROJECT_MODE',
            status: 'info',
        });
    }

    if (latestRouting?.source === 'executive_router') {
        edges.push({
            id: 'edge:executive',
            fromId: 'strategy',
            toId: 'boss',
            label: 'EXECUTIVE_ROUTER',
            status: 'warning',
        });
    }

    return edges;
}

function buildGraphEdgeStyle(
    fromNode: GraphNodeState,
    toNode: GraphNodeState
): React.CSSProperties {
    const fromX = fromNode.x * 100;
    const fromY = fromNode.y * 100;
    const deltaX = (toNode.x - fromNode.x) * 100;
    const deltaY = (toNode.y - fromNode.y) * 100;
    const width = Math.sqrt((deltaX ** 2) + (deltaY ** 2));
    const angle = Math.atan2(deltaY, deltaX);

    return {
        left: `${fromX}%`,
        top: `${fromY}%`,
        width: `${width}%`,
        transform: `translateY(-50%) rotate(${angle}rad)`,
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

function clampGraphCoordinate(value: number): number {
    if (!Number.isFinite(value)) {
        return 0.5;
    }

    return Math.min(0.95, Math.max(0.05, value));
}

function isOfficeRoomId(value: string | null | undefined): value is OfficeRoomId {
    return value === 'strategy'
        || value === 'boss'
        || value === 'voting'
        || value === 'collaboration'
        || value === 'memory'
        || value === 'incubator'
        || value === 'execution';
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

function formatDurationMs(value: number | null | undefined): string | null {
    if (typeof value !== 'number' || value < 0) {
        return null;
    }
    if (value < 1000) {
        return `${value} ms`;
    }

    const seconds = value / 1000;
    if (seconds < 60) {
        return `${seconds >= 10 ? seconds.toFixed(0) : seconds.toFixed(1)} s`;
    }

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
}

function formatEvaluationScore(value: number | null | undefined): string {
    if (typeof value !== 'number') {
        return 'Not captured';
    }
    return `${Math.round(value * 100)}%`;
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
