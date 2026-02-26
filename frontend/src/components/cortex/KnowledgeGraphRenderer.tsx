'use client';

/**
 * Knowledge Graph Renderer - 3D Visualization
 * 
 * Renders knowledge graph with force-directed layout.
 * 
 * Features:
 * - 3D force-directed graph layout
 * - Node clustering by type
 * - Interactive node selection
 * - Edge rendering with thickness based on weight
 * - Dynamic camera controls
 * - Performance optimization (LOD, culling)
 */

'use client';

import { useRef, useMemo, useState, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { Text } from '@react-three/drei';
import { ForceSimulation, GraphNode, GraphEdge, ClusterLayout } from './ForceSimulation';

// ============================================================================
// Types
// ============================================================================

interface KnowledgeGraphProps {
    nodes: GraphNode[];
    edges: GraphEdge[];
    onNodeClick?: (node: GraphNode) => void;
    onNodeHover?: (node: GraphNode | null) => void;
}

// ============================================================================
// Constants
// ============================================================================

const NODE_COLORS = {
    concept: new THREE.Color(0x64b5f6),     // Blue
    entity: new THREE.Color(0x66bb6a),      // Green
    action: new THREE.Color(0xffa726),      // Orange
    property: new THREE.Color(0xab47bc),    // Purple
    default: new THREE.Color(0x9e9e9e),     // Gray
} as const;

const BASE_NODE_SIZE = 0.5;
const EDGE_WIDTH = 0.02;

// ============================================================================
// Node Component
// ============================================================================

function GraphNodeMesh({
    node,
    onClick,
    onHover,
    isSelected,
}: {
    node: GraphNode;
    onClick?: (node: GraphNode) => void;
    onHover?: (node: GraphNode | null) => void;
    isSelected: boolean;
}) {
    const meshRef = useRef<THREE.Mesh>(null);
    const [hovered, setHovered] = useState(false);

    const color = useMemo(
        () => NODE_COLORS[node.type as keyof typeof NODE_COLORS] || NODE_COLORS.default,
        [node.type]
    );

    const scale = isSelected ? 1.5 : hovered ? 1.2 : 1.0;

    useFrame(() => {
        if (meshRef.current) {
            // Smooth scale transition
            const targetScale = scale * (node.radius / BASE_NODE_SIZE);
            meshRef.current.scale.lerp(
                new THREE.Vector3(targetScale, targetScale, targetScale),
                0.1
            );

            // Update position from simulation
            meshRef.current.position.copy(node.position);
        }
    });

    return (
        <group>
            <mesh
                ref={meshRef}
                position={node.position}
                onClick={() => onClick?.(node)}
                onPointerOver={(e) => {
                    e.stopPropagation();
                    setHovered(true);
                    onHover?.(node);
                    document.body.style.cursor = 'pointer';
                }}
                onPointerOut={() => {
                    setHovered(false);
                    onHover?.(null);
                    document.body.style.cursor = 'auto';
                }}
            >
                <sphereGeometry args={[BASE_NODE_SIZE, 32, 32]} />
                <meshStandardMaterial
                    color={color}
                    emissive={color}
                    emissiveIntensity={isSelected ? 0.5 : hovered ? 0.3 : 0.1}
                    roughness={0.3}
                    metalness={0.7}
                />
            </mesh>

            {/* Label */}
            {(hovered || isSelected) && (
                <Text
                    position={[node.position.x, node.position.y + node.radius + 0.5, node.position.z]}
                    fontSize={0.5}
                    color="white"
                    anchorX="center"
                    anchorY="middle"
                    outlineWidth={0.05}
                    outlineColor="#000000"
                >
                    {node.label}
                </Text>
            )}
        </group>
    );
}

// ============================================================================
// Edge Component
// ============================================================================

function GraphEdgeLine({
    edge,
    sourceNode,
    targetNode,
}: {
    edge: GraphEdge;
    sourceNode: GraphNode;
    targetNode: GraphNode;
}) {
    const geometry = useMemo(() => {
        const geom = new THREE.BufferGeometry();
        const positions = new Float32Array(6);
        geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        return geom;
    }, []);

    useFrame(() => {
        // Update line positions from simulation
        geometry.setAttribute(
            'position',
            new THREE.BufferAttribute(
                new Float32Array([
                    sourceNode.position.x, sourceNode.position.y, sourceNode.position.z,
                    targetNode.position.x, targetNode.position.y, targetNode.position.z,
                ]),
                3
            )
        );
    });

    const opacity = Math.min(edge.weight, 1.0);
    const lineWidth = EDGE_WIDTH * edge.weight;

    return (
        <line geometry={geometry}>
            <lineBasicMaterial
                color={0x64b5f6}
                opacity={opacity * 0.3}
                transparent
                linewidth={lineWidth}
            />
        </line>
    );
}

// ============================================================================
// Main Knowledge Graph Component
// ============================================================================

export function KnowledgeGraphRenderer({
    nodes,
    edges,
    onNodeClick,
    onNodeHover,
}: KnowledgeGraphProps) {
    const groupRef = useRef<THREE.Group>(null);
    const simulationRef = useRef<ForceSimulation | null>(null);
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

    // ============================================================================
    // Initialize Simulation
    // ============================================================================

    useEffect(() => {
        // Apply cluster layout
        ClusterLayout.applyClusterPositions(nodes, 20);

        // Create simulation
        simulationRef.current = new ForceSimulation(nodes, edges, {
            repulsionStrength: 500,
            springStrength: 0.02,
            springLength: 3,
            centerGravity: 0.03,
            damping: 0.85,
        });

        return () => {
            simulationRef.current = null;
        };
    }, [nodes, edges]);

    // ============================================================================
    // Animation Loop
    // ============================================================================

    useFrame((state, delta) => {
        if (simulationRef.current) {
            // Run simulation
            simulationRef.current.tick(delta);

            // Auto-stop after convergence
            if (simulationRef.current.hasConverged(0.1)) {
                simulationRef.current.stop();
            }
        }
    });

    // ============================================================================
    // Event Handlers
    // ============================================================================

    const handleNodeClick = (node: GraphNode) => {
        setSelectedNodeId(node.id);
        onNodeClick?.(node);
    };

    const handleNodeHover = (node: GraphNode | null) => {
        onNodeHover?.(node);
    };

    // ============================================================================
    // Render
    // ============================================================================

    return (
        <group ref={groupRef}>
            {/* Render Edges */}
            {edges.map((edge) => {
                const sourceNode = nodes.find(n => n.id === edge.source);
                const targetNode = nodes.find(n => n.id === edge.target);

                if (!sourceNode || !targetNode) return null;

                return (
                    <GraphEdgeLine
                        key={edge.id}
                        edge={edge}
                        sourceNode={sourceNode}
                        targetNode={targetNode}
                    />
                );
            })}

            {/* Render Nodes */}
            {nodes.map((node) => (
                <GraphNodeMesh
                    key={node.id}
                    node={node}
                    onClick={handleNodeClick}
                    onHover={handleNodeHover}
                    isSelected={node.id === selectedNodeId}
                />
            ))}
        </group>
    );
}

// ============================================================================
// Graph Statistics Component
// ============================================================================

export function GraphStats({ nodes, edges }: { nodes: GraphNode[]; edges: GraphEdge[] }) {
    const avgDegree = nodes.length > 0 ? (edges.length * 2) / nodes.length : 0;

    return (
        <div className="absolute left-3 top-3 z-10 rounded-xl border border-fuchsia-400/25 bg-slate-950/88 px-3.5 py-2.5 font-mono text-xs text-slate-100 shadow-lg backdrop-blur-md md:left-4 md:top-4">
            <div>Nodes: {nodes.length}</div>
            <div>Edges: {edges.length}</div>
            <div>Avg Degree: {avgDegree.toFixed(2)}</div>
        </div>
    );
}
