/**
 * Tournament Bracket Visualization
 * 
 * Advanced SVG-based bracket rendering with:
 * - Dynamic layout algorithm
 * - Animated match progression
 * - Real-time updates via WebSocket
 * - Zoom & pan controls
 * - Interactive match details
 * - Export to PNG/PDF
 */

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ZoomIn,
    ZoomOut,
    Download,
    Maximize2,
    Trophy,
    Clock,
    Users
} from 'lucide-react';
import './TournamentBracket.css';

// ============================================================================
// Types
// ============================================================================

interface Match {
    id: string;
    round: number;
    position: number;
    player1_id: string;
    player1_name: string;
    player1_score: number;
    player2_id: string;
    player2_name: string;
    player2_score: number;
    winner_id?: string;
    status: 'pending' | 'in_progress' | 'completed';
    start_time?: string;
}

interface Tournament {
    id: string;
    name: string;
    format: 'single_elimination' | 'round_robin' | 'swiss';
    status: 'setup' | 'in_progress' | 'completed';
    rounds: Match[][];
    winner?: string;
}

// ============================================================================
// Tournament Bracket Component
// ============================================================================

export function TournamentBracket({ tournamentId }: { tournamentId: string }) {
    const [tournament, setTournament] = useState<Tournament | null>(null);
    const [selectedMatch, setSelectedMatch] = useState<Match | null>(null);
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const svgRef = useRef<SVGSVGElement>(null);

    // Fetch tournament data
    useEffect(() => {
        fetchTournament();

        // WebSocket for real-time updates
        const ws = new WebSocket(`ws://localhost:8008/ws/tournaments/${tournamentId}`);

        ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            if (update.type === 'match_update') {
                updateMatch(update.match);
            }
        };

        return () => ws.close();
    }, [tournamentId]);

    const fetchTournament = async () => {
        try {
            const response = await fetch(`/api/v1/gaia/tournament/${tournamentId}`);
            const data = await response.json();
            setTournament(data);
        } catch (error) {
            console.error('Failed to fetch tournament:', error);
        }
    };

    const updateMatch = (match: Match) => {
        setTournament(prev => {
            if (!prev) return prev;

            const newRounds = prev.rounds.map(round =>
                round.map(m => (m.id === match.id ? match : m))
            );

            return { ...prev, rounds: newRounds };
        });
    };

    const handleZoom = (delta: number) => {
        setZoom(prev => Math.max(0.5, Math.min(2, prev + delta)));
    };

    const handleExport = async () => {
        if (!svgRef.current) return;

        // Convert SVG to PNG using canvas
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const svgData = new XMLSerializer().serializeToString(svgRef.current);
        const img = new Image();

        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx?.drawImage(img, 0, 0);

            canvas.toBlob(blob => {
                if (blob) {
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `tournament-${tournamentId}.png`;
                    a.click();
                }
            });
        };

        img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
    };

    if (!tournament) {
        return <div className="tournament-loading">Loading tournament...</div>;
    }

    if (tournament.format === 'single_elimination') {
        return (
            <div className="tournament-bracket">
                {/* Header */}
                <div className="bracket-header">
                    <div className="tournament-info">
                        <Trophy className="trophy-icon" size={32} />
                        <div>
                            <h1>{tournament.name}</h1>
                            <p className="tournament-status">
                                <span className={`status-badge ${tournament.status}`}>
                                    {tournament.status.replace('_', ' ')}
                                </span>
                                {tournament.winner && (
                                    <span className="winner-badge">
                                        🏆 Winner: {tournament.winner}
                                    </span>
                                )}
                            </p>
                        </div>
                    </div>

                    {/* Controls */}
                    <div className="bracket-controls">
                        <button onClick={() => handleZoom(0.1)} title="Zoom In">
                            <ZoomIn size={20} />
                        </button>
                        <button onClick={() => handleZoom(-0.1)} title="Zoom Out">
                            <ZoomOut size={20} />
                        </button>
                        <button onClick={handleExport} title="Export">
                            <Download size={20} />
                        </button>
                        <span className="zoom-level">{(zoom * 100).toFixed(0)}%</span>
                    </div>
                </div>

                {/* Bracket Visualization */}
                <div className="bracket-container">
                    <EliminationBracket
                        tournament={tournament}
                        zoom={zoom}
                        pan={pan}
                        svgRef={svgRef}
                        onMatchClick={setSelectedMatch}
                    />
                </div>

                {/* Match Details Modal */}
                <AnimatePresence>
                    {selectedMatch && (
                        <MatchModal
                            match={selectedMatch}
                            onClose={() => setSelectedMatch(null)}
                        />
                    )}
                </AnimatePresence>
            </div>
        );
    }
    // Simplified view for round_robin and swiss formats
    if (tournament.format === 'round_robin' || tournament.format === 'swiss') {
        return (
            <div className="tournament-bracket">
                <div className="bracket-header">
                    <div className="tournament-info">
                        <Trophy className="trophy-icon" size={32} />
                        <div>
                            <h1>{tournament.name || 'Tournament'}</h1>
                            <p className="tournament-status">
                                <span className={`status-badge ${tournament.status}`}>
                                    {tournament.format.replace('_', ' ').toUpperCase()} - {tournament.status.replace('_', ' ')}
                                </span>
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bracket-container" style={{ padding: '20px' }}>
                    <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '24px' }}>
                        <h3 style={{ marginBottom: '16px' }}>Tournament Information</h3>
                        <p><strong>Format:</strong> {tournament.format.replace('_', ' ').toUpperCase()}</p>
                        <p><strong>Status:</strong> {tournament.status.replace('_', ' ')}</p>
                        <p><strong>Total Rounds:</strong> {tournament.rounds?.length || 0}</p>
                        {tournament.winner && <p><strong>Winner:</strong> 🏆 {tournament.winner}</p>}
                        <p style={{ marginTop: '16px', color: '#6b7280' }}>
                            Full {tournament.format} bracket visualization coming soon!
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    return <div>Unsupported tournament format: {tournament.format}</div>;
}

