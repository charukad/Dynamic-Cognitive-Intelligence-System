/**
 * Orbit Scene - Main 3D Visualization Container
 * 
 * Combines all orbital visualization components:
 * - Agent Particle System
 * - Neural Link connections
 * - Camera controls
 * - Lighting setup
 * - Post-processing effects
 */

import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Stars } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import { AgentParticleSystem, ParticleSystemStats } from './AgentParticleSystem';
import { NeuralLink, useConnectionManager } from './NeuralLink';
import { SynapseSystem } from './SynapseSystem';
import { useAgentStore } from '../../store/agentStore';
import { useEffect } from 'react';

// ============================================================================
// Lighting Setup
// ============================================================================

function Lighting() {
    return (
        <>
            {/* Ambient light for base illumination */}
            <ambientLight intensity={0.3} />

            {/* Main directional light */}
            <directionalLight
                position={[10, 10, 10]}
                intensity={0.8}
                castShadow
            />

            {/* Fill light from opposite side */}
            <directionalLight
                position={[-10, -10, -10]}
                intensity={0.3}
            />

            {/* Point light at center for glow */}
            <pointLight
                position={[0, 0, 0]}
                intensity={0.5}
                color="#64b5f6"
                distance={30}
            />
        </>
    );
}

// ============================================================================
// Main Orbit Scene Component
// ============================================================================

export function OrbitScene() {
    const { agents } = useAgentStore();
    const { addConnection, getConnections, cleanup } = useConnectionManager();

    // Simulate connections when agents communicate
    // In production, this would come from WebSocket events
    useEffect(() => {
        const interval = setInterval(() => {
            // Randomly create connections between active agents
            const activeAgents = agents.filter(a => a.state === 'executing');

            if (activeAgents.length >= 2) {
                const source = activeAgents[Math.floor(Math.random() * activeAgents.length)];
                const target = activeAgents[Math.floor(Math.random() * activeAgents.length)];

                if (source.id !== target.id) {
                    // In production, positions would come from particle system state
                    // For now, we'll use placeholder positions
                    addConnection(
                        source.id,
                        target.id,
                        { x: 0, y: 0, z: 0 } as any,
                        { x: 1, y: 1, z: 1 } as any,
                        Math.random()
                    );
                }
            }

            // Clean up old connections
            cleanup(5000);
        }, 2000);

        return () => clearInterval(interval);
    }, [agents, addConnection, cleanup]);

    return (
        <div style={{ width: '100vw', height: '100vh', background: '#000' }}>
            <Canvas>
                {/* Camera Setup */}
                <PerspectiveCamera makeDefault position={[0, 10, 25]} fov={60} />

                {/* Camera Controls */}
                <OrbitControls
                    enableDamping
                    dampingFactor={0.05}
                    minDistance={10}
                    maxDistance={50}
                    maxPolarAngle={Math.PI / 1.5}
                />

                {/* Lighting */}
                <Lighting />

                {/* Background Stars */}
                <Stars
                    radius={100}
                    depth={50}
                    count={5000}
                    factor={4}
                    saturation={0}
                    fade
                    speed={1}
                />

                {/* Agent Particles */}
                <AgentParticleSystem maxAgents={100} />

                {/* Neural Links */}
                <NeuralLink connections={getConnections()} />

                {/* Synapse System (existing) */}
                <SynapseSystem />

                {/* Performance Monitoring */}
                <ParticleSystemStats />

                {/* Post-processing Effects */}
                <EffectComposer>
                    <Bloom
                        intensity={0.5}
                        luminanceThreshold={0.4}
                        luminanceSmoothing={0.9}
                    />
                </EffectComposer>
            </Canvas>
        </div>
    );
}
