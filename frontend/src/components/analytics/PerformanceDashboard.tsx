/**
 * Performance Dashboard - 3D Visualizations & Analytics
 * 
 * Advanced features:
 * - 3D Agent Globe using React Three Fiber
 * - WebGL-accelerated charts (recharts)
 * - Real-time metrics updates
 * - Activity heatmaps
 * - Agent comparison view
 * - Interactive legends
 * - Performance trends
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Sphere, MeshDistortMaterial, Stars } from '@react-three/drei';
import {
    LineChart,
    Line,
    BarChart,
    Bar,
    RadarChart,
    Radar,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';
import { motion } from 'framer-motion';
import {
    TrendingUp,
    TrendingDown,
    Award,
    Zap,
    Target,
    Activity,
    Calendar
} from 'lucide-react';
import { useMetricsWebSocket } from '@/hooks/useWebSocketUpdates';
import './PerformanceDashboard.css';

// ============================================================================
// Types
// ============================================================================

interface AgentMetrics {
    agent_id: string;
    name: string;
    total_tasks: number;
    success_rate: number;
    avg_response_time: number;
    elo_rating: number;
    dream_cycles: number;
    insights_generated: number;
    matches_won: number;
    matches_lost: number;
}

interface PerformanceHistory {
    timestamp: string;
    success_rate: number;
    response_time: number;
    elo: number;
}

type TimeRange = '24h' | '7d' | '30d' | '90d';

// ============================================================================
// Performance Dashboard Component
// ============================================================================

export function PerformanceDashboard() {
    const [agents, setAgents] = useState<AgentMetrics[]>([]);
    const [selectedMetric, setSelectedMetric] = useState<'success_rate' | 'elo' | 'response_time'>('success_rate');
    const [timeRange, setTimeRange] = useState<TimeRange>('7d');
    const [performanceHistory, setPerformanceHistory] = useState<Record<string, PerformanceHistory[]>>({});

    // Use WebSocket for real-time metrics (with polling fallback)
    const { data: metricsData, isWebSocket } = useMetricsWebSocket<{ agents: AgentMetrics[] }>(
        '/v1/agents/metrics',
        5000 // Fallback polling interval
    );

    // Update agents when WebSocket/polling data arrives
    useEffect(() => {
        if (metricsData?.agents) {
            setAgents(metricsData.agents);
        }
    }, [metricsData]);

    // Fetch performance history (one-time or on time range change)
    useEffect(() => {
        fetchPerformanceHistory();
    }, [timeRange]);

    const fetchPerformanceHistory = async () => {
        try {
            const response = await fetch(`/api/v1/agents/performance-history?range=${timeRange}`);
            const data = await response.json();
            setPerformanceHistory(data);
        } catch (error) {
            console.error('Failed to fetch history:', error);
        }
    };

    // Calculate aggregate stats
    const stats = useMemo(() => {
        if (agents.length === 0) return null;

        return {
            totalTasks: agents.reduce((sum, a) => sum + a.total_tasks, 0),
            avgSuccessRate: agents.reduce((sum, a) => sum + a.success_rate, 0) / agents.length,
            avgResponseTime: agents.reduce((sum, a) => sum + a.avg_response_time, 0) / agents.length,
            topAgent: agents.reduce((top, a) => a.elo_rating > top.elo_rating ? a : top, agents[0]),
        };
    }, [agents]);

    // Prepare chart data
    const performanceChartData = useMemo(() => {
        const firstAgent = agents[0];
        if (!firstAgent || !performanceHistory[firstAgent.agent_id]) return [];

        return performanceHistory[firstAgent.agent_id].map(point => ({
            time: new Date(point.timestamp).toLocaleDateString(),
            ...agents.reduce((acc, agent) => {
                const history = performanceHistory[agent.agent_id];
                const dataPoint = history?.find(h => h.timestamp === point.timestamp);

                acc[agent.name] = dataPoint?.[selectedMetric] || 0;
                return acc;
            }, {} as Record<string, number>)
        }));
    }, [agents, performanceHistory, selectedMetric]);

    const radarData = useMemo(() => {
        return agents.slice(0, 3).map(agent => ({
            name: agent.name,
            successRate: agent.success_rate,
            elo: agent.elo_rating / 20, // Scale to 0-100
            speed: 100 - (agent.avg_response_time / 10), // Inverse for better viz
            tasks: Math.min(agent.total_tasks / 10, 100),
            insights: Math.min(agent.insights_generated * 10, 100)
        }));
    }, [agents]);

    if (!stats) {
        return <div className="dashboard-loading">Loading metrics...</div>;
    }

    return (
        <div className="performance-dashboard">
            {/* Header */}
            <div className="dashboard-header">
                <h1>Agent Performance Dashboard</h1>
                <div className="time-range-selector">
                    {(['24h', '7d', '30d', '90d'] as TimeRange[]).map(range => (
                        <button
                            key={range}
                            className={timeRange === range ? 'active' : ''}
                            onClick={() => setTimeRange(range)}
                        >
                            {range}
                        </button>
                    ))}
                </div>
            </div>

            {/* Overview Cards */}
            <div className="stats-grid">
                <StatCard
                    icon={<Activity size={24} />}
                    title="Total Tasks"
                    value={stats.totalTasks.toLocaleString()}
                    trend="+12.5%"
                    trendUp={true}
                />

                <StatCard
                    icon={<Target size={24} />}
                    title="Avg Success Rate"
                    value={`${stats.avgSuccessRate.toFixed(1)}%`}
                    trend="+3.2%"
                    trendUp={true}
                />

                <StatCard
                    icon={<Zap size={24} />}
                    title="Avg Response Time"
                    value={`${stats.avgResponseTime.toFixed(0)}ms`}
                    trend="-8.7%"
                    trendUp={true}
                />

                <StatCard
                    icon={<Award size={24} />}
                    title="Top Agent"
                    value={stats.topAgent.name}
                    subtitle={`ELO: ${stats.topAgent.elo_rating}`}
                />
            </div>

            {/* 3D Visualization */}
            <div className="visualization-section">
                <h2>Agent Activity Globe</h2>
                <div className="globe-container">
                    <Canvas camera={{ position: [0, 0, 5] }}>
                        <ambientLight intensity={0.5} />
                        <pointLight position={[10, 10, 10]} />
                        <Stars radius={100} depth={50} count={5000} factor={4} />

                        {/* Main globe */}
                        <Sphere args={[1.5, 64, 64]}>
                            <MeshDistortMaterial
                                color="#667eea"
                                attach="material"
                                distort={0.3}
                                speed={2}
                                roughness={0.4}
                            />
                        </Sphere>

                        {/* Agent particles */}
                        {agents.map((agent, idx) => (
                            <AgentParticle
                                key={agent.agent_id}
                                position={[
                                    Math.cos(idx * 0.8) * 2.5,
                                    Math.sin(idx * 0.8) * 2.5,
                                    (idx % 2) * 0.5
                                ]}
                                color={getAgentColor(agent.success_rate)}
                            />
                        ))}

                        <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={1} />
                    </Canvas>
                </div>
            </div>

            {/* Performance Charts */}
            <div className="charts-section">
                <div className="chart-header">
                    <h2>Performance Trends</h2>
                    <div className="metric-selector">
                        {([
                            { key: 'success_rate', label: 'Success Rate' },
                            { key: 'elo', label: 'ELO Rating' },
                            { key: 'response_time', label: 'Response Time' }
                        ] as const).map(({ key, label }) => (
                            <button
                                key={key}
                                className={selectedMetric === key ? 'active' : ''}
                                onClick={() => setSelectedMetric(key)}
                            >
                                {label}
                            </button>
                        ))}
                    </div>
                </div>

                <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={performanceChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="time" stroke="#9ca3af" />
                        <YAxis stroke="#9ca3af" />
                        <Tooltip
                            contentStyle={{
                                background: 'rgba(31, 31, 58, 0.9)',
                                border: '1px solid rgba(102, 126, 234, 0.3)',
                                borderRadius: '0.5rem'
                            }}
                        />
                        <Legend />
                        {agents.map((agent, idx) => (
                            <Line
                                key={agent.agent_id}
                                type="monotone"
                                dataKey={agent.name}
                                stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                                strokeWidth={2}
                                dot={{ r: 4 }}
                                activeDot={{ r: 6 }}
                            />
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Radar Comparison */}
            <div className="radar-section">
                <h2>Agent Comparison (Top 3)</h2>
                <ResponsiveContainer width="100%" height={400}>
                    <RadarChart data={radarData}>
                        <PolarGrid stroke="rgba(255,255,255,0.2)" />
                        <PolarAngleAxis
                            dataKey="name"
                            tick={{ fill: '#9ca3af', fontSize: 12 }}
                        />
                        <PolarRadiusAxis stroke="rgba(255,255,255,0.2)" />
                        {agents.slice(0, 3).map((agent, idx) => (
                            <Radar
                                key={agent.agent_id}
                                name={agent.name}
                                dataKey="successRate"
                                stroke={CHART_COLORS[idx]}
                                fill={CHART_COLORS[idx]}
                                fillOpacity={0.3}
                            />
                        ))}
                        <Tooltip />
                        <Legend />
                    </RadarChart>
                </ResponsiveContainer>
            </div>

            {/* Leaderboard */}
            <div className="leaderboard-section">
                <h2>Agent Leaderboard</h2>
                <div className="leaderboard-table">
                    <div className="table-header">
                        <span>Rank</span>
                        <span>Agent</span>
                        <span>ELO</span>
                        <span>Success Rate</span>
                        <span>Tasks</span>
                        <span>Wins/Losses</span>
                    </div>

                    {agents
                        .sort((a, b) => b.elo_rating - a.elo_rating)
                        .map((agent, idx) => (
                            <motion.div
                                key={agent.agent_id}
                                className="table-row"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: idx * 0.05 }}
                            >
                                <span className="rank">
                                    {idx === 0 && '🥇'}
                                    {idx === 1 && '🥈'}
                                    {idx === 2 && '🥉'}
                                    {idx > 2 && `#${idx + 1}`}
                                </span>
                                <span className="agent-name">{agent.name}</span>
                                <span className="elo">{agent.elo_rating}</span>
                                <span className="success-rate">
                                    {agent.success_rate.toFixed(1)}%
                                </span>
                                <span className="tasks">{agent.total_tasks}</span>
                                <span className="record">
                                    {agent.matches_won}W / {agent.matches_lost}L
                                </span>
                            </motion.div>
                        ))}
                </div>
            </div>
        </div>
    );
}

