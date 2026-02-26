'use client';

/**
 * Dream Viewer Component - Real - time Dream Cycle Visualization
 * 
 * Displays ongoing and completed dream cycles with phase progression,
 * insight extraction, and performance metrics.
 */

'use client';

import { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import './DreamViewer.css';
import { apiPath } from '@/lib/runtime';

// ============================================================================
// Types
// ============================================================================

interface DreamCycle {
    cycle_id: string;
    agent_id: string;
    phase: 'rem' | 'nrem' | 'integration' | null;
    progress: number;
    insights_count: number;
    duration_seconds: number;
    status: 'running' | 'completed' | 'failed';
    start_time: string;
}

interface Insight {
    id: string;
    type: 'strategy_improvement' | 'pattern_recognition' | 'knowledge_gap' | 'heuristic_update' | 'risk_assessment';
    content: string;
    confidence: number;
    impact_score: number;
    timestamp: string;
    applied: boolean;
}

// ============================================================================
// Dream Viewer Component
// ============================================================================

export function DreamViewer({ agentId }: { agentId: string }) {
    const [activeCycle, setActiveCycle] = useState<DreamCycle | null>(null);
    const [insights, setInsights] = useState<Insight[]>([]);
    const [performanceHistory] = useState<number[]>([]);
    const [loading, setLoading] = useState(true);

    // Fetch dream status
    useEffect(() => {
        const fetchDreamStatus = async () => {
            try {
                // Get latest insights
                const insightsRes = await fetch(
                    apiPath(`/v1/oneiroi/insights/${agentId}?limit=20`)
                );
                const insightsData = await insightsRes.json();
                setInsights(insightsData.insights);

                setLoading(false);
            } catch (error) {
                console.error('Failed to fetch dream data:', error);
                setLoading(false);
            }
        };

        fetchDreamStatus();

        // Poll every 2 seconds for active cycles
        const interval = setInterval(fetchDreamStatus, 2000);
        return () => clearInterval(interval);
    }, [agentId]);

    if (loading) {
        return (
            <div className="dream-viewer-loading">
                <div className="loader" />
                <p>Loading dream data...</p>
            </div>
        );
    }

    return (
        <div className="dream-viewer">
            {/* Header */}
            <div className="dream-viewer-header">
                <h2>🌙 Oneiroi Dream Viewer</h2>
                <div className="agent-badge">Agent: {agentId}</div>
            </div>

            {/* Active Dream Cycle */}
            {activeCycle && (
                <div className="active-dream-section">
                    <h3>Active Dream Cycle</h3>
                    <DreamCycleCard cycle={activeCycle} />
                </div>
            )}

            {/* Initiate Dream Button */}
            {!activeCycle && (
                <div className="dream-actions">
                    <button
                        className="initiate-dream-btn"
                        onClick={() => initiateDream(agentId, setActiveCycle)}
                    >
                        🌙 Initiate Dream Cycle
                    </button>
                </div>
            )}

            {/* Insights Feed */}
            <div className="insights-section">
                <h3>💡 Extracted Insights</h3>
                <InsightFeed insights={insights} />
            </div>

            {/* Performance Chart */}
            <div className="performance-section">
                <h3>📈 Performance Evolution</h3>
                <PerformanceChart history={performanceHistory} />
            </div>
        </div>
    );
}

// ============================================================================
// Dream Cycle Card
// ============================================================================

function DreamCycleCard({ cycle }: { cycle: DreamCycle }) {
    const getPhaseColor = (phase: string | null): string => {
        switch (phase) {
            case 'rem': return '#64b5f6';
            case 'nrem': return '#ab47bc';
            case 'integration': return '#66bb6a';
            default: return '#9e9e9e';
        }
    };

    const getPhaseLabel = (phase: string | null): string => {
        switch (phase) {
            case 'rem': return 'REM - Experience Replay';
            case 'nrem': return 'NREM - Pattern Consolidation';
            case 'integration': return 'Integration - Applying Insights';
            default: return 'Initializing...';
        }
    };

    return (
        <div className="dream-cycle-card">
            {/* Phase Indicator */}
            <div className="phase-indicator">
                <div className="phase-timeline">
                    <PhaseStep
                        name="REM"
                        active={cycle.phase === 'rem'}
                        completed={cycle.progress > 0.33}
                    />
                    <PhaseStep
                        name="NREM"
                        active={cycle.phase === 'nrem'}
                        completed={cycle.progress > 0.66}
                    />
                    <PhaseStep
                        name="Integration"
                        active={cycle.phase === 'integration'}
                        completed={cycle.progress >= 1.0}
                    />
                </div>

                <div
                    className="current-phase"
                    style={{ color: getPhaseColor(cycle.phase) }}
                >
                    {getPhaseLabel(cycle.phase)}
                </div>
            </div>

            {/* Progress Bar */}
            <div className="progress-container">
                <div
                    className="progress-bar"
                    style={{
                        width: `${cycle.progress * 100}%`,
                        background: getPhaseColor(cycle.phase)
                    }}
                />
                <span className="progress-label">
                    {(cycle.progress * 100).toFixed(0)}%
                </span>
            </div>

            {/* Stats */}
            <div className="dream-stats">
                <div className="stat">
                    <div className="stat-label">Insights Extracted</div>
                    <div className="stat-value">{cycle.insights_count}</div>
                </div>
                <div className="stat">
                    <div className="stat-label">Duration</div>
                    <div className="stat-value">{cycle.duration_seconds.toFixed(1)}s</div>
                </div>
                <div className="stat">
                    <div className="stat-label">Status</div>
                    <div className={`stat-value status-${cycle.status}`}>
                        {cycle.status.toUpperCase()}
                    </div>
                </div>
            </div>
        </div>
    );
}

// ============================================================================
// Phase Step Component
// ============================================================================

function PhaseStep({
    name,
    active,
    completed
}: {
    name: string;
    active: boolean;
    completed: boolean;
}) {
    return (
        <div className={`phase-step ${active ? 'active' : ''} ${completed ? 'completed' : ''}`}>
            <div className="phase-dot" />
            <div className="phase-name">{name}</div>
        </div>
    );
}

// ============================================================================
// Insight Feed Component
// ============================================================================

function InsightFeed({ insights }: { insights: Insight[] }) {
    const getInsightIcon = (type: string): string => {
        switch (type) {
            case 'strategy_improvement': return '🎯';
            case 'pattern_recognition': return '🔍';
            case 'knowledge_gap': return '❓';
            case 'heuristic_update': return '⚙️';
            case 'risk_assessment': return '⚠️';
            default: return '💡';
        }
    };

    const getInsightColor = (type: string): string => {
        switch (type) {
            case 'strategy_improvement': return '#66bb6a';
            case 'pattern_recognition': return '#64b5f6';
            case 'knowledge_gap': return '#ffa726';
            case 'heuristic_update': return '#ab47bc';
            case 'risk_assessment': return '#ef5350';
            default: return '#9e9e9e';
        }
    };

    if (insights.length === 0) {
        return (
            <div className="no-insights">
                <p>No insights yet. Initiate a dream cycle to extract insights.</p>
            </div>
        );
    }

    return (
        <div className="insight-feed">
            {insights.map((insight) => (
                <div key={insight.id} className="insight-card">
                    <div className="insight-header">
                        <span className="insight-icon">{getInsightIcon(insight.type)}</span>
                        <span
                            className="insight-type"
                            style={{ color: getInsightColor(insight.type) }}
                        >
                            {insight.type.replace('_', ' ').toUpperCase()}
                        </span>
                        <span className="insight-confidence">
                            {(insight.confidence * 100).toFixed(0)}% confident
                        </span>
                    </div>

                    <div className="insight-content">
                        {insight.content}
                    </div>

                    <div className="insight-footer">
                        <div className="insight-impact">
                            Impact: <strong>{insight.impact_score > 0 ? '+' : ''}{(insight.impact_score * 100).toFixed(1)}%</strong>
                        </div>
                        <div className="insight-timestamp">
                            {new Date(insight.timestamp).toLocaleTimeString()}
                        </div>
                        {!insight.applied && (
                            <button className="apply-btn">
                                Apply Insight
                            </button>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}

// ============================================================================
// Performance Chart Component
// ============================================================================

function PerformanceChart({ history }: { history: number[] }) {
    const data = {
        labels: history.map((_, i) => `Dream ${i + 1}`),
        datasets: [
            {
                label: 'Performance',
                data: history,
                borderColor: '#66bb6a',
                backgroundColor: 'rgba(102, 187, 106, 0.1)',
                tension: 0.4,
            },
        ],
    };

    const options = {
        responsive: true,
        plugins: {
            legend: {
                display: false,
            },
        },
        scales: {
            y: {
                beginAtZero: true,
                max: 1.0,
            },
        },
    };

    if (history.length === 0) {
        return (
            <div className="no-data">
                <p>No performance data yet.</p>
            </div>
        );
    }

    return <Line data={data} options={options} />;
}

// ============================================================================
// Helper Functions
// ============================================================================

async function initiateDream(
    agentId: string,
    setActiveCycle: (cycle: DreamCycle | null) => void
) {
    try {
        const response = await fetch(
            apiPath(`/v1/oneiroi/dream/initiate/${agentId}`),
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    agent_id: agentId,
                    experience_count: 100
                })
            }
        );

        const data = await response.json();

        // Start polling for status
        const cycleId = data.cycle_id;
        const pollStatus = async () => {
            const statusRes = await fetch(
                apiPath(`/v1/oneiroi/dream/${cycleId}`)
            );
            const cycleData = await statusRes.json();
            setActiveCycle(cycleData);

            if (cycleData.status === 'running') {
                setTimeout(pollStatus, 1000);
            } else {
                setActiveCycle(null);
            }
        };

        pollStatus();

    } catch (error) {
        console.error('Failed to initiate dream:', error);
        alert('Failed to initiate dream cycle');
    }
}
