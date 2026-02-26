'use client';

/**
 * GAIA Arena - 3D Match Visualization
 * 
 * Real-time visualization of agent self-play matches with:
 * - 3D arena with agent positions
 * - Live score tracking
 * - Match timeline
 * - Leaderboard
 * - Tournament brackets
 */

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Sphere } from '@react-three/drei';
import * as THREE from 'three';
import './GAIAArena.css';
import { apiPath } from '@/lib/runtime';

// ============================================================================
// Types
// ============================================================================

interface Match {
    match_id: string;
    status: string;
    current_round: number;
    total_rounds: number;
    agent_score: number;
    opponent_score: number;
    agent_name: string;
    opponent_name: string;
}

interface LeaderboardEntry {
    rank: number;
    agent_id: string;
    elo: number;
}

// ============================================================================
// GAIA Arena Component
// ============================================================================

export function GAIAArena() {
    const [activeMatch, setActiveMatch] = useState<Match | null>(null);
    const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
    const [selectedAgent, setSelectedAgent] = useState<string>('agent_1');

    const fetchLeaderboard = useCallback(async () => {
        try {
            const res = await fetch(apiPath('/v1/gaia/leaderboard/general'));
            const data = await res.json();
            setLeaderboard(data);
        } catch (error) {
            console.error('Failed to fetch leaderboard:', error);
        }
    }, []);

    useEffect(() => {
        const initTimer = setTimeout(() => {
            void fetchLeaderboard();
        }, 0);
        const interval = setInterval(fetchLeaderboard, 5000);
        return () => {
            clearTimeout(initTimer);
            clearInterval(interval);
        };
    }, [fetchLeaderboard]);

    const handleCreateMatch = async () => {
        try {
            const res = await fetch(apiPath('/v1/gaia/match/create'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    agent1_id: 'agent_1',
                    agent2_id: 'agent_2',
                    environment: 'standard_arena'
                })
            });
            const data = await res.json();
            setActiveMatch({
                match_id: data.match_id,
                status: 'pending',
                current_round: 0,
                total_rounds: 0,
                agent_score: 0,
                opponent_score: 0,
                agent_name: selectedAgent,
                opponent_name: 'Synthetic Opponent',
            });
        } catch (error) {
            console.error('Failed to create match:', error);
        }
    };

    useEffect(() => {
        if (!activeMatch) return;

        const pollMatch = async () => {
            try {
                const res = await fetch(apiPath(`/v1/gaia/match/${activeMatch.match_id}`));
                const matchData = await res.json();

                setActiveMatch({
                    ...matchData,
                    agent_name: selectedAgent,
                    opponent_name: 'Synthetic Opponent'
                });

                if (matchData.status === 'in_progress' || matchData.status === 'pending') {
                    setTimeout(pollMatch, 500);
                } else {
                    // Match complete
                    setTimeout(() => setActiveMatch(null), 3000);
                    fetchLeaderboard(); // Refresh leaderboard
                }
            } catch (error) {
                console.error('Failed to poll match:', error);
            }
        };

        void pollMatch();
    }, [activeMatch, selectedAgent, fetchLeaderboard]);

    return (
        <div className="gaia-arena">
            {/* Header */}
            <div className="arena-header">
                <h2>⚔️ GAIA Arena</h2>
                <div className="arena-subtitle">Self-Play Training & Competition</div>
            </div>

            {/* 3D Arena */}
            <div className="arena-canvas-container">
                <Canvas camera={{ position: [0, 5, 10], fov: 60 }}>
                    <ArenaScene match={activeMatch} />
                </Canvas>
            </div>

            {/* Match Controls */}
            <div className="match-controls">
                <select
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                    className="agent-selector"
                >
                    <option value="agent_1">Agent Alpha</option>
                    <option value="agent_2">Agent Beta</option>
                    <option value="agent_3">Agent Gamma</option>
                </select>

                <button
                    onClick={handleCreateMatch}
                    disabled={!!activeMatch}
                    className="start-match-btn"
                >
                    {activeMatch ? '⏳ Match in Progress...' : '⚔️ Start Match'}
                </button>
            </div>

            {/* Active Match Display */}
            {activeMatch && (
                <div className="active-match-display">
                    <MatchCard match={activeMatch} />
                </div>
            )}

            {/* Leaderboard */}
            <div className="leaderboard-section">
                <h3>🏆 Leaderboard</h3>
                <Leaderboard entries={leaderboard} />
            </div>
        </div>
    );
}

// ============================================================================
// 3D Arena Scene
// ============================================================================

