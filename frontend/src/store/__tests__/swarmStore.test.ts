import { describe, it, expect, beforeEach } from 'vitest';
import { useSwarmStore } from '../swarmStore';
import type { Agent } from '../swarmStore';

describe('SwarmStore', () => {
    beforeEach(() => {
        // Reset store state
        const store = useSwarmStore.getState();
        store.agents = [];
    });

    const mockAgent: Agent = {
        id: 'agent-1',
        name: 'Logician',
        role: 'logician',
        status: 'idle',
        model: 'gpt-4',
        temperature: 0.7,
        tokensUsed: 0
    };

    describe('addAgent', () => {
        it('should add a new agent to the swarm', () => {
            const { addAgent } = useSwarmStore.getState();

            addAgent(mockAgent);

            expect(useSwarmStore.getState().agents).toHaveLength(1);
            expect(useSwarmStore.getState().agents[0]).toEqual(mockAgent);
        });

        it('should not add duplicate agents', () => {
            const { addAgent } = useSwarmStore.getState();

            addAgent(mockAgent);
            addAgent(mockAgent);

            expect(useSwarmStore.getState().agents).toHaveLength(1);
        });

        it('should add multiple different agents', () => {
            const { addAgent } = useSwarmStore.getState();

            const agent2: Agent = { ...mockAgent, id: 'agent-2', name: 'Creative' };

            addAgent(mockAgent);
            addAgent(agent2);

            expect(useSwarmStore.getState().agents).toHaveLength(2);
        });
    });

    describe('removeAgent', () => {
        it('should remove an agent by ID', () => {
            const { addAgent, removeAgent } = useSwarmStore.getState();

            addAgent(mockAgent);
            expect(useSwarmStore.getState().agents).toHaveLength(1);

            removeAgent('agent-1');
            expect(useSwarmStore.getState().agents).toHaveLength(0);
        });

        it('should not error when removing non-existent agent', () => {
            const { removeAgent } = useSwarmStore.getState();

            expect(() => removeAgent('non-existent')).not.toThrow();
        });
    });

    describe('updateAgentStatus', () => {
        it('should update agent status', () => {
            const { addAgent, updateAgentStatus } = useSwarmStore.getState();

            addAgent(mockAgent);
            updateAgentStatus('agent-1', 'thinking');

            const updatedAgent = useSwarmStore.getState().agents[0];
            expect(updatedAgent.status).toBe('thinking');
        });

        it('should not affect other agents', () => {
            const { addAgent, updateAgentStatus } = useSwarmStore.getState();

            const agent2: Agent = { ...mockAgent, id: 'agent-2', name: 'Creative' };

            addAgent(mockAgent);
            addAgent(agent2);

            updateAgentStatus('agent-1', 'thinking');

            const agents = useSwarmStore.getState().agents;
            expect(agents[0].status).toBe('thinking');
            expect(agents[1].status).toBe('idle');
        });
    });

    describe('clearSwarm', () => {
        it('should remove all agents', () => {
            const { addAgent, clearSwarm } = useSwarmStore.getState();

            addAgent(mockAgent);
            addAgent({ ...mockAgent, id: 'agent-2' });

            expect(useSwarmStore.getState().agents).toHaveLength(2);

            clearSwarm();

            expect(useSwarmStore.getState().agents).toHaveLength(0);
        });
    });
});
