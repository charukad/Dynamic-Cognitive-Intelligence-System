import { create } from 'zustand';
import { Agent, Task } from '@/types/agent';

// Re-export types for external use
export type { Agent, Task } from '@/types/agent';

type AgentStatus = Agent['status'];

interface SwarmStore {
    agents: Agent[];
    tasks: Task[];
    selectedAgentId: string | null;

    // Actions
    setAgents: (agents: Agent[]) => void;
    updateAgent: (id: string, updates: Partial<Agent>) => void;
    selectAgent: (id: string | null) => void;
    addAgent: (agent: Agent) => void;
    removeAgent: (id: string) => void;
    updateAgentStatus: (id: string, status: string) => void;
    clearSwarm: () => void;
    addTask: (task: Task) => void;
    updateTask: (id: string, updates: Partial<Task>) => void;
}

export const useSwarmStore = create<SwarmStore>((set) => ({
    agents: [],
    tasks: [],
    selectedAgentId: null,

    setAgents: (agents) => set({ agents }),

    updateAgent: (id, updates) => set((state) => ({
        agents: state.agents.map((agent) =>
            agent.id === id ? { ...agent, ...updates } : agent
        ),
    })),

    selectAgent: (id) => set({ selectedAgentId: id }),

    addTask: (task) => set((state) => ({
        tasks: [...state.tasks, task]
    })),

    updateTask: (id, updates) => set((state) => ({
        tasks: state.tasks.map((task) =>
            task.id === id ? { ...task, ...updates } : task
        ),
    })),

    addAgent: (agent) => set((state) => {
        // Prevent duplicates
        if (state.agents.some(a => a.id === agent.id)) {
            return state;
        }
        return { agents: [...state.agents, agent] };
    }),

    removeAgent: (id) => set((state) => ({
        agents: state.agents.filter((agent) => agent.id !== id)
    })),

    updateAgentStatus: (id, status) => set((state) => ({
        agents: state.agents.map((agent) =>
            agent.id === id ? { ...agent, status: status as AgentStatus } : agent
        ),
    })),

    clearSwarm: () => set({ agents: [] }),
}));
