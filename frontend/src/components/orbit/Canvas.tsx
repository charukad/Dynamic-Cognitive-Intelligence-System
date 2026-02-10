'use client';

import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars, Stats } from '@react-three/drei';
import { Suspense } from 'react';
import { useThreeScene } from '@/hooks/useThreeScene';
import * as THREE from 'three';
import { EffectComposer, Bloom, ChromaticAberration } from '@react-three/postprocessing';

interface SwarmCanvasProps {
    children?: React.ReactNode;
}

import { ParticleSystem } from './ParticleSystem';
import { SynapseSystem } from './SynapseSystem';
import { ForceDirectedLayout } from '../cortex/ForceDirectedLayout';
import { useUIStore } from "@/store/uiStore"

function SceneSetup() {
    useThreeScene();
    return null;
}

export function SwarmCanvas({ children }: SwarmCanvasProps) {
    const { settings } = useUIStore()

    return (
        <div className="w-full h-full absolute inset-0 bg-[#000F1A]">
            <Canvas
                dpr={[1, 2]} // Dynamic pixel ratio for performance
                gl={{
                    antialias: false, // Antialias off for postprocessing
                    toneMapping: THREE.ReinhardToneMapping,
                    toneMappingExposure: 1.5,
                    powerPreference: "high-performance",
                }}
                camera={{ position: [20, 10, 20], fov: 45 }}
            >
                <Suspense fallback={null}>
                    <SceneSetup />

                    <ParticleSystem />
                    <SynapseSystem />
                    <ForceDirectedLayout /> { /* The Cortex */}

                    {/* Environment / Lighting */}
                    <ambientLight intensity={0.2} color="#00F0FF" /> {/* Cyan ambient */}
                    <pointLight position={[10, 10, 10]} intensity={1} color="#B026FF" /> {/* Purple accent */}

                    <Stars
                        radius={100}
                        depth={50}
                        count={5000}
                        factor={4}
                        saturation={0}
                        fade
                        speed={1}
                    />

                    {settings.enablePostProcessing && (
                        <EffectComposer>
                            <Bloom luminanceThreshold={1} mipmapBlur intensity={1.5} radius={0.4} />
                            <ChromaticAberration offset={[0.002, 0.002] as [number, number]} />
                        </EffectComposer>
                    )}

                    {/* Interactive Controls */}
                    <OrbitControls
                        enablePan={true}
                        enableZoom={true}
                        enableRotate={true}
                        maxDistance={100}
                        minDistance={5}
                        dampingFactor={0.05}
                    />

                    {children}

                    {/* Dev Tools */}
                    {process.env.NODE_ENV === 'development' && <Stats />}
                </Suspense>
            </Canvas>
        </div>
    );
}
