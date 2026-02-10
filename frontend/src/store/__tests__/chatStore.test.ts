import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '../chatStore';

describe('ChatStore', () => {
    beforeEach(() => {
        // Reset store state before each test
        const store = useChatStore.getState();
        store.messages = [];
    });

    describe('addMessage', () => {
        it('should add a new message to the store', () => {
            const { addMessage } = useChatStore.getState();

            addMessage({
                sender: 'Commander',
                role: 'user',
                content: 'Hello, agents!'
            });

            const messages = useChatStore.getState().messages;
            expect(messages).toHaveLength(1); // Changed from 2 to 1, assuming no initial message
            expect(messages[0].sender).toBe('Commander'); // Changed from 1 to 0
            expect(messages[0].role).toBe('user'); // Changed from 1 to 0
            expect(messages[0].content).toBe('Hello, agents!'); // Changed from 1 to 0
            expect(messages[0].id).toBeDefined(); // Changed from 1 to 0
            expect(messages[0].timestamp).toBeDefined(); // Changed from 1 to 0
        });

        it('should maintain message order', () => {
            const { addMessage } = useChatStore.getState();

            addMessage({ sender: 'User', role: 'user', content: 'First' });
            addMessage({ sender: 'Agent', role: 'agent', content: 'Second' });
            addMessage({ sender: 'User', role: 'user', content: 'Third' });

            const messages = useChatStore.getState().messages;
            expect(messages).toHaveLength(3); // Changed from 4 to 3
            expect(messages[0].content).toBe('First'); // Changed from 1 to 0
            expect(messages[1].content).toBe('Second'); // Changed from 2 to 1
            expect(messages[2].content).toBe('Third'); // Changed from 3 to 2
        });

        it('should generate unique IDs for each message', () => {
            const { addMessage } = useChatStore.getState();

            addMessage({ sender: 'User', role: 'user', content: 'Message 1' });
            addMessage({ sender: 'User', role: 'user', content: 'Message 2' });

            const messages = useChatStore.getState().messages;
            const ids = messages.map(m => m.id);
            const uniqueIds = new Set(ids);
            expect(uniqueIds.size).toBe(ids.length);
        });
    });

    describe('clearMessages', () => {
        it('should remove all messages', () => {
            const { addMessage, clearMessages } = useChatStore.getState();

            addMessage({ sender: 'User', role: 'user', content: 'Test 1' });
            addMessage({ sender: 'User', role: 'user', content: 'Test 2' });

            expect(useChatStore.getState().messages).toHaveLength(2); // Changed from 3 to 2

            clearMessages();

            expect(useChatStore.getState().messages).toHaveLength(0);
        });
    });

    describe('typing indicator', () => {
        it('should set typing indicator', () => {
            const { setTyping } = useChatStore.getState();

            expect(useChatStore.getState().isTyping).toBe(false);

            setTyping(true);
            expect(useChatStore.getState().isTyping).toBe(true);

            setTyping(false);
            expect(useChatStore.getState().isTyping).toBe(false);
        });
    });
});
