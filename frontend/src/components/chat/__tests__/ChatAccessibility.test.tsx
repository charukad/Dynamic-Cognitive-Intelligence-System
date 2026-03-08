import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import ChatHistorySidebar from '../ChatHistorySidebar';
import { ChatInterface } from '../ChatInterface';
import { useChatStore } from '@/store/chatStore';

const listChatSessions = vi.fn();
const createChatSession = vi.fn();
const getChatWorkspace = vi.fn();
const getChatWorkspaceRoom = vi.fn();
const getChatWorkspaceDag = vi.fn();
const getChatWorkspaceReplay = vi.fn();
const getChatSession = vi.fn();
const listChatMessages = vi.fn();
const sendChatMessage = vi.fn();
const upsertChatFeedback = vi.fn();
const deleteChatSession = vi.fn();

vi.mock('framer-motion', () => ({
    AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    useReducedMotion: () => false,
    motion: {
        div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement> & Record<string, unknown>) => {
            const {
                initial,
                animate,
                exit,
                transition,
                whileHover,
                whileTap,
                ...domProps
            } = props;
            void initial;
            void animate;
            void exit;
            void transition;
            void whileHover;
            void whileTap;
            return <div {...domProps}>{children}</div>;
        },
        button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & Record<string, unknown>) => {
            const {
                initial,
                animate,
                exit,
                transition,
                whileHover,
                whileTap,
                ...domProps
            } = props;
            void initial;
            void animate;
            void exit;
            void transition;
            void whileHover;
            void whileTap;
            return <button {...domProps}>{children}</button>;
        },
        aside: ({ children, ...props }: React.HTMLAttributes<HTMLElement> & Record<string, unknown>) => {
            const {
                initial,
                animate,
                exit,
                transition,
                whileHover,
                whileTap,
                ...domProps
            } = props;
            void initial;
            void animate;
            void exit;
            void transition;
            void whileHover;
            void whileTap;
            return <aside {...domProps}>{children}</aside>;
        },
    },
}));

