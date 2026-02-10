export interface GraphNode {
    id: string;
    name: string;
    group: 'concept' | 'entity' | 'action'; // Determines color
    val: number; // Size
    // Simulation props (filled by d3)
    x?: number;
    y?: number;
    z?: number;
    vx?: number;
    vy?: number;
    vz?: number;
}

export interface GraphLink {
    source: string | GraphNode;
    target: string | GraphNode;
    value: number; // Thickness/Strength
}

export interface GraphData {
    nodes: GraphNode[];
    links: GraphLink[];
}
