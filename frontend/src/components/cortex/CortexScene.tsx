/**
 * Cortex Scene - Knowledge Graph Visualization Container
 * 
 * Main scene component integrating all cortex visualization elements.
 */

import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Environment } from '@react-three/drei';
import { EffectComposer, Bloom, SSAO } from '@react-three/postprocessing';
import { KnowledgeGraphRenderer, GraphStats } from './KnowledgeGraphRenderer';
import { GraphNode, GraphEdge } from './ForceSimulation';
import { useKnowledgeGraph } from '../../hooks/useKnowledgeGraph';
import { useState } from 'react';

// ============================================================================
// Lighting Setup for Knowledge Graph
// ============================================================================

function CortexLighting() {
    return (
        <>
            <ambientLight intensity={0.4} />
            <directionalLight position={[10, 10, 10]} intensity={0.6} />
            <directionalLight position={[-10, -10, -10]} intensity={0.2} />
            <pointLight position={[0, 0, 0]} intensity={0.3} color="#9c27b0" />
        </>
    );
}

// ============================================================================
// Main Cortex Scene Component
// ============================================================================

export function CortexScene() {
    const { nodes, edges, loading, error } = useKnowledgeGraph();
    const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
    const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);

    const handleNodeClick = (node: GraphNode) => {
        setSelectedNode(node);
        console.log('Selected node:', node);

        // In production: fetch related concepts, show details panel
    };

    const handleNodeHover = (node: GraphNode | null) => {
        setHoveredNode(node);
    };

    if (loading) {
        return (
            <div
                style={{
                    width: '100vw',
                    height: '100vh',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: '#0a0a0a',
                    color: 'white',
                }}
            >
                Loading knowledge graph...
            </div>
        );
    }

    if (error) {
        return (
            <div
                style={{
                    width: '100vw',
                    height: '100vh',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: '#0a0a0a',
                    color: '#ef5350',
                }}
            >
                Error loading graph: {error}
            </div>
        );
    }

    return (
        <div style={{ width: '100vw', height: '100vh', background: '#0a0a0a' }}>
            <Canvas>
                {/* Camera */}
                <PerspectiveCamera makeDefault position={[0, 15, 30]} fov={60} />

                {/* Camera Controls */}
                <OrbitControls
                    enableDamping
                    dampingFactor={0.05}
                    minDistance={5}
                    maxDistance={100}
                />

                {/* Lighting */}
                <CortexLighting />

                {/* Environment for reflections */}
                <Environment preset="city" />

                {/* Knowledge Graph */}
                <KnowledgeGraphRenderer
                    nodes={nodes}
                    edges={edges}
                    onNodeClick={handleNodeClick}
                    onNodeHover={handleNodeHover}
                />

                {/* Post-processing */}
                <EffectComposer>
                    <Bloom
                        intensity={0.3}
                        luminanceThreshold={0.5}
                        luminanceSmoothing={0.9}
                    />
                    <SSAO
                        intensity={30}
                        radius={10}
                        luminanceInfluence={0.5}
                    />
                </EffectComposer>
            </Canvas>

            {/* Graph Statistics Overlay */}
            <GraphStats nodes={nodes} edges={edges} />

            {/* Node Details Panel */}
            {selectedNode && (
                <div
                    style={{
                        position: 'absolute',
                        top: 20,
                        right: 20,
                        background: 'rgba(0,0,0,0.8)',
                        color: 'white',
                        padding: '15px 20px',
                        borderRadius: 8,
                        maxWidth: 300,
                        fontFamily: 'system-ui',
                    }}
                >
                    <h3 style={{ margin: '0 0 10px 0', fontSize: 16 }}>
                        {selectedNode.label}
                    </h3>
                    <div style={{ fontSize: 12, color: '#aaa' }}>
                        <div>Type: {selectedNode.type}</div>
                        <div>Cluster: {selectedNode.cluster || 'None'}</div>
                        <div>
                            Connections:{' '}
                            {edges.filter(
                                (e) => e.source === selectedNode.id || e.target === selectedNode.id
                            ).length}
                        </div>
                    </div>
                    <button
                        onClick={() => setSelectedNode(null)}
                        style={{
                            marginTop: 10,
                            padding: '5px 10px',
                            background: '#9c27b0',
                            color: 'white',
                            border: 'none',
                            borderRadius: 4,
                            cursor: 'pointer',
                        }}
                    >
                        Close
                    </button>
                </div>
            )}

            {/* Hover Tooltip */}
            {hoveredNode && !selectedNode && (
                <div
                    style={{
                        position: 'absolute',
                        bottom: 20,
                        left: '50%',
                        transform: 'translateX(-50%)',
                        background: 'rgba(0,0,0,0.9)',
                        color: 'white',
                        padding: '8px 12px',
                        borderRadius: 6,
                        fontSize: 12,
                        pointerEvents: 'none',
                    }}
                >
                    {hoveredNode.label} ({hoveredNode.type})
                </div>
            )}
        </div>
    );
}
