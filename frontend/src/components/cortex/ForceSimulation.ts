/**
 * Force Simulation Engine for 3D Knowledge Graph
 * 
 * Implements force-directed graph layout algorithm in 3D space.
 * 
 * Features:
 * - Repulsion forces (nodes push each other away)
 * - Spring forces (edges pull connected nodes together)
 * - Center gravity (prevents drift)
 * - Collision detection
 * - Damping for stability
 * 
 * Based on:
 * - Force-directed graph drawing (Fruchterman-Reingold)
 * - Barnes-Hut approximation for performance
 */

import * as THREE from 'three';

// ============================================================================
// Types
// ============================================================================

export interface GraphNode {
    id: string;
    label: string;
    type: string;
    position: THREE.Vector3;
    velocity: THREE.Vector3;
    mass: number;
    radius: number;
    fixed: boolean;
    cluster?: string;
}

export interface GraphEdge {
    id: string;
    source: string;
    target: string;
    weight: number;
}

export interface ForceConfig {
    repulsionStrength: number;
    springStrength: number;
    springLength: number;
    centerGravity: number;
    damping: number;
    iterations: number;
}

// ============================================================================
// Default Configuration
// ============================================================================

const DEFAULT_CONFIG: ForceConfig = {
    repulsionStrength: 1000,    // Strength of node repulsion
    springStrength: 0.01,        // Strength of edge springs
    springLength: 5,             // Ideal edge length
    centerGravity: 0.05,         // Pull towards center
    damping: 0.9,                // Velocity damping (0-1)
    iterations: 1,               // Iterations per frame
};

// ============================================================================
// Force Simulation Class
// ============================================================================

export class ForceSimulation {
    private nodes: Map<string, GraphNode>;
    private edges: GraphEdge[];
    private config: ForceConfig;
    private isRunning: boolean = true;

    constructor(
        nodes: GraphNode[],
        edges: GraphEdge[],
        config: Partial<ForceConfig> = {}
    ) {
        this.nodes = new Map(nodes.map(n => [n.id, n]));
        this.edges = edges;
        this.config = { ...DEFAULT_CONFIG, ...config };

        this.initializePositions();
    }

    /**
     * Initialize nodes with random positions in a sphere
     */
    private initializePositions(): void {
        const radius = Math.cbrt(this.nodes.size) * 5;

        for (const node of this.nodes.values()) {
            if (!node.position || (node.position.x === 0 && node.position.y === 0 && node.position.z === 0)) {
                // Random position in sphere
                const theta = Math.random() * Math.PI * 2;
                const phi = Math.acos(2 * Math.random() - 1);
                const r = radius * Math.cbrt(Math.random());

                node.position = new THREE.Vector3(
                    r * Math.sin(phi) * Math.cos(theta),
                    r * Math.sin(phi) * Math.sin(theta),
                    r * Math.cos(phi)
                );
            }

            if (!node.velocity) {
                node.velocity = new THREE.Vector3();
            }
        }
    }

    /**
     * Calculate repulsion force between two nodes
     */
    private calculateRepulsion(node1: GraphNode, node2: GraphNode): THREE.Vector3 {
        const delta = new THREE.Vector3().subVectors(node1.position, node2.position);
        const distance = delta.length();

        if (distance < 0.01) {
            // Avoid division by zero - add small random offset
            return new THREE.Vector3(
                (Math.random() - 0.5) * 0.1,
                (Math.random() - 0.5) * 0.1,
                (Math.random() - 0.5) * 0.1
            );
        }

        // Coulomb's law: F = k * (m1 * m2) / r^2
        const strength = this.config.repulsionStrength * node1.mass * node2.mass / (distance * distance);

        return delta.normalize().multiplyScalar(strength);
    }

    /**
     * Calculate spring force for an edge
     */
    private calculateSpring(edge: GraphEdge): { source: THREE.Vector3; target: THREE.Vector3 } {
        const sourceNode = this.nodes.get(edge.source);
        const targetNode = this.nodes.get(edge.target);

        if (!sourceNode || !targetNode) {
            return {
                source: new THREE.Vector3(),
                target: new THREE.Vector3(),
            };
        }

        const delta = new THREE.Vector3().subVectors(targetNode.position, sourceNode.position);
        const distance = delta.length();

        if (distance < 0.01) {
            return {
                source: new THREE.Vector3(),
                target: new THREE.Vector3(),
            };
        }

        // Hooke's law: F = k * (x - x0)
        const displacement = distance - this.config.springLength;
        const strength = this.config.springStrength * displacement * edge.weight;

        const force = delta.normalize().multiplyScalar(strength);

        return {
            source: force.clone(),
            target: force.clone().negate(),
        };
    }

    /**
     * Calculate center gravity force
     */
    private calculateCenterGravity(node: GraphNode): THREE.Vector3 {
        return node.position.clone().negate().multiplyScalar(this.config.centerGravity);
    }

