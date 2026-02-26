'use client';

/**
 * Agent Particle System - 3D Visualization
 * 
 * Features:
 * - Instanced particle rendering for performance (1000+ agents)
 * - Physics-based movement simulation
 * - Color-coded by agent state (idle, thinking, executing)
 * - Real-time WebSocket updates
 * - Camera controls (orbit, zoom, pan)
 * - Smooth animations with spring physics
 * 
 * Performance targets:
 * - 60 FPS with 100+ agents
 * - <16ms frame time
 * - Optimized with frustum culling
 */

'use client';

import { useRef, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useAgentStore } from '../../store/agentStore';

// ============================================================================
// Types
// ============================================================================

export type AgentState = 'idle' | 'thinking' | 'executing' | 'failed' | 'success';

interface ParticleData {
    position: THREE.Vector3;
    velocity: THREE.Vector3;
    targetPosition: THREE.Vector3;
    color: THREE.Color;
    scale: number;
    agentId: string;
    state: AgentState;
}

interface AgentParticleSystemProps {
    maxAgents?: number;
    particleSize?: number;
    springStrength?: number;
    damping?: number;
}

// ============================================================================
// Constants
// ============================================================================

const PARTICLE_SIZE = 0.15;
const SPRING_STRENGTH = 0.05;
const DAMPING = 0.92;
const MAX_VELOCITY = 2.0;
const ORBIT_RADIUS = 10;

// Agent state colors
const STATE_COLORS = {
    idle: new THREE.Color(0x64b5f6),      // Blue
    thinking: new THREE.Color(0xffa726),  // Orange
    executing: new THREE.Color(0x66bb6a), // Green
    failed: new THREE.Color(0xef5350),    // Red
    success: new THREE.Color(0x9ccc65),   // Light green
} as const;

// ============================================================================
// Physics Utilities
// ============================================================================

class ParticlePhysics {
    /**
     * Apply spring force towards target position
     */
    static applySpringForce(
        particle: ParticleData,
        springStrength: number,
        damping: number,
        deltaTime: number
    ): void {
        // Calculate spring force
        const force = new THREE.Vector3()
            .subVectors(particle.targetPosition, particle.position)
            .multiplyScalar(springStrength);

        // Update velocity
        particle.velocity.add(force.multiplyScalar(deltaTime));

        // Apply damping
        particle.velocity.multiplyScalar(damping);

        // Clamp velocity
        const speed = particle.velocity.length();
        if (speed > MAX_VELOCITY) {
            particle.velocity.normalize().multiplyScalar(MAX_VELOCITY);
        }

        // Update position
        particle.position.add(
            particle.velocity.clone().multiplyScalar(deltaTime)
        );
    }

    /**
     * Generate orbital position for agent
     */
    static generateOrbitalPosition(
        index: number,
        total: number,
        radius: number,
        time: number
    ): THREE.Vector3 {
        const angle = (index / total) * Math.PI * 2;
        const heightVariation = Math.sin(time * 0.5 + index) * 2;

        return new THREE.Vector3(
            Math.cos(angle) * radius,
            heightVariation,
            Math.sin(angle) * radius
        );
    }

    /**
     * Apply separation force (avoid clustering)
     */
    static applySeparation(
        particle: ParticleData,
        allParticles: ParticleData[],
        separationRadius: number = 1.5
    ): void {
        const separationForce = new THREE.Vector3();
        let nearbyCount = 0;

        for (const other of allParticles) {
            if (other === particle) continue;

            const distance = particle.position.distanceTo(other.position);

            if (distance < separationRadius && distance > 0) {
                const diff = new THREE.Vector3()
                    .subVectors(particle.position, other.position)
                    .normalize()
                    .divideScalar(distance); // Stronger when closer

                separationForce.add(diff);
                nearbyCount++;
            }
        }

        if (nearbyCount > 0) {
            separationForce.divideScalar(nearbyCount);
            particle.velocity.add(separationForce.multiplyScalar(0.1));
        }
    }
}

// ============================================================================
// Main Component
// ============================================================================