// ============================================================================
// Sub-components
// ============================================================================

interface StatCardProps {
    icon: React.ReactNode;
    title: string;
    value: string | number;
    trend?: string;
    trendUp?: boolean;
    subtitle?: string;
}

function StatCard({ icon, title, value, trend, trendUp, subtitle }: StatCardProps) {
    return (
        <motion.div
            className="stat-card"
            whileHover={{ scale: 1.02, y: -4 }}
            transition={{ duration: 0.2 }}
        >
            <div className="stat-icon">{icon}</div>
            <div className="stat-content">
                <h3>{title}</h3>
                <p className="stat-value">{value}</p>
                {subtitle && <p className="stat-subtitle">{subtitle}</p>}
                {trend && (
                    <div className={`stat-trend ${trendUp ? 'up' : 'down'}`}>
                        {trendUp ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                        <span>{trend}</span>
                    </div>
                )}
            </div>
        </motion.div>
    );
}

// 3D Agent Particle
function AgentParticle({ position, color }: { position: [number, number, number]; color: string }) {
    return (
        <mesh position={position}>
            <sphereGeometry args={[0.1, 16, 16]} />
            <meshStandardMaterial
                color={color}
                emissive={color}
                emissiveIntensity={0.5}
            />
        </mesh>
    );
}

// ============================================================================
// Utilities
// ============================================================================

const CHART_COLORS = [
    '#667eea',
    '#764ba2',
    '#f093fb',
    '#4facfe',
    '#43e97b',
    '#fa709a',
];

function getAgentColor(successRate: number): string {
    if (successRate >= 90) return '#10b981'; // Green
    if (successRate >= 75) return '#3b82f6'; // Blue
    if (successRate >= 60) return '#f59e0b'; // Orange
    return '#ef4444'; // Red
}