function ArenaScene({ match }: { match: Match | null }) {
    return (
        <>
            {/* Lighting */}
            <ambientLight intensity={0.5} />
            <pointLight position={[10, 10, 10]} intensity={1} />
            <pointLight position={[-10, -10, -10]} intensity={0.5} />

            {/* Arena Floor */}
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]} receiveShadow>
                <planeGeometry args={[20, 20]} />
                <meshStandardMaterial color="#1a1a2e" />
            </mesh>

            {/* Grid */}
            <gridHelper args={[20, 20, '#667eea', '#333']} position={[0, -1.99, 0]} />

            {/* Agent Positions */}
            {match ? (
                <>
                    <AgentSphere
                        position={[-4, 0, 0]}
                        name={match.agent_name}
                        score={match.agent_score}
                        color="#667eea"
                        isWinning={match.agent_score > match.opponent_score}
                    />
                    <AgentSphere
                        position={[4, 0, 0]}
                        name={match.opponent_name}
                        score={match.opponent_score}
                        color="#ef5350"
                        isWinning={match.opponent_score > match.agent_score}
                    />

                    {/* VS Text */}
                    <Text
                        position={[0, 1, 0]}
                        fontSize={0.8}
                        color="#ffffff"
                        anchorX="center"
                        anchorY="middle"
                    >
                        VS
                    </Text>

                    {/* Round Indicator */}
                    <Text
                        position={[0, -1.5, 0]}
                        fontSize={0.4}
                        color="#888"
                        anchorX="center"
                    >
                        Round {match.current_round}/{match.total_rounds}
                    </Text>
                </>
            ) : (
                <Text
                    position={[0, 0, 0]}
                    fontSize={0.6}
                    color="#666"
                    anchorX="center"
                    anchorY="middle"
                >
                    Start a match to begin
                </Text>
            )}

            <OrbitControls enablePan={false} maxDistance={15} minDistance={5} />
        </>
    );
}

// ============================================================================
// Agent Sphere
// ============================================================================

function AgentSphere({
    position,
    name,
    score,
    color,
    isWinning
}: {
    position: [number, number, number];
    name: string;
    score: number;
    color: string;
    isWinning: boolean;
}) {
    const meshRef = useRef<THREE.Mesh>(null);

    useFrame((state) => {
        if (meshRef.current) {
            // Gentle floating animation
            meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime) * 0.2;

            // Rotate if winning
            if (isWinning) {
                meshRef.current.rotation.y += 0.02;
            }
        }
    });

    return (
        <group position={position}>
            {/* Sphere */}
            <Sphere ref={meshRef} args={[0.8, 32, 32]} castShadow>
                <meshStandardMaterial
                    color={color}
                    emissive={color}
                    emissiveIntensity={isWinning ? 0.5 : 0.2}
                    metalness={0.8}
                    roughness={0.2}
                />
            </Sphere>

            {/* Glow ring for winner */}
            {isWinning && (
                <mesh rotation={[Math.PI / 2, 0, 0]}>
                    <torusGeometry args={[1.2, 0.05, 16, 32]} />
                    <meshBasicMaterial color={color} transparent opacity={0.6} />
                </mesh>
            )}

            {/* Name label */}
            <Text
                position={[0, -1.5, 0]}
                fontSize={0.3}
                color="white"
                anchorX="center"
            >
                {name}
            </Text>

            {/* Score */}
            <Text
                position={[0, -2, 0]}
                fontSize={0.5}
                color={color}
                anchorX="center"
                fontWeight="bold"
            >
                {score.toFixed(1)}
            </Text>
        </group>
    );
}

// ============================================================================
// Match Card
// ============================================================================

function MatchCard({ match }: { match: Match }) {
    const agentWinning = match.agent_score > match.opponent_score;
    const progress = (match.current_round / match.total_rounds) * 100;

    return (
        <div className="match-card">
            <div className="match-header">
                <div className="match-status">
                    <span className={`status-badge status-${match.status}`}>
                        {match.status.toUpperCase()}
                    </span>
                </div>
            </div>

            <div className="match-scoreboard">
                <div className={`score-item ${agentWinning ? 'winning' : ''}`}>
                    <div className="score-name">{match.agent_name}</div>
                    <div className="score-value">{match.agent_score.toFixed(1)}</div>
                </div>

                <div className="score-divider">-</div>

                <div className={`score-item ${!agentWinning && match.opponent_score > match.agent_score ? 'winning' : ''}`}>
                    <div className="score-value">{match.opponent_score.toFixed(1)}</div>
                    <div className="score-name">{match.opponent_name}</div>
                </div>
            </div>

            {/* Progress */}
            <div className="match-progress">
                <div className="progress-bar-container">
                    <div className="progress-bar" style={{ width: `${progress}%` }} />
                </div>
                <div className="progress-label">
                    Round {match.current_round} of {match.total_rounds}
                </div>
            </div>
        </div>
    );
}

// ============================================================================
// Leaderboard
// ============================================================================

function Leaderboard({ entries }: { entries: LeaderboardEntry[] }) {
    if (entries.length === 0) {
        return <div className="no-data">No rankings yet</div>;
    }

    return (
        <div className="leaderboard">
            {entries.map((entry) => (
                <div key={entry.agent_id} className="leaderboard-entry">
                    <div className={`rank rank-${entry.rank}`}>#{entry.rank}</div>
                    <div className="agent-name">{entry.agent_id}</div>
                    <div className="elo-rating">{Math.round(entry.elo)} ELO</div>
                    <div className="elo-bar">
                        <div
                            className="elo-fill"
                            style={{
                                width: `${((entry.elo - 1000) / 1000) * 100}%`
                            }}
                        />
                    </div>
                </div>
            ))}
        </div>
    );
}