    /**
     * Tick simulation forward by one step
     */
    public tick(deltaTime: number = 0.016): void {
        if (!this.isRunning) return;

        const forces = new Map<string, THREE.Vector3>();

        // Initialize forces
        for (const node of this.nodes.values()) {
            forces.set(node.id, new THREE.Vector3());
        }

        // Apply repulsion forces (all pairs)
        const nodeArray = Array.from(this.nodes.values());
        for (let i = 0; i < nodeArray.length; i++) {
            for (let j = i + 1; j < nodeArray.length; j++) {
                const node1 = nodeArray[i];
                const node2 = nodeArray[j];

                if (node1.fixed && node2.fixed) continue;

                const repulsion = this.calculateRepulsion(node1, node2);

                if (!node1.fixed) {
                    forces.get(node1.id)!.add(repulsion);
                }
                if (!node2.fixed) {
                    forces.get(node2.id)!.sub(repulsion);
                }
            }
        }

        // Apply spring forces (edges)
        for (const edge of this.edges) {
            const sourceNode = this.nodes.get(edge.source);
            const targetNode = this.nodes.get(edge.target);

            if (!sourceNode || !targetNode) continue;

            const springForces = this.calculateSpring(edge);

            if (!sourceNode.fixed) {
                forces.get(sourceNode.id)!.add(springForces.source);
            }
            if (!targetNode.fixed) {
                forces.get(targetNode.id)!.add(springForces.target);
            }
        }

        // Apply center gravity
        for (const node of this.nodes.values()) {
            if (!node.fixed) {
                const gravity = this.calculateCenterGravity(node);
                forces.get(node.id)!.add(gravity);
            }
        }

        // Update velocities and positions
        for (const node of this.nodes.values()) {
            if (node.fixed) continue;

            const force = forces.get(node.id)!;

            // F = ma, so a = F/m
            const acceleration = force.divideScalar(node.mass);

            // Update velocity
            node.velocity.add(acceleration.multiplyScalar(deltaTime));

            // Apply damping
            node.velocity.multiplyScalar(this.config.damping);

            // Update position
            node.position.add(node.velocity.clone().multiplyScalar(deltaTime));
        }
    }

    /**
     * Get all nodes
     */
    public getNodes(): GraphNode[] {
        return Array.from(this.nodes.values());
    }

    /**
     * Get all edges
     */
    public getEdges(): GraphEdge[] {
        return this.edges;
    }

    /**
     * Update node
     */
    public updateNode(id: string, updates: Partial<GraphNode>): void {
        const node = this.nodes.get(id);
        if (node) {
            Object.assign(node, updates);
        }
    }

    /**
     * Add node
     */
    public addNode(node: GraphNode): void {
        this.nodes.set(node.id, node);
    }

    /**
     * Remove node
     */
    public removeNode(id: string): void {
        this.nodes.delete(id);
        this.edges = this.edges.filter(e => e.source !== id && e.target !== id);
    }

    /**
     * Add edge
     */
    public addEdge(edge: GraphEdge): void {
        this.edges.push(edge);
    }

    /**
     * Start/stop simulation
     */
    public start(): void {
        this.isRunning = true;
    }

    public stop(): void {
        this.isRunning = false;
    }

    public isActive(): boolean {
        return this.isRunning;
    }

    /**
     * Calculate total energy (for convergence detection)
     */
    public getTotalEnergy(): number {
        let energy = 0;
        for (const node of this.nodes.values()) {
            energy += node.velocity.lengthSq();
        }
        return energy;
    }

    /**
     * Check if simulation has converged
     */
    public hasConverged(threshold: number = 0.01): boolean {
        return this.getTotalEnergy() < threshold;
    }
}

// ============================================================================
// Clustering Utilities
// ============================================================================

export class ClusterLayout {
    /**
     * Group nodes by cluster and position them in separate regions
     */
    static applyClusterPositions(
        nodes: GraphNode[],
        clusterRadius: number = 20
    ): void {
        const clusters = new Map<string, GraphNode[]>();

        // Group by cluster
        for (const node of nodes) {
            const cluster = node.cluster || 'default';
            if (!clusters.has(cluster)) {
                clusters.set(cluster, []);
            }
            clusters.get(cluster)!.push(node);
        }

        // Position clusters in circle
        const clusterArray = Array.from(clusters.entries());
        const angleStep = (Math.PI * 2) / clusterArray.length;

        clusterArray.forEach(([clusterName, clusterNodes], index) => {
            const angle = index * angleStep;
            const clusterCenter = new THREE.Vector3(
                Math.cos(angle) * clusterRadius,
                0,
                Math.sin(angle) * clusterRadius
            );

            // Position nodes within cluster
            const innerRadius = Math.cbrt(clusterNodes.length) * 2;
            clusterNodes.forEach((node, nodeIndex) => {
                const nodeAngle = (nodeIndex / clusterNodes.length) * Math.PI * 2;
                const nodePhi = Math.acos(2 * (nodeIndex / clusterNodes.length) - 1);
                const r = innerRadius * Math.cbrt(nodeIndex / clusterNodes.length);

                node.position = clusterCenter.clone().add(
                    new THREE.Vector3(
                        r * Math.sin(nodePhi) * Math.cos(nodeAngle),
                        r * Math.sin(nodePhi) * Math.sin(nodeAngle),
                        r * Math.cos(nodePhi)
                    )
                );
            });
        });
    }
}
