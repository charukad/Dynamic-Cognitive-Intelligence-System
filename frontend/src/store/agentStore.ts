import { create } from 'zustand';
import { Agent, AgentStore } from '../types/agent';

export const useAgentStore = create<AgentStore>((set, get) => ({
    agents: {},
    activeAgentId: null,

    addAgent: (agent) =>
        set((state) => ({
            agents: { ...state.agents, [agent.id]: agent }
        })),

    updateAgent: (id, updates) =>
        set((state) => ({
            agents: {
                ...state.agents,
                [id]: { ...state.agents[id], ...updates }
            }
        })),

    setActiveAgent: (id) => set({ activeAgentId: id }),

    getAgent: (id) => get().agents[id],
}));
