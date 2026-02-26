'use client';

import { useThree } from '@react-three/fiber';
import { useEffect, useMemo } from 'react';
import * as THREE from 'three';

export interface SceneConfig {
    cameraPosition?: [number, number, number];
    fov?: number;
    enableFog?: boolean;
}

export const useThreeScene = ({
    cameraPosition = [15, 15, 15],
    enableFog = true,
}: Omit<SceneConfig, 'fov'> = {}) => {
    const { camera, scene, gl, size } = useThree();
    const fog = useMemo(
        () => (enableFog ? new THREE.FogExp2('#000F1A', 0.02) : null),
        [enableFog]
    );

    useEffect(() => {
        // Camera Setup
        camera.position.set(...cameraPosition);
        camera.lookAt(0, 0, 0);

        // Renderer Optimization
        gl.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Limit dpr to 2 for performance

    }, [camera, gl, cameraPosition]);

    return { camera, scene, gl, size, fog };
};