vi.mock('react-markdown', () => ({
    default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('react-syntax-highlighter', () => ({
    Prism: ({ children }: { children: React.ReactNode }) => <pre>{children}</pre>,
}));

vi.mock('react-syntax-highlighter/dist/esm/styles/prism', () => ({
    vscDarkPlus: {},
}));

vi.mock('@/lib/chatApi', () => ({
    listChatSessions: (...args: unknown[]) => listChatSessions(...args),
    createChatSession: (...args: unknown[]) => createChatSession(...args),
    getChatWorkspace: (...args: unknown[]) => getChatWorkspace(...args),
    getChatWorkspaceRoom: (...args: unknown[]) => getChatWorkspaceRoom(...args),
    getChatWorkspaceDag: (...args: unknown[]) => getChatWorkspaceDag(...args),
    getChatWorkspaceReplay: (...args: unknown[]) => getChatWorkspaceReplay(...args),
    getChatSession: (...args: unknown[]) => getChatSession(...args),
    deleteChatSession: (...args: unknown[]) => deleteChatSession(...args),
    listChatMessages: (...args: unknown[]) => listChatMessages(...args),
    sendChatMessage: (...args: unknown[]) => sendChatMessage(...args),
    upsertChatFeedback: (...args: unknown[]) => upsertChatFeedback(...args),
}));

class MockWebSocket {
    static CONNECTING = 0;
    static OPEN = 1;
    static CLOSING = 2;
    static CLOSED = 3;

    readyState = MockWebSocket.CLOSED;
    onopen: ((event: Event) => void) | null = null;
    onclose: ((event: CloseEvent) => void) | null = null;
    onerror: ((event: Event) => void) | null = null;
    onmessage: ((event: MessageEvent<string>) => void) | null = null;
    send = vi.fn();
    close = vi.fn(() => {
        this.readyState = MockWebSocket.CLOSED;
        this.onclose?.(new CloseEvent('close'));
    });

    constructor(public readonly url: string) { }
}

const session = {
    id: 'session-1',
    title: 'New Conversation',
    status: 'active',
    selected_agent_id: null,
    message_count: 0,
    last_message: '',
    last_message_at: null,
    metadata: {},
    created_at: '2026-02-27T10:00:00.000Z',
    updated_at: '2026-02-27T10:00:00.000Z',
};

const sessionTwo = {
    ...session,
    id: 'session-2',
    title: 'Bug triage',
    selected_agent_id: 'coder',
    created_at: '2026-02-27T09:00:00.000Z',
    updated_at: '2026-02-27T09:30:00.000Z',
};

const workspace = {
    session,
    route: {
        source: 'explicit',
        reason: 'Manual agent selection was provided.',
        inferred_task_type: 'creative',
        inferred_agent_type: 'designer',
        mode: 'balanced',
        start_project_mode: false,
    },
    rooms: [
        {
            id: 'strategy',
            title: 'Strategy Center',
            label: 'Planning Room',
            status: 'watching',
            detail: 'Incoming requests route here first.',
            metric: 'creative',
            description: 'Task decomposition and routing view.',
        },
    ],
    activity_feed: [
        {
            id: 'evt-1',
            type: 'TASK_STARTED',
            description: 'User request entered the office workflow.',
            timestamp: '2026-02-27T10:00:00.000Z',
            severity: 'info',
        },
    ],
    office_stats: [
        {
            label: 'Persisted Messages',
            value: '0',
            hint: 'Saved turns in this session',
        },
    ],
    task_stages: [
        {
            id: 'intake',
            title: 'Front Desk Intake',
            status: 'waiting',
            detail: 'Waiting for the first request.',
        },
    ],
    replay: [],
    graph_nodes: [],
    graph_edges: [],
    room_timeline: [],
    working_context: {},
};

const roomDetail = {
    room: workspace.rooms[0],
    summary: 'Strategy Center is preparing the latest route plan.',
    metrics: [
        {
            label: 'Route Source',
            value: 'Manual Selection',
            hint: 'Manual agent selection was provided.',
        },
    ],
    highlights: [
        'Task type: creative',
    ],
    recent_events: [
        {
            id: 'evt-1',
            room_id: 'strategy',
            room_title: 'Strategy Center',
            type: 'TASK_STARTED',
            description: 'User request entered the office workflow.',
            timestamp: '2026-02-27T10:00:00.000Z',
            severity: 'info',
        },
    ],
    related_messages: [
        {
            id: 'msg-1',
            role: 'user',
            sender: 'user',
            content: 'Design a cleaner navigation system',
            status: 'completed',
            agent_name: null,
            created_at: '2026-02-27T10:00:00.000Z',
        },
    ],
    actions: [
        'Open task DAG viewer',
    ],
};

const dagDetail = {
    session_id: 'session-1',
    summary: 'Designer completed the latest delivery path.',
    latest_node_id: 'delivery',
    total_duration_ms: 2200,
    nodes: [
        {
            id: 'routing',
            title: 'Routing and Planning',
            room_id: 'strategy',
            status: 'done',
            detail: 'Manual agent selection was provided.',
            dependencies: ['intake'],
            started_at: '2026-02-27T10:00:00.000Z',
            completed_at: '2026-02-27T10:00:01.000Z',
            execution_time_ms: 120,
            assigned_agent: 'Designer',
            evaluation_score: null,
            retry_count: 0,
            model_used: null,
            event_ids: ['evt-1'],
        },
        {
            id: 'delivery',
            title: 'Delivery and Validation',
            room_id: 'execution',
            status: 'done',
            detail: 'Latest response delivered successfully.',
            dependencies: ['execution'],
            started_at: '2026-02-27T10:00:02.000Z',
            completed_at: '2026-02-27T10:00:04.000Z',
            execution_time_ms: 840,
            assigned_agent: 'Designer',
            evaluation_score: 1,
            retry_count: 0,
            model_used: 'demo-model',
            event_ids: ['evt-2'],
        },
    ],
    edges: [
        {
            id: 'execution:delivery',
            from_id: 'execution',
            to_id: 'delivery',
            label: 'depends_on',
            status: 'success',
        },
    ],
};

const replayDetail = {
    session_id: 'session-1',
    summary: 'Designer completed the response and returned it to the front desk.',
    current_index: 1,
    started_at: '2026-02-27T10:00:00.000Z',
    ended_at: '2026-02-27T10:00:04.000Z',
    total_duration_ms: 1800,
    frames: [
        {
            id: 'evt-1',
            index: 0,
            type: 'TASK_STARTED',
            description: 'User request entered the office workflow.',
            timestamp: '2026-02-27T10:00:00.000Z',
            severity: 'info',
            room_id: 'strategy',
            room_title: 'Strategy Center',
            agent_name: 'Designer',
            related_message_id: 'msg-1',
            focus_node_ids: ['strategy', 'front_desk'],
            focus_edge_id: 'front_desk:strategy:TASK_STARTED',
        },
        {
            id: 'evt-2',
            index: 1,
            type: 'FINAL_RESPONSE_SENT',
            description: 'Designer completed the response and returned it to the front desk.',
            timestamp: '2026-02-27T10:00:04.000Z',
            severity: 'success',
            room_id: 'execution',
            room_title: 'Active Pods',
            agent_name: 'Designer',
            related_message_id: 'msg-2',
            focus_node_ids: ['execution', 'front_desk'],
            focus_edge_id: 'execution:front_desk:FINAL_RESPONSE_SENT',
        },
    ],
};

describe('Chat accessibility', () => {
    beforeEach(() => {
        useChatStore.getState().reset();
        vi.clearAllMocks();
        HTMLElement.prototype.scrollIntoView = vi.fn();
        vi.stubGlobal('WebSocket', MockWebSocket);
        vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify([
            {
                id: 'designer',
                name: 'Designer',
                description: 'UI and UX specialist',
            },
        ]), {
            status: 200,
            headers: {
                'Content-Type': 'application/json',
            },
        })));

        listChatSessions.mockResolvedValue([]);
        createChatSession.mockResolvedValue(session);
        getChatWorkspace.mockResolvedValue(workspace);
        getChatWorkspaceRoom.mockResolvedValue(roomDetail);
        getChatWorkspaceDag.mockResolvedValue(dagDetail);
        getChatWorkspaceReplay.mockResolvedValue(replayDetail);
        getChatSession.mockResolvedValue(session);
        listChatMessages.mockResolvedValue([]);
        sendChatMessage.mockImplementation(async (sessionId: string, payload: { id: string; content: string; agent_id?: string | null }) => ({
            session: {
                ...session,
                id: sessionId,
                selected_agent_id: payload.agent_id || null,
                last_message: payload.content,
                last_message_at: '2026-02-27T10:05:00.000Z',
                updated_at: '2026-02-27T10:05:00.000Z',
                message_count: 2,
            },
            user_message: {
                id: payload.id,
                session_id: sessionId,
                sequence_number: 1,
                role: 'user',
                sender: 'user',
                content: payload.content,
                status: 'completed',
                metadata: {},
                created_at: '2026-02-27T10:05:00.000Z',
                updated_at: '2026-02-27T10:05:00.000Z',
            },
            assistant_message: {
                id: 'assistant-1',
                session_id: sessionId,
                sequence_number: 2,
                role: 'assistant',
                sender: 'agent',
                content: 'Acknowledged.',
                status: 'completed',
                agent_id: payload.agent_id || 'designer',
                agent_name: 'Designer',
                metadata: {},
                created_at: '2026-02-27T10:05:01.000Z',
                updated_at: '2026-02-27T10:05:01.000Z',
            },
        }));
        deleteChatSession.mockResolvedValue(undefined);
        vi.stubGlobal('confirm', vi.fn(() => true));
    });

    it('supports accessible composer controls and Enter-to-send keyboard behavior', async () => {
        render(<ChatInterface embedded />);

        const composer = await screen.findByRole('textbox', { name: 'Message composer' });
        await waitFor(() => {
            expect(screen.getByRole('button', { name: /send message to designer/i })).toBeInTheDocument();
        });
        const sendButton = screen.getByRole('button', { name: /send message to designer/i });
        fireEvent.click(screen.getByRole('tab', { name: 'High Accuracy' }));
        fireEvent.click(screen.getByRole('button', { name: /start project mode/i }));

        expect(screen.getByRole('log')).toBeInTheDocument();
        expect(composer).toHaveAttribute('aria-describedby');
        expect(sendButton).toBeDisabled();

        fireEvent.change(composer, { target: { value: 'Line one' } });
        fireEvent.keyDown(composer, { key: 'Enter', shiftKey: true });
        expect(sendChatMessage).not.toHaveBeenCalled();
        expect(composer).toHaveValue('Line one');

        fireEvent.change(composer, { target: { value: 'Send this' } });
        fireEvent.keyDown(composer, { key: 'Enter' });

        await waitFor(() => {
            expect(sendChatMessage).toHaveBeenCalledTimes(1);
        });

        expect(sendChatMessage).toHaveBeenCalledWith(
            'session-1',
            expect.objectContaining({
                content: 'Send this',
                agent_id: 'designer',
                metadata: expect.objectContaining({
                    mode: 'high_accuracy',
                    start_project_mode: true,
                }),
            })
        );
    });

    it('opens a room detail drawer backed by the room-detail API', async () => {
        render(<ChatInterface embedded />);

        const roomButton = await screen.findByRole('button', { name: /strategy center/i });
        fireEvent.click(roomButton);

        await waitFor(() => {
            expect(getChatWorkspaceRoom).toHaveBeenCalledWith('session-1', 'strategy');
        });

        expect(await screen.findByRole('dialog', { name: /strategy center detail panel/i })).toBeInTheDocument();
        expect(screen.getByText('Strategy Center is preparing the latest route plan.')).toBeInTheDocument();
        expect(screen.getByText('Open task DAG viewer')).toBeInTheDocument();
    });

    it('loads the DAG viewer and replay controls from dedicated workspace APIs', async () => {
        render(<ChatInterface embedded />);

        fireEvent.click(await screen.findByRole('tab', { name: 'Task DAG Viewer' }));

        await waitFor(() => {
            expect(getChatWorkspaceDag).toHaveBeenCalledWith('session-1');
        });

        expect(await screen.findByText('Designer completed the latest delivery path.')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: /delivery and validation/i }));
        await waitFor(() => {
            expect(screen.getByText('demo-model')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('tab', { name: 'Replay' }));

        await waitFor(() => {
            expect(getChatWorkspaceReplay).toHaveBeenCalledWith('session-1');
        });

        const scrubber = await screen.findByLabelText('Replay frame scrubber');
        expect(scrubber).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Rewind replay to the first frame' }));
        fireEvent.click(screen.getByRole('button', { name: 'Step forward in replay' }));
        expect(scrubber).toHaveValue('1');
    }, 15000);

    it('switches sessions and reloads the persisted message timeline', async () => {
        listChatSessions.mockResolvedValue([session, sessionTwo]);
        listChatMessages.mockImplementation(async (sessionId: string) => (
            sessionId === 'session-2'
                ? [
                    {
                        id: 'assistant-session-2',
                        session_id: 'session-2',
                        sequence_number: 1,
                        role: 'assistant',
                        sender: 'agent',
                        content: 'Coder handled: Fix the failing retry logic',
                        status: 'completed',
                        agent_id: 'coder',
                        agent_name: 'Coder',
                        metadata: {},
                        created_at: '2026-02-27T09:31:00.000Z',
                        updated_at: '2026-02-27T09:31:00.000Z',
                    },
                ]
                : [
                    {
                        id: 'assistant-session-1',
                        session_id: 'session-1',
                        sequence_number: 1,
                        role: 'assistant',
                        sender: 'agent',
                        content: 'Designer handled: Architecture review',
                        status: 'completed',
                        agent_id: 'designer',
                        agent_name: 'Designer',
                        metadata: {},
                        created_at: '2026-02-27T10:01:00.000Z',
                        updated_at: '2026-02-27T10:01:00.000Z',
                    },
                ]
        ));

        render(<ChatInterface />);

        expect(await screen.findByText('Designer handled: Architecture review')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Open conversation Bug triage' }));

        await waitFor(() => {
            expect(listChatMessages).toHaveBeenCalledWith('session-2');
        });
        expect(await screen.findByText('Coder handled: Fix the failing retry logic')).toBeInTheDocument();
    });

    it('persists assistant feedback and updates the selected state', async () => {
        listChatSessions.mockResolvedValue([session]);
        listChatMessages.mockResolvedValue([
            {
                id: 'assistant-feedback',
                session_id: 'session-1',
                sequence_number: 1,
                role: 'assistant',
                sender: 'agent',
                content: 'Designer handled: Feedback request',
                status: 'completed',
                agent_id: 'designer',
                agent_name: 'Designer',
                metadata: {},
                created_at: '2026-02-27T10:01:00.000Z',
                updated_at: '2026-02-27T10:01:00.000Z',
            },
        ]);
        upsertChatFeedback.mockResolvedValue({
            id: 'feedback-1',
            session_id: 'session-1',
            message_id: 'assistant-feedback',
            agent_id: 'designer',
            feedback_type: 'thumbs_up',
            rating: 5,
            metadata: {},
            created_at: '2026-02-27T10:02:00.000Z',
            updated_at: '2026-02-27T10:02:00.000Z',
        });

        render(<ChatInterface embedded />);

        const feedbackButton = await screen.findByRole('button', { name: 'Mark assistant response as helpful' });
        fireEvent.click(feedbackButton);

        await waitFor(() => {
            expect(upsertChatFeedback).toHaveBeenCalledWith(expect.objectContaining({
                session_id: 'session-1',
                message_id: 'assistant-feedback',
                feedback_type: 'thumbs_up',
            }));
        });
        expect(feedbackButton).toHaveAttribute('aria-pressed', 'true');
    });

    it('deletes the active session and starts a replacement conversation', async () => {
        const onNewChat = vi.fn();
        const store = useChatStore.getState();
        store.setSessions([
            {
                ...session,
                id: 'session-a',
                title: 'Session A',
            },
            {
                ...sessionTwo,
                id: 'session-b',
                title: 'Session B',
            },
        ]);
        store.setCurrentSessionId('session-a');

        render(
            <ChatHistorySidebar
                onSessionSelect={vi.fn()}
                onNewChat={onNewChat}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: 'Delete conversation Session A' }));

        await waitFor(() => {
            expect(deleteChatSession).toHaveBeenCalledWith('session-a');
        });
        await waitFor(() => {
            expect(onNewChat).toHaveBeenCalledTimes(1);
        });
        expect(screen.queryByRole('button', { name: 'Open conversation Session A' })).not.toBeInTheDocument();
    });

    it('renders saved sessions as keyboard-accessible buttons', () => {
        const store = useChatStore.getState();
        store.setSessions([
            {
                ...session,
                id: 'session-a',
                title: 'Session A',
            },
            {
                ...session,
                id: 'session-b',
                title: 'Session B',
                updated_at: '2026-02-26T10:00:00.000Z',
                created_at: '2026-02-26T10:00:00.000Z',
            },
        ]);

        render(
            <ChatHistorySidebar
                onSessionSelect={vi.fn()}
                onNewChat={vi.fn()}
            />
        );

        expect(screen.getByRole('list', { name: 'Saved conversations' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Open conversation Session A' })).toHaveAttribute('aria-current', 'page');
        expect(screen.getByRole('button', { name: 'Open conversation Session B' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Delete conversation Session A' })).toBeInTheDocument();
    });
});
