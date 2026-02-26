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

export interface Task {
    id: string;
    title?: string;
    description: string;
    agentId?: string;
    assignedTo?: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    createdAt?: number;
    completedAt?: number;
    result?: string;
    subtasks?: Task[];
}