export function AgentParticleSystem({
    maxAgents = 100,
    particleSize = PARTICLE_SIZE,
    springStrength = SPRING_STRENGTH,
    damping = DAMPING,
}: AgentParticleSystemProps) {
    const meshRef = useRef<THREE.InstancedMesh>(null);
    const particlesRef = useRef<ParticleData[]>([]);
    const timeRef = useRef(0);

    const { agents } = useAgentStore();

    // ============================================================================
    // Geometry & Material (Memoized for performance)
    // ============================================================================

    const geometry = useMemo(
        () => new THREE.SphereGeometry(particleSize, 16, 16),
        [particleSize]
    );

    const material = useMemo(
        () => new THREE.MeshStandardMaterial({
            emissive: new THREE.Color(0x000000),
            emissiveIntensity: 0.2,
            roughness: 0.3,
            metalness: 0.7,
        }),
        []
    );

    // ============================================================================
    // Initialize Particles
    // ============================================================================

    useEffect(() => {
        // Create particle data for each agent
        const agentsArray = Object.values(agents);
        const newParticles: ParticleData[] = agentsArray.slice(0, maxAgents).map((agent, index) => {
            const position = ParticlePhysics.generateOrbitalPosition(
                index,
                Math.min(agentsArray.length, maxAgents),
                ORBIT_RADIUS,
                0
            );

            return {
                position: position.clone(),
                velocity: new THREE.Vector3(),
                targetPosition: position.clone(),
                color: STATE_COLORS[(agent.status || 'idle') as keyof typeof STATE_COLORS] || STATE_COLORS.idle,
                scale: 1.0,
                agentId: agent.id,
                state: (agent.status || 'idle') as AgentState,
            };
        });

        particlesRef.current = newParticles;

        // Initialize instance matrices
        if (meshRef.current) {
            const matrix = new THREE.Matrix4();
            const color = new THREE.Color();

            for (let i = 0; i < maxAgents; i++) {
                if (i < newParticles.length) {
                    const particle = newParticles[i];

                    matrix.setPosition(particle.position);
                    meshRef.current.setMatrixAt(i, matrix);
                    meshRef.current.setColorAt(i, particle.color);
                } else {
                    // Hide unused instances
                    matrix.setPosition(0, -1000, 0);
                    meshRef.current.setMatrixAt(i, matrix);
                    meshRef.current.setColorAt(i, color.set(0x000000));
                }
            }

            meshRef.current.instanceMatrix.needsUpdate = true;
            if (meshRef.current.instanceColor) {
                meshRef.current.instanceColor.needsUpdate = true;
            }
        }
    }, [agents, maxAgents]);

    // ============================================================================
    // Animation Loop
    // ============================================================================

    useFrame((state, delta) => {
        if (!meshRef.current || particlesRef.current.length === 0) return;

        timeRef.current += delta;
        const particles = particlesRef.current;
        const matrix = new THREE.Matrix4();

        // Update each particle
        for (let i = 0; i < particles.length; i++) {
            const particle = particles[i];

            // Find corresponding agent and update state
            const agent = agents[particle.agentId];
            if (agent) {
                const agentState = (agent.status || 'idle') as AgentState;
                // Update color based on agent state
                const newColor = STATE_COLORS[agentState as keyof typeof STATE_COLORS] || STATE_COLORS.idle;
                if (!particle.color.equals(newColor)) {
                    particle.color.lerp(newColor, 0.1); // Smooth color transition
                    meshRef.current.setColorAt(i, particle.color);
                }

                // Update target position based on agent activity
                particle.targetPosition = ParticlePhysics.generateOrbitalPosition(
                    i,
                    particles.length,
                    ORBIT_RADIUS + (agentState === 'executing' ? 1 : 0), // Expand when executing
                    timeRef.current
                );

                // Scale based on state
                const targetScale = agentState === 'executing' ? 1.5 :
                    agentState === 'thinking' ? 1.2 : 1.0;
                particle.scale += (targetScale - particle.scale) * 0.1;
                particle.state = agentState;
            }

            // Apply physics
            ParticlePhysics.applySpringForce(particle, springStrength, damping, delta);
            ParticlePhysics.applySeparation(particle, particles);

            // Update instance matrix
            matrix.makeScale(particle.scale, particle.scale, particle.scale);
            matrix.setPosition(particle.position);
            meshRef.current.setMatrixAt(i, matrix);
        }

        // Update GPU buffers
        meshRef.current.instanceMatrix.needsUpdate = true;
        if (meshRef.current.instanceColor) {
            meshRef.current.instanceColor.needsUpdate = true;
        }

    });

    // ============================================================================
    // Render
    // ============================================================================

    return (
        <instancedMesh
            ref={meshRef}
            args={[geometry, material, maxAgents]}
            frustumCulled={true}
        >
            {/* Material is passed as args */}
        </instancedMesh>
    );
}

// ============================================================================
// Performance Monitor Component
// ============================================================================

export function ParticleSystemStats() {
    useFrame((state) => {
        // Log performance metrics in development
        if (process.env.NODE_ENV === 'development') {
            const fps = 1 / state.clock.getDelta();
            if (fps < 55) {
                console.warn(`Low FPS detected: ${fps.toFixed(1)}`);
            }
        }
    });

    return null;
}
