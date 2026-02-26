'use client';

/**
 * Neural Link Connection Renderer
 * 
 * Visualizes communication between agents using animated Bezier curves.
 * 
 * Features:
 * - Dynamic connection creation/destruction
 * - Animated flow of information
 * - Connection strength visualization
 * - Fade out based on recency
 * - Batch rendering for performance
 */

'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { Line } from '@react-three/drei';

// ============================================================================
// Types
// ============================================================================

interface Connection {
    id: string;
    sourceAgentId: string;
    targetAgentId: string;
    sourcePosition: THREE.Vector3;
    targetPosition: THREE.Vector3;
    strength: number;        // 0-1
    createdAt: number;       // timestamp
    flowDirection: number;   // 0-1 for animation
    color: THREE.Color;
}

interface NeuralLinkProps {
    connections: Connection[];
    maxConnectionAge?: number;  // ms
    flowSpeed?: number;
    fadeOutDuration?: number;   // ms
}

// ============================================================================
// Constants
// ============================================================================

const MAX_CONNECTION_AGE = 5000;  // 5 seconds
const FLOW_SPEED = 0.5;
const FADE_OUT_DURATION = 1000;   // 1 second
const CONNECTION_WIDTH = 0.05;

// ============================================================================
// Utilities
// ============================================================================

class ConnectionUtils {
    /**
     * Calculate Bezier control point for smooth curves
     */
    static calculateControlPoint(
        start: THREE.Vector3,
        end: THREE.Vector3,
        curvature: number = 0.3
    ): THREE.Vector3 {
        const midpoint = new THREE.Vector3()
            .addVectors(start, end)
            .multiplyScalar(0.5);

        // Offset towards center for organic curves
        const toCenter = new THREE.Vector3().subVectors(new THREE.Vector3(0, 0, 0), midpoint);
        toCenter.normalize().multiplyScalar(curvature * start.distanceTo(end));

        return midpoint.add(toCenter);
    }

    /**
     * Generate Bezier curve points
     */
    static generateBezierCurve(
        start: THREE.Vector3,
        end: THREE.Vector3,
        control: THREE.Vector3,
        segments: number = 32
    ): THREE.Vector3[] {
        const curve = new THREE.QuadraticBezierCurve3(start, control, end);
        return curve.getPoints(segments);
    }

    /**
     * Calculate connection opacity based on age
     */
    static calculateOpacity(
        createdAt: number,
        currentTime: number,
        maxAge: number,
        fadeOutDuration: number
    ): number {
        const age = currentTime - createdAt;

        if (age > maxAge) {
            return 0;
        }

        // Fade out in last portion of lifetime
        const timeUntilDeath = maxAge - age;
        if (timeUntilDeath < fadeOutDuration) {
            return timeUntilDeath / fadeOutDuration;
        }

        return 1.0;
    }
}

// ============================================================================
// Single Connection Component
// ============================================================================

function ConnectionLine({
    connection,
    maxAge,
    fadeOutDuration,
    flowSpeed,
}: {
    connection: Connection;
    maxAge: number;
    fadeOutDuration: number;
    flowSpeed: number;
}) {
    const lineRef = useRef<THREE.Object3D | null>(null);

    // Calculate control point for Bezier curve
    const controlPoint = useMemo(
        () => ConnectionUtils.calculateControlPoint(
            connection.sourcePosition,
            connection.targetPosition,
            0.2 + connection.strength * 0.3 // More strength = more curve
        ),
        [connection]
    );

    // Generate curve points
    const points = useMemo(
        () => ConnectionUtils.generateBezierCurve(
            connection.sourcePosition,
            connection.targetPosition,
            controlPoint,
            32
        ),
        [connection, controlPoint]
    );

    // Animate flow
    useFrame((_, delta) => {
        if (!lineRef.current) return;

        const opacity = ConnectionUtils.calculateOpacity(
            connection.createdAt,
            Date.now(),
            maxAge,
            fadeOutDuration
        );

        // Animate dashed line to show flow
        const material =
            'material' in lineRef.current
                ? lineRef.current.material
                : null;

        if (!material) {
            return;
        }

        const dashStep = delta * (2 + flowSpeed);

        if (Array.isArray(material)) {
            material.forEach((entry) => {
                if ('dashOffset' in entry && typeof entry.dashOffset === 'number') {
                    entry.dashOffset -= dashStep;
                }
                if ('opacity' in entry && typeof entry.opacity === 'number') {
                    entry.opacity = opacity * 0.6;
                }
            });
            lineRef.current.visible = opacity > 0;
            return;
        }

        if ('dashOffset' in material && typeof material.dashOffset === 'number') {
            material.dashOffset -= dashStep;
        }
        if ('opacity' in material && typeof material.opacity === 'number') {
            material.opacity = opacity * 0.6;
        }
        lineRef.current.visible = opacity > 0;
    });

    return (
        <Line
            ref={lineRef}
            points={points}
            color={connection.color}
            lineWidth={CONNECTION_WIDTH * connection.strength}
            transparent
            opacity={0.6}
            dashed
            dashScale={20}
            dashSize={0.5}
            gapSize={0.5}
        />
    );
}

// ============================================================================
// Main Neural Link Component
// ============================================================================

export function NeuralLink({
    connections,
    maxConnectionAge = MAX_CONNECTION_AGE,
    flowSpeed = FLOW_SPEED,
    fadeOutDuration = FADE_OUT_DURATION,
}: NeuralLinkProps) {
    return (
        <group name="neural-link">
            {connections.map(connection => (
                <ConnectionLine
                    key={connection.id}
                    connection={connection}
                    maxAge={maxConnectionAge}
                    fadeOutDuration={fadeOutDuration}
                    flowSpeed={flowSpeed}
                />
            ))}
        </group>
    );
}

// ============================================================================
// Connection Manager Hook
// ============================================================================

/**
 * Hook to manage connections from WebSocket events
 */
export function useConnectionManager() {
    const connectionsRef = useRef<Map<string, Connection>>(new Map());

    /**
     * Add new connection
     */
    const addConnection = (
        sourceAgentId: string,
        targetAgentId: string,
        sourcePosition: THREE.Vector3,
        targetPosition: THREE.Vector3,
        strength: number = 1.0
    ): void => {
        const id = `${sourceAgentId}-${targetAgentId}-${Date.now()}`;

        // Color based on strength
        const color = new THREE.Color().lerpColors(
            new THREE.Color(0x64b5f6), // Blue (weak)
            new THREE.Color(0xffa726), // Orange (strong)
            strength
        );

        const connection: Connection = {
            id,
            sourceAgentId,
            targetAgentId,
            sourcePosition: sourcePosition.clone(),
            targetPosition: targetPosition.clone(),
            strength,
            createdAt: Date.now(),
            flowDirection: 0,
            color,
        };

        connectionsRef.current.set(id, connection);
    };

    /**
     * Get all active connections
     */
    const getConnections = (): Connection[] => {
        return Array.from(connectionsRef.current.values());
    };

    /**
     * Clean up old connections
     */
    const cleanup = (maxAge: number): void => {
        const now = Date.now();

        for (const [id, connection] of connectionsRef.current.entries()) {
            if (now - connection.createdAt > maxAge) {
                connectionsRef.current.delete(id);
            }
        }
    };

    return {
        addConnection,
        getConnections,
        cleanup,
    };
}
