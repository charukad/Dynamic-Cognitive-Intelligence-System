import { beforeEach, describe, expect, it } from 'vitest';

import { selectCurrentMessages, useChatStore } from '../chatStore';

const sessionA = {
    id: 'session-a',
    title: 'Session A',
    status: 'active',
    selected_agent_id: 'designer',
    message_count: 0,
    last_message: '',
    last_message_at: null,
    metadata: {},
    created_at: '2026-02-27T00:00:00.000Z',
    updated_at: '2026-02-27T00:00:00.000Z',
};

const sessionB = {
    id: 'session-b',
    title: 'Session B',
    status: 'active',
    selected_agent_id: 'coder',
    message_count: 0,
    last_message: '',
    last_message_at: null,
    metadata: {},
    created_at: '2026-02-26T00:00:00.000Z',
    updated_at: '2026-02-26T00:00:00.000Z',
};

describe('ChatStore', () => {
    beforeEach(() => {
        useChatStore.getState().reset();
    });

    it('stores sessions and defaults current session to the newest entry', () => {
        useChatStore.getState().setSessions([sessionB, sessionA]);

        const state = useChatStore.getState();
        expect(state.sessions.map((session) => session.id)).toEqual(['session-a', 'session-b']);
        expect(state.currentSessionId).toBe('session-a');
    });

    it('keeps optimistic and reconciled messages in order for the active session', () => {
        const store = useChatStore.getState();
        store.setSessions([sessionA]);
        store.addOptimisticUserMessage('session-a', {
            id: 'user-1',
            sessionId: 'session-a',
            sender: 'user',
            role: 'user',
            content: 'Hello',
            timestamp: new Date('2026-02-27T12:00:00.000Z'),
            status: 'sending',
        });

        store.upsertMessage('session-a', {
            id: 'assistant-1',
            sessionId: 'session-a',
            sender: 'agent',
            role: 'assistant',
            content: 'Hi there',
            timestamp: new Date('2026-02-27T12:00:01.000Z'),
            status: 'delivered',
            agentId: 'designer',
            agentName: 'Designer',
        });

        const messages = selectCurrentMessages(useChatStore.getState());
        expect(messages).toHaveLength(2);
        expect(messages[0].content).toBe('Hello');
        expect(messages[1].content).toBe('Hi there');
        expect(useChatStore.getState().sessions[0].last_message).toBe('Hi there');
    });

    it('reconciles streaming chunks into a single assistant message', () => {
        const store = useChatStore.getState();
        store.setSessions([sessionA]);

        store.appendStreamChunk('session-a', 'assistant-1', 'Hello', 'designer', 'Designer');
        store.appendStreamChunk('session-a', 'assistant-1', ' world', 'designer', 'Designer');
        store.finalizeStreamMessage('session-a', 'assistant-1');

        const messages = selectCurrentMessages(useChatStore.getState());
        expect(messages).toHaveLength(1);
        expect(messages[0].content).toBe('Hello world');
        expect(messages[0].status).toBe('delivered');
        expect(messages[0].isStreaming).toBe(false);
    });

    it('updates the latest pending user message status', () => {
        const store = useChatStore.getState();
        store.setSessions([sessionA]);
        store.addOptimisticUserMessage('session-a', {
            id: 'user-1',
            sessionId: 'session-a',
            sender: 'user',
            role: 'user',
            content: 'First',
            timestamp: new Date('2026-02-27T12:00:00.000Z'),
            status: 'delivered',
        });
        store.addOptimisticUserMessage('session-a', {
            id: 'user-2',
            sessionId: 'session-a',
            sender: 'user',
            role: 'user',
            content: 'Second',
            timestamp: new Date('2026-02-27T12:01:00.000Z'),
            status: 'sent',
        });

        store.markLatestPendingUserMessage('session-a', 'error');

        const messages = selectCurrentMessages(useChatStore.getState());
        expect(messages[0].status).toBe('delivered');
        expect(messages[1].status).toBe('error');
    });

    it('removes session data and advances the current session when deleting the active session', () => {
        const store = useChatStore.getState();
        store.setSessions([sessionA, sessionB]);
        store.setCurrentSessionId('session-a');
        store.removeSession('session-a');

        const state = useChatStore.getState();
        expect(state.sessions.map((session) => session.id)).toEqual(['session-b']);
        expect(state.currentSessionId).toBe('session-b');
        expect(state.messagesBySession['session-a']).toBeUndefined();
    });

    it('tracks reconnect attempts and recoverable errors', () => {
        const store = useChatStore.getState();

        store.setReconnectAttempt(2);
        store.setError({
            code: 'websocket_disconnected',
            message: 'Realtime connection lost',
            recoverable: true,
        });

        let state = useChatStore.getState();
        expect(state.reconnectAttempt).toBe(2);
        expect(state.lastError?.recoverable).toBe(true);

        store.clearError();
        state = useChatStore.getState();
        expect(state.lastError).toBeNull();
    });

    it('tracks session loading independently from bootstrap state', () => {
        const store = useChatStore.getState();

        store.setBootstrapping(true);
        store.setSessionLoading(true);

        let state = useChatStore.getState();
        expect(state.isBootstrapping).toBe(true);
        expect(state.isSessionLoading).toBe(true);

        store.setBootstrapping(false);
        store.setSessionLoading(false);

        state = useChatStore.getState();
        expect(state.isBootstrapping).toBe(false);
        expect(state.isSessionLoading).toBe(false);
    });
});
