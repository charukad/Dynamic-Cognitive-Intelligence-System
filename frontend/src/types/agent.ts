export interface Agent {
    id: string;
    name: string;
    description: string;
    capabilities: string[];
    status?: 'active' | 'idle' | 'error';
    lastActive?: number;
    tasksCompleted?: number;
    currentTask?: string;
}

export interface AgentStore {
    agents: Record<string, Agent>;
    activeAgentId: string | null;
    addAgent: (agent: Agent) => void;
    updateAgent: (id: string, updates: Partial<Agent>) => void;
    setActiveAgent: (id: string) => void;
    getAgent: (id: string) => Agent | undefined;
}