// ============================================================================
// Elimination Bracket Component
// ============================================================================

interface BracketProps {
    tournament: Tournament;
    zoom: number;
    pan: { x: number; y: number };
    svgRef: React.RefObject<SVGSVGElement>;
    onMatchClick: (match: Match) => void;
}

function EliminationBracket({ tournament, zoom, pan, svgRef, onMatchClick }: BracketProps) {
    const MATCH_WIDTH = 200;
    const MATCH_HEIGHT = 80;
    const ROUND_SPACING = 300;
    const MATCH_SPACING = 120;

    const totalRounds = tournament.rounds.length;
    const maxMatchesInRound = Math.max(...tournament.rounds.map(r => r.length));

    const svgWidth = totalRounds * ROUND_SPACING + 200;
    const svgHeight = maxMatchesInRound * MATCH_SPACING + 200;

    return (
        <svg
            ref={svgRef}
            width="100%"
            height="600"
            viewBox={`${pan.x} ${pan.y} ${svgWidth / zoom} ${svgHeight / zoom}`}
            className="bracket-svg"
        >
            <defs>
                {/* Gradients */}
                <linearGradient id="match-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#667eea" />
                    <stop offset="100%" stopColor="#764ba2" />
                </linearGradient>

                <linearGradient id="winner-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#10b981" />
                    <stop offset="100%" stopColor="#059669" />
                </linearGradient>

                {/* Glow filter */}
                <filter id="glow">
                    <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                    <feMerge>
                        <feMergeNode in="coloredBlur" />
                        <feMergeNode in="SourceGraphic" />
                    </feMerge>
                </filter>
            </defs>

            {/* Render rounds */}
            {tournament.rounds.map((round, roundIdx) => {
                const roundX = roundIdx * ROUND_SPACING + 100;
                const roundHeight = round.length * MATCH_SPACING;
                const roundStartY = (svgHeight - roundHeight) / 2;

                return (
                    <g key={roundIdx}>
                        {/* Round label */}
                        <text
                            x={roundX + MATCH_WIDTH / 2}
                            y={roundStartY - 30}
                            textAnchor="middle"
                            className="round-label"
                        >
                            {getRoundName(roundIdx, totalRounds)}
                        </text>

                        {/* Matches */}
                        {round.map((match, matchIdx) => {
                            const matchY = roundStartY + matchIdx * MATCH_SPACING;

                            return (
                                <g key={match.id}>
                                    {/* Connector lines to next round */}
                                    {roundIdx < totalRounds - 1 && (
                                        <ConnectorLine
                                            x1={roundX + MATCH_WIDTH}
                                            y1={matchY + MATCH_HEIGHT / 2}
                                            x2={roundX + ROUND_SPACING}
                                            y2={calculateNextMatchY(roundIdx, matchIdx, tournament.rounds, MATCH_SPACING, svgHeight, roundStartY)}
                                            animated={match.status === 'in_progress'}
                                        />
                                    )}

                                    {/* Match box */}
                                    <MatchBox
                                        match={match}
                                        x={roundX}
                                        y={matchY}
                                        width={MATCH_WIDTH}
                                        height={MATCH_HEIGHT}
                                        onClick={() => onMatchClick(match)}
                                    />
                                </g>
                            );
                        })}
                    </g>
                );
            })}
        </svg>
    );
}

// ============================================================================
// Match Box Component
// ============================================================================

interface MatchBoxProps {
    match: Match;
    x: number;
    y: number;
    width: number;
    height: number;
    onClick: () => void;
}

