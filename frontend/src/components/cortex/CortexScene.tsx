'use client';

/**
 * Cortex Scene - Knowledge Graph Visualization Container
 * 
 * Main scene component integrating all cortex visualization elements.
 */

'use client';

import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Environment } from '@react-three/drei';
import { EffectComposer, Bloom, SSAO } from '@react-three/postprocessing';
import { KnowledgeGraphRenderer, GraphStats } from './KnowledgeGraphRenderer';
import { GraphNode } from './ForceSimulation';
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
            <div className="flex h-full min-h-[540px] w-full items-center justify-center rounded-2xl border border-fuchsia-500/20 bg-[radial-gradient(circle_at_top,_rgba(168,85,247,0.12),_transparent_45%),linear-gradient(180deg,rgba(4,6,23,0.96),rgba(2,9,26,0.82))] text-slate-200 shadow-[0_22px_64px_rgba(0,0,0,0.45)]">
                Loading knowledge graph...
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex h-full min-h-[540px] w-full items-center justify-center rounded-2xl border border-rose-500/25 bg-[radial-gradient(circle_at_top,_rgba(244,63,94,0.12),_transparent_45%),linear-gradient(180deg,rgba(4,6,23,0.96),rgba(2,9,26,0.82))] text-rose-300 shadow-[0_22px_64px_rgba(0,0,0,0.45)]">
                Error loading graph: {error}
            </div>
        );
    }

    return (
        <div className="relative h-full min-h-[600px] w-full overflow-hidden rounded-2xl border border-fuchsia-500/20 bg-[radial-gradient(circle_at_top,_rgba(192,132,252,0.16),_transparent_44%),linear-gradient(180deg,rgba(9,7,24,0.96),rgba(3,11,28,0.82))] shadow-[0_22px_64px_rgba(0,0,0,0.45)]">
            <Canvas className="h-full w-full">
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
                <div className="absolute right-3 top-3 z-10 w-[min(320px,88vw)] rounded-xl border border-fuchsia-400/25 bg-slate-950/90 p-4 text-slate-100 backdrop-blur-md md:right-4 md:top-4">
                    <h3 className="mb-2 text-base font-semibold">
                        {selectedNode.label}
                    </h3>
                    <div className="space-y-1 text-xs text-slate-400">
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
                        className="mt-3 rounded-md border border-fuchsia-400/40 bg-fuchsia-600/80 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-fuchsia-500"
                    >
                        Close
                    </button>
                </div>
            )}

            {/* Hover Tooltip */}
            {hoveredNode && !selectedNode && (
                <div className="pointer-events-none absolute bottom-3 left-1/2 z-10 -translate-x-1/2 rounded-lg border border-fuchsia-400/20 bg-slate-950/90 px-3 py-1.5 text-xs text-slate-100 shadow-xl md:bottom-4">
                    {hoveredNode.label} ({hoveredNode.type})
                </div>
            )}
        </div>
    );
}
