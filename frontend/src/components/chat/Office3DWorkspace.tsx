'use client';

import React, { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import type { Group } from 'three';

export type Office3DStatus = 'active' | 'watching' | 'idle' | 'alert';
export type Office3DSeverity = 'info' | 'success' | 'warning' | 'critical';

export interface Office3DRoom {
    id: string;
    title: string;
    label: string;
    status: Office3DStatus;
    metric: string;
}

export interface Office3DAgent {
    id: string;
    name: string;
    roomId: string;
    status: Office3DStatus;
    task: string;
}

export interface Office3DTask {
    id: string;
    roomId: string;
    type: string;
    description: string;
    severity: Office3DSeverity;
}

interface Office3DWorkspaceProps {
    rooms: Office3DRoom[];
    activeRoomId: string;
    agents: Office3DAgent[];
    tasks: Office3DTask[];
    onRoomSelect: (roomId: string) => void;
}

const ROOM_LAYOUT: Record<string, [number, number, number]> = {
    strategy: [0, 0, 0],
    boss: [-2.6, 0, -1.4],
    voting: [2.6, 0, -1.4],
    collaboration: [-2.7, 0, 1.8],
    memory: [2.7, 0, 1.8],
    incubator: [-0.8, 0, 3.2],
    execution: [0.8, 0, 3.2],
};

const STATUS_COLORS: Record<Office3DStatus, string> = {
    active: '#22c55e',
    watching: '#38bdf8',
    idle: '#64748b',
    alert: '#ef4444',
};

const TASK_COLORS: Record<Office3DSeverity, string> = {
    info: '#38bdf8',
    success: '#22c55e',
    warning: '#f59e0b',
    critical: '#ef4444',
};

function truncateLabel(value: string, max = 22) {
    if (value.length <= max) {
        return value;
    }
    return `${value.slice(0, max - 1)}…`;
}

function phaseFromId(value: string) {
    let hash = 0;
    for (let index = 0; index < value.length; index += 1) {
        hash = ((hash << 5) - hash + value.charCodeAt(index)) | 0;
    }
    const normalized = Math.abs(hash % 628) / 100;
    return normalized;
}

function RoomPod({
    room,
    position,
    isActive,
    onSelect,
}: {
    room: Office3DRoom;
    position: [number, number, number];
    isActive: boolean;
    onSelect: () => void;
}) {
    const glow = STATUS_COLORS[room.status];
    return (
        <group position={position}>
            <mesh position={[0, -0.2, 0]} onClick={onSelect}>
                <cylinderGeometry args={[1.1, 1.25, 0.3, 32]} />
                <meshStandardMaterial color="#0f172a" metalness={0.3} roughness={0.5} />
            </mesh>
            <mesh position={[0, 0.15, 0]} onClick={onSelect}>
                <boxGeometry args={[1.45, 0.52, 1.05]} />
                <meshStandardMaterial
                    color={isActive ? '#1d4ed8' : '#1e293b'}
                    emissive={glow}
                    emissiveIntensity={isActive ? 0.35 : 0.12}
                    metalness={0.35}
                    roughness={0.45}
                />
            </mesh>
            <Text
                position={[0, 0.74, 0]}
                fontSize={0.15}
                color="#e2e8f0"
                maxWidth={2}
                textAlign="center"
                anchorX="center"
                anchorY="middle"
            >
                {truncateLabel(room.title, 20)}
            </Text>
            <Text
                position={[0, 0.52, 0]}
                fontSize={0.1}
                color={glow}
                maxWidth={2}
                textAlign="center"
                anchorX="center"
                anchorY="middle"
            >
                {room.status.toUpperCase()}
            </Text>
        </group>
    );
}

function AgentBody({ agent, position }: { agent: Office3DAgent; position: [number, number, number] }) {
    const groupRef = useRef<Group>(null);
    const baseY = 0.55;
    const phase = useMemo(() => phaseFromId(agent.id), [agent.id]);
    const color = STATUS_COLORS[agent.status];

    useFrame(({ clock }) => {
        if (!groupRef.current) return;
        groupRef.current.position.y = baseY + Math.sin(clock.elapsedTime * 2 + phase) * 0.06;
    });

    return (
        <group ref={groupRef} position={[position[0], baseY, position[2] + 0.55]}>
            <mesh>
                <capsuleGeometry args={[0.16, 0.38, 6, 12]} />
                <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.12} />
            </mesh>
            <mesh position={[0, 0.42, 0]}>
                <sphereGeometry args={[0.15, 16, 16]} />
                <meshStandardMaterial color="#e2e8f0" roughness={0.4} metalness={0.1} />
            </mesh>
            <Text
                position={[0, 0.77, 0]}
                fontSize={0.09}
                color="#bfdbfe"
                maxWidth={2}
                textAlign="center"
                anchorX="center"
                anchorY="middle"
            >
                {truncateLabel(agent.name, 18)}
            </Text>
            <Text
                position={[0, 0.62, 0]}
                fontSize={0.075}
                color="#f8fafc"
                maxWidth={2.2}
                textAlign="center"
                anchorX="center"
                anchorY="middle"
            >
                {truncateLabel(agent.task, 28)}
            </Text>
        </group>
    );
}