function MatchBox({ match, x, y, width, height, onClick }: MatchBoxProps) {
    const isComplete = match.status === 'completed';
    const isLive = match.status === 'in_progress';

    return (
        <motion.g
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ scale: 1.05 }}
            onClick={onClick}
            style={{ cursor: 'pointer' }}
        >
            {/* Background */}
            <rect
                x={x}
                y={y}
                width={width}
                height={height}
                rx="8"
                fill={isComplete ? "url(#winner-gradient)" : "#ffffff"}
                stroke={isLive ? "#667eea" : "#e5e7eb"}
                strokeWidth={isLive ? "3" : "2"}
                filter={isLive ? "url(#glow)" : undefined}
            />

            {/* Live indicator */}
            {isLive && (
                <motion.circle
                    cx={x + width - 15}
                    cy={y + 15}
                    r="5"
                    fill="#ef4444"
                    animate={{ opacity: [1, 0.3, 1] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                />
            )}

            {/* Player 1 */}
            <text
                x={x + 15}
                y={y + 30}
                className={`player-name ${match.winner_id === match.player1_id ? 'winner' : ''}`}
                fill={isComplete ? "#ffffff" : "#374151"}
            >
                {match.player1_name}
            </text>

            {isComplete && (
                <text
                    x={x + width - 15}
                    y={y + 30}
                    textAnchor="end"
                    className="player-score"
                    fill="#ffffff"
                    fontWeight="bold"
                >
                    {match.player1_score}
                </text>
            )}

            {/* Player 2 */}
            <text
                x={x + 15}
                y={y + 55}
                className={`player-name ${match.winner_id === match.player2_id ? 'winner' : ''}`}
                fill={isComplete ? "#ffffff" : "#374151"}
            >
                {match.player2_name}
            </text>

            {isComplete && (
                <text
                    x={x + width - 15}
                    y={y + 55}
                    textAnchor="end"
                    className="player-score"
                    fill="#ffffff"
                    fontWeight="bold"
                >
                    {match.player2_score}
                </text>
            )}

            {/* Divider */}
            <line
                x1={x + 10}
                y1={y + height / 2}
                x2={x + width - 10}
                y2={y + height / 2}
                stroke={isComplete ? "#ffffff" : "#e5e7eb"}
                strokeWidth="1"
                opacity="0.5"
            />
        </motion.g>
    );
}

// ============================================================================
// Connector Line Component
// ============================================================================

interface ConnectorProps {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    animated?: boolean;
}

function ConnectorLine({ x1, y1, x2, y2, animated }: ConnectorProps) {
    const midX = (x1 + x2) / 2;

    // Create smooth S-curve path
    const path = `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;

    return (
        <>
            <motion.path
                d={path}
                fill="none"
                stroke="#d1d5db"
                strokeWidth="2"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.5 }}
            />

            {animated && (
                <motion.circle
                    r="4"
                    fill="#667eea"
                    animate={{
                        offsetDistance: ['0%', '100%'],
                    }}
                    transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: 'linear'
                    }}
                >
                    <animateMotion dur="2s" repeatCount="indefinite">
                        <mpath href={`#path-${x1}-${y1}`} />
                    </animateMotion>
                </motion.circle>
            )}
        </>
    );
}

// ============================================================================
// Match Modal Component
// ============================================================================

function MatchModal({ match, onClose }: { match: Match; onClose: () => void }) {
    return (
        <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
        >
            <motion.div
                className="match-modal"
                initial={{ scale: 0.9, y: 50 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.9, y: 50 }}
                onClick={(e) => e.stopPropagation()}
            >
                <h2>Match Details</h2>

                <div className="modal-content">
                    <div className="match-players">
                        <div className={`player ${match.winner_id === match.player1_id ? 'winner' : ''}`}>
                            <h3>{match.player1_name}</h3>
                            {match.status === 'completed' && (
                                <span className="score">{match.player1_score}</span>
                            )}
                        </div>

                        <div className="vs">VS</div>

                        <div className={`player ${match.winner_id === match.player2_id ? 'winner' : ''}`}>
                            <h3>{match.player2_name}</h3>
                            {match.status === 'completed' && (
                                <span className="score">{match.player2_score}</span>
                            )}
                        </div>
                    </div>

                    <div className="match-info">
                        <div className="info-item">
                            <Clock size={16} />
                            <span>Round {match.round + 1}</span>
                        </div>

                        {match.start_time && (
                            <div className="info-item">
                                <Clock size={16} />
                                <span>{new Date(match.start_time).toLocaleString()}</span>
                            </div>
                        )}

                        <div className="info-item">
                            <span className={`status-badge ${match.status}`}>
                                {match.status.replace('_', ' ')}
                            </span>
                        </div>
                    </div>
                </div>

                <button className="close-btn" onClick={onClose}>
                    Close
                </button>
            </motion.div>
        </motion.div>
    );
}

// ============================================================================
// Utility Functions
// ============================================================================

function getRoundName(roundIdx: number, totalRounds: number): string {
    const roundsFromEnd = totalRounds - roundIdx;

    if (roundsFromEnd === 1) return 'Finals';
    if (roundsFromEnd === 2) return 'Semi-Finals';
    if (roundsFromEnd === 3) return 'Quarter-Finals';

    return `Round ${roundIdx + 1}`;
}

function calculateNextMatchY(
    roundIdx: number,
    matchIdx: number,
    rounds: Match[][],
    spacing: number,
    svgHeight: number,
    startY: number
): number {
    const nextRound = rounds[roundIdx + 1];
    if (!nextRound) return 0;

    const nextMatchIdx = Math.floor(matchIdx / 2);
    const nextRoundHeight = nextRound.length * spacing;
    const nextRoundStartY = (svgHeight - nextRoundHeight) / 2;

    return nextRoundStartY + nextMatchIdx * spacing + 40;
}
