import { create } from 'zustand';
import { GraphData, GraphNode, GraphLink } from '@/types/graph';

interface GraphStore {
    data: GraphData;
    hoveredNode: string | null;

    // Actions
    setData: (data: GraphData) => void;
    setHoveredNode: (id: string | null) => void;
    generateMockData: (count?: number) => void;
}

export const useGraphStore = create<GraphStore>((set) => ({
    data: { nodes: [], links: [] },
    hoveredNode: null,

    setData: (data) => set({ data }),
    setHoveredNode: (id) => set({ hoveredNode: id }),

    generateMockData: (count = 100) => {
        const nodes: GraphNode[] = [];
        const links: GraphLink[] = [];

        // 1. Central "DCIS" Node
        nodes.push({ id: 'DCIS', name: 'DCIS', group: 'entity', val: 20 });

        // 2. Generate random nodes
        const groups = ['concept', 'entity', 'action'] as const;

        for (let i = 1; i < count; i++) {
            nodes.push({
                id: `node-${i}`,
                name: `Concept ${i}`,
                group: groups[Math.floor(Math.random() * groups.length)],
                val: Math.random() * 5 + 1
            });

            // 3. Connect to random existing nodes (prefer DCIS)
            const target = Math.random() > 0.7 ? 'DCIS' : nodes[Math.floor(Math.random() * i)].id;

            links.push({
                source: `node-${i}`,
                target: target,
                value: 1
            });
        }

        set({ data: { nodes, links } });
    }
}));
