'use client';

import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Shaders
import vertexShader from './shaders/holographic.vert';
import fragmentShader from './shaders/holographic.frag';

const PARTICLE_COUNT = 2000; // Start with 2k for dev

export function ParticleSystem() {
    const pointsRef = useRef<THREE.Points>(null);

    // Generate initial particles
    const { positions, colors, sizes, alphas } = useMemo(() => {
        const pos = new Float32Array(PARTICLE_COUNT * 3);
        const col = new Float32Array(PARTICLE_COUNT * 3);
        const siz = new Float32Array(PARTICLE_COUNT);
        const alp = new Float32Array(PARTICLE_COUNT);

        const color = new THREE.Color();

        for (let i = 0; i < PARTICLE_COUNT; i++) {
            // Spherical distribution
            const r = 40 * Math.cbrt(Math.random());
            const theta = Math.random() * 2 * Math.PI;
            const phi = Math.acos(2 * Math.random() - 1);

            const x = r * Math.sin(phi) * Math.cos(theta);
            const y = r * Math.sin(phi) * Math.sin(theta);
            const z = r * Math.cos(phi);

            pos[i * 3] = x;
            pos[i * 3 + 1] = y;
            pos[i * 3 + 2] = z;

            // Random Colors (Cyan/Purple/Gold palette)
            const rand = Math.random();
            if (rand > 0.6) color.setHex(0x00F0FF); // Cyan
            else if (rand > 0.3) color.setHex(0xB026FF); // Purple
            else color.setHex(0xFFD700); // Gold

            col[i * 3] = color.r;
            col[i * 3 + 1] = color.g;
            col[i * 3 + 2] = color.b;

            siz[i] = Math.random() * 2 + 1; // Base size
            alp[i] = Math.random() * 0.5 + 0.5; // Base alpha
        }

        return {
            positions: pos,
            colors: col,
            sizes: siz,
            alphas: alp
        };
    }, []);

    // Animation Loop
    useFrame((state) => {
        if (!pointsRef.current) return;

        // Slow rotation of the entire system
        pointsRef.current.rotation.y += 0.0005;
        pointsRef.current.rotation.z += 0.0002;

        // Pulse effect
        const time = state.clock.getElapsedTime();
        const sizes = pointsRef.current.geometry.attributes.size.array as Float32Array;

        // Update random particles to "pulse"
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            if (i % 100 === 0) { // Optimize loop
                sizes[i] = (Math.sin(time * 2 + i) * 1.5) + 2.5;
            }
        }
        pointsRef.current.geometry.attributes.size.needsUpdate = true;
    });

    return (
        <points ref={pointsRef}>
            <bufferGeometry>
                <bufferAttribute
                    attach="attributes-position"
                    args={[positions, 3]}
                />
                <bufferAttribute
                    attach="attributes-color"
                    args={[colors, 3]}
                />
                <bufferAttribute
                    attach="attributes-size"
                    args={[sizes, 1]}
                />
                <bufferAttribute
                    attach="attributes-alpha"
                    args={[alphas, 1]}
                />
            </bufferGeometry>
            <shaderMaterial
                vertexShader={vertexShader}
                fragmentShader={fragmentShader}
                transparent
                // additive blending happens in shader via alpha implementation, or standard blending
                blending={THREE.AdditiveBlending}
                depthWrite={false}
            />
        </points>
    );
}
