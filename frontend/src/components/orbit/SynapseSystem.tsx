'use client';

import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { QuadraticBezierLine } from '@react-three/drei';
import * as THREE from 'three';

// Simulate active connections
const CONNECTION_COUNT = 5;

// Helper to get random point in sphere
function getRandomPoint() {
    const r = 20 * Math.cbrt(Math.random());
    const theta = Math.random() * 2 * Math.PI;
    const phi = Math.acos(2 * Math.random() - 1);
    return new THREE.Vector3(
        r * Math.sin(phi) * Math.cos(theta),
        r * Math.sin(phi) * Math.sin(theta),
        r * Math.cos(phi)
    );
}

export function SynapseSystem() {
    // We'll regenerate connections every few seconds for visual effect
    // In real app, this would be driven by Socket.io events
    const [connections, setConnections] = useState(() =>
        Array.from({ length: CONNECTION_COUNT }).map(() => ({
            start: getRandomPoint(),
            end: getRandomPoint(),
            mid: new THREE.Vector3(0, 0, 0), // Will compute dynamically
            color: Math.random() > 0.5 ? '#00F0FF' : '#B026FF',
            id: Math.random()
        }))
    );

    // Animation refs
    const linesRef = useRef<Array<any>>([]);

    // Re-roll connections periodically
    useFrame((state, delta) => {
        const time = state.clock.elapsedTime;

        // Animate dashes
        linesRef.current.forEach(line => {
            if (line && line.material) {
                line.material.dashOffset -= delta * 2; // Speed of flow
            }
        });

        if (Math.floor(time) % 3 === 0 && Math.random() > 0.95) {
            // Occasionally replace one connection
            setConnections(prev => {
                const next = [...prev];
                next.shift();
                next.push({
                    start: getRandomPoint(),
                    end: getRandomPoint(),
                    mid: new THREE.Vector3(0, 0, 0),
                    color: Math.random() > 0.5 ? '#00F0FF' : '#B026FF',
                    id: Math.random()
                });
                return next;
            });
        }
    });

    return (
        <group>
            {connections.map((conn, i) => (
                <QuadraticBezierLine
                    key={conn.id}
                    ref={el => { linesRef.current[i] = el; }}
                    start={conn.start}
                    end={conn.end}
                    mid={conn.start.clone().lerp(conn.end, 0.5).add(new THREE.Vector3(0, 5, 0))} // Arc upwards
                    color={conn.color}
                    lineWidth={2}
                    dashed={true}
                    dashScale={2}
                    gapSize={1}
                    opacity={0.6}
                    transparent
                />
            ))}
        </group>
    );
}