function TaskPulse({
    task,
    position,
}: {
    task: Office3DTask;
    position: [number, number, number];
}) {
    return (
        <group position={[position[0], 1.03, position[2]]}>
            <mesh>
                <sphereGeometry args={[0.08, 12, 12]} />
                <meshStandardMaterial color={TASK_COLORS[task.severity]} emissive={TASK_COLORS[task.severity]} emissiveIntensity={0.35} />
            </mesh>
            <Text
                position={[0, 0.2, 0]}
                fontSize={0.08}
                color="#e2e8f0"
                maxWidth={2.4}
                textAlign="center"
                anchorX="center"
                anchorY="middle"
            >
                {truncateLabel(task.type, 26)}
            </Text>
        </group>
    );
}

export function Office3DWorkspace({
    rooms,
    activeRoomId,
    agents,
    tasks,
    onRoomSelect,
}: Office3DWorkspaceProps) {
    const roomPositions = useMemo(() => {
        const positions = new Map<string, [number, number, number]>();
        rooms.forEach((room, index) => {
            const predefined = ROOM_LAYOUT[room.id];
            if (predefined) {
                positions.set(room.id, predefined);
                return;
            }
            const angle = (index / Math.max(1, rooms.length)) * Math.PI * 2;
            positions.set(room.id, [Math.cos(angle) * 3.2, 0, Math.sin(angle) * 2.4]);
        });
        return positions;
    }, [rooms]);

    const latestTaskPerRoom = useMemo(() => {
        const byRoom = new Map<string, Office3DTask>();
        tasks.forEach((task) => {
            if (!byRoom.has(task.roomId)) {
                byRoom.set(task.roomId, task);
            }
        });
        return byRoom;
    }, [tasks]);

    return (
        <div className="office-3d-stage">
            <Canvas className="office-3d-canvas" camera={{ position: [0, 6.8, 8.6], fov: 42 }}>
                <color attach="background" args={['#050b11']} />
                <ambientLight intensity={0.58} />
                <directionalLight position={[8, 10, 6]} intensity={0.95} />
                <pointLight position={[0, 3.8, 0]} intensity={0.65} color="#38bdf8" />

                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.36, 0]}>
                    <planeGeometry args={[14, 12]} />
                    <meshStandardMaterial color="#0b1220" metalness={0.15} roughness={0.85} />
                </mesh>

                {rooms.map((room) => {
                    const position = roomPositions.get(room.id) ?? [0, 0, 0];
                    const task = latestTaskPerRoom.get(room.id);
                    return (
                        <React.Fragment key={room.id}>
                            <RoomPod
                                room={room}
                                position={position}
                                isActive={room.id === activeRoomId}
                                onSelect={() => onRoomSelect(room.id)}
                            />
                            {task && <TaskPulse task={task} position={position} />}
                        </React.Fragment>
                    );
                })}

                {agents.map((agent) => {
                    const position = roomPositions.get(agent.roomId);
                    if (!position) return null;
                    return <AgentBody key={agent.id} agent={agent} position={position} />;
                })}

                <OrbitControls
                    enablePan={false}
                    enableDamping
                    dampingFactor={0.08}
                    minDistance={5.5}
                    maxDistance={13}
                    minPolarAngle={0.6}
                    maxPolarAngle={1.45}
                    target={[0, 0.35, 0]}
                />
            </Canvas>

            <div className="office-3d-room-controls" role="group" aria-label="Office rooms">
                {rooms.map((room) => (
                    <button
                        key={room.id}
                        type="button"
                        className={`office-3d-room-button ${room.id === activeRoomId ? 'active' : ''} status-${room.status}`}
                        onClick={() => onRoomSelect(room.id)}
                        aria-pressed={room.id === activeRoomId}
                    >
                        <span>{room.title}</span>
                        <small>{room.status}</small>
                    </button>
                ))}
            </div>
        </div>
    );
}
