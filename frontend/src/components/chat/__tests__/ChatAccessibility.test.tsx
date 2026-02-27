import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import ChatHistorySidebar from '../ChatHistorySidebar';
import { ChatInterface } from '../ChatInterface';
import { useChatStore } from '@/store/chatStore';

const listChatSessions = vi.fn();
const createChatSession = vi.fn();
const getChatWorkspace = vi.fn();
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
    working_context: {},
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
