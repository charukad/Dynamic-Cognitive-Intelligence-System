'use client';

import { useEffect, useRef, useMemo, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import * as forceGraph3d from 'd3-force-3d';
import { useGraphStore } from '@/store/graphStore';
import { GraphNode } from '@/types/graph';

// Force d3-force-3d types (since they might be missing/generic)
// We import the module just to get the forceSimulation function
// In reality, we often just use d3-force standard types extended with Z

export function ForceDirectedLayout() {
    const { data, generateMockData } = useGraphStore();

    // Refs for InstancedMesh (Nodes) and LineSegments (Edges)
    const nodesRef = useRef<THREE.InstancedMesh>(null);
    const edgesRef = useRef<THREE.LineSegments>(null);

    // Simulation State
    type D3ForceSimulation = ReturnType<typeof forceGraph3d.forceSimulation>;
    const simulation = useRef<D3ForceSimulation | null>(null);

    // 1. Initialize Mock Data on Mount
    useEffect(() => {
        generateMockData(500); // Start with 500 nodes

        // Cleanup simulation on unmount
        return () => {
            if (simulation.current) simulation.current.stop();
        };
    }, [generateMockData]);

    // 2. Setup / Update Simulation when Data Changes
    useEffect(() => {
        if (data.nodes.length === 0) return;

        // Initialize D3 Force Simulation
        // @ts-expect-error - d3-force-3d has incomplete type definitions for id accessor
        const sim = forceGraph3d.forceSimulation(data.nodes, 3) // 3 dimensions
            .force('charge', forceGraph3d.forceManyBody().strength(-50))
            .force('link', forceGraph3d.forceLink(data.links).id((d: GraphNode) => d.id).distance(30))
            .force('center', forceGraph3d.forceCenter());

        simulation.current = sim;

        // Stop auto-tick to control via useFrame or manual steps
        sim.stop();

        // Re-warm simulation for initial layout
        for (let i = 0; i < 100; i++) sim.tick();

    }, [data]);

    // 3. Render Loop - Update Positions
    const dummy = useMemo(() => new THREE.Object3D(), []);

    useFrame(() => {
        if (!simulation.current || !nodesRef.current || !edgesRef.current) return;

        // Tick simulation (slow down or stop after convergence in real app)
        simulation.current.tick();

        // Update Nodes (InstancedMesh)
        data.nodes.forEach((node, i) => {
            dummy.position.set(node.x || 0, node.y || 0, node.z || 0);
            dummy.updateMatrix();
            nodesRef.current!.setMatrixAt(i, dummy.matrix);
        });
        nodesRef.current.instanceMatrix.needsUpdate = true;

        // Update Edges (LineBufferGeometry)
        const positions = edgesRef.current.geometry.attributes.position.array as Float32Array;
        let idx = 0;
        data.links.forEach((link) => {
            const source = link.source as GraphNode;
            const target = link.target as GraphNode;

            // Start Point
            positions[idx++] = source.x || 0;
            positions[idx++] = source.y || 0;
            positions[idx++] = source.z || 0;

            // End Point
            positions[idx++] = target.x || 0;
            positions[idx++] = target.y || 0;
            positions[idx++] = target.z || 0;
        });
        edgesRef.current.geometry.attributes.position.needsUpdate = true;
    });

    // Calculate buffer size for edges (max possible lines * 2 points * 3 coords)
    const maxEdges = 2000;
    const edgePositions = useMemo(() => new Float32Array(maxEdges * 2 * 3), []);


    // Hover interaction
    const { setHoveredNode } = useGraphStore();
    const [hoveredInstance, setHoveredInstance] = useState<number | null>(null);

    // Update hover visual
    useEffect(() => {
        if (!nodesRef.current) return;
        const color = new THREE.Color();

        // Reset all to Gold
        for (let i = 0; i < data.nodes.length; i++) {
            color.setHex(0xFFD700);
            nodesRef.current.setColorAt(i, color);
        }

        // Highlight hovered
        if (hoveredInstance !== null) {
            color.setHex(0x00F0FF); // Cyan highlight
            nodesRef.current.setColorAt(hoveredInstance, color);
        }

        // Safely update instance color if ref is ready
        if (nodesRef.current?.instanceColor) {
            nodesRef.current.instanceColor.needsUpdate = true;
        }
    }, [hoveredInstance, data.nodes.length]);


    return (
        <group>
            {/* Nodes */}
            <instancedMesh
                ref={nodesRef}
                args={[undefined, undefined, 1000]}
                onPointerOver={(e) => {
                    e.stopPropagation();
                    if (e.instanceId !== undefined && data.nodes[e.instanceId]) {
                        setHoveredInstance(e.instanceId);
                        setHoveredNode(data.nodes[e.instanceId].id);
                    }
                }}
                onPointerOut={() => {
                    setHoveredInstance(null);
                    setHoveredNode(null);
                }}
            >
                <sphereGeometry args={[0.5, 16, 16]} />
                <meshStandardMaterial emissive="#FFD700" emissiveIntensity={0.5} roughness={0.2} metalness={0.8} />
            </instancedMesh>

            {/* Edges */}
            <lineSegments ref={edgesRef}>
                <bufferGeometry>
                    <bufferAttribute
                        attach="attributes-position"
                        args={[edgePositions, 3]}
                    />
                </bufferGeometry>
                <lineBasicMaterial color="#ffffff" transparent opacity={0.1} depthWrite={false} />
            </lineSegments>
        </group>
    );
}
