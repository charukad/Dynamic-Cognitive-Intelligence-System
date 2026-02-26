'use client';

/**
 * Unified Analytics Dashboard
 * 
 * Comprehensive system-wide analytics combining:
 * - RLHF feedback metrics
 * - Agent performance stats
 * - Memory system analytics
 * - Evolution progress
 * - Operations monitoring
 */

'use client';

import React, { useCallback, useEffect, useState } from 'react';
import {
    AreaChart, Area, LineChart, Line,
    PieChart, Pie, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
    TrendingUp, Award, Brain, Dna, Activity, Zap,
    Database, ThumbsUp, Clock, Target, Cpu
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';

// ============================================================================
// Types
// ============================================================================

interface SystemMetrics {
    rlhf: {
        total_feedback: number;
        approval_rate: number;
        avg_rating: number;
        trend: string;
    };
    performance: {
        avg_latency_ms: number;
        total_requests: number;
        success_rate: number;
        latency_trend?: number;
        requests_trend?: number;
    };
    memory: {
        total_memories: number;
        semantic_count: number;
        episodic_count: number;
        avg_importance: number;
        memory_trend?: number;
    };
    evolution: {
        current_generation: number;
        best_fitness: number;
        avg_fitness: number;
        improvement_rate: number;
        evolution_trend?: string;
    };
    operations: {
        cache_hit_rate: number;
        circuit_breaker_state: string;
        active_traces: number;
    };
}

interface TimeSeriesPoint {
    time: string;
    feedback: number;
    memories: number;
    generation: number;
    latency: number;
}

interface MemoryDistributionDatum {
    name: string;
    value: number;
    color: string;
}

// ============================================================================
// Main Component
// ============================================================================

export function UnifiedAnalyticsDashboard() {
    const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
    const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesPoint[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedView, setSelectedView] = useState<'overview' | 'detailed'>('overview');

    const fetchMetrics = useCallback(async () => {
        try {
            // Use unified analytics endpoint for efficiency
            const unifiedRes = await apiClient.get('/v1/analytics/unified-dashboard');

            const unified = unifiedRes.data || unifiedRes;

            const metrics: SystemMetrics = {
                rlhf: {
                    total_feedback: unified.rlhf?.total_feedback || 0,
                    approval_rate: unified.rlhf?.approval_rate || 0,
                    avg_rating: unified.rlhf?.avg_rating || 0,
                    trend: unified.rlhf?.trend || 'stable',
                },
                performance: {
                    avg_latency_ms: unified.performance?.avg_latency_ms || 0,
                    total_requests: unified.performance?.total_requests || 0,
                    success_rate: unified.performance?.success_rate || 0.95,
                    latency_trend: unified.performance?.latency_trend,
                    requests_trend: unified.performance?.requests_trend,
                },
                memory: {
                    total_memories: unified.memory?.total_memories || 0,
                    semantic_count: unified.memory?.semantic_count || 0,
                    episodic_count: unified.memory?.episodic_count || 0,
                    avg_importance: unified.memory?.avg_importance || 0,
                    memory_trend: unified.memory?.memory_trend,
                },
                evolution: {
                    current_generation: unified.evolution?.current_generation || 0,
                    best_fitness: unified.evolution?.best_fitness || 0,
                    avg_fitness: unified.evolution?.avg_population_fitness || 0,
                    improvement_rate: 0,
                    evolution_trend: unified.evolution?.evolution_trend,
                },
                operations: {
                    cache_hit_rate: unified.cache?.hit_rate || 0,
                    circuit_breaker_state: (() => {
                        const breakers = unified.circuit_breakers || {};
                        const firstBreaker = Object.values(breakers)[0] as
                            | { state?: string }
                            | undefined;
                        return firstBreaker?.state || 'closed';
                    })(),
                    active_traces: 0,
                },
            };

            setMetrics(metrics);

            // Add to time series
            setTimeSeriesData(prev => [
                ...prev.slice(-19),
                {
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    feedback: metrics.rlhf.total_feedback,
                    memories: metrics.memory.total_memories,
                    generation: metrics.evolution.current_generation,
                    latency: metrics.performance.avg_latency_ms,
                }
            ]);

            setIsLoading(false);
        } catch (error) {
            console.error('Failed to fetch unified metrics:', error);
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        const initialFetchTimer = setTimeout(() => {
            void fetchMetrics();
        }, 0);
        const interval = setInterval(() => {
            void fetchMetrics();
        }, 5000);

        return () => {
            clearTimeout(initialFetchTimer);
            clearInterval(interval);
        };
    }, [fetchMetrics]);

    if (isLoading || !metrics) {
        return (
            <div className="h-full flex items-center justify-center">
                <div className="text-gray-400">Loading analytics...</div>
            </div>
        );
    }

    // Prepare system health radar data
    const radarData = [
        { metric: 'Feedback', value: Math.min(metrics.rlhf.approval_rate * 100, 100), fullMark: 100 },
        { metric: 'Performance', value: Math.min(metrics.performance.success_rate * 100, 100), fullMark: 100 },
        { metric: 'Memory', value: Math.min((metrics.memory.avg_importance / 10) * 100, 100), fullMark: 100 },
        { metric: 'Evolution', value: Math.min(metrics.evolution.best_fitness * 100, 100), fullMark: 100 },
        { metric: 'Operations', value: Math.min(metrics.operations.cache_hit_rate * 100, 100), fullMark: 100 },
    ];

    // Memory distribution
    const memoryDistribution = [
        { name: 'Semantic', value: metrics.memory.semantic_count, color: '#3b82f6' },
        { name: 'Episodic', value: metrics.memory.episodic_count, color: '#8b5cf6' },
    ];

    return (
        <div className="h-full w-full bg-black/50 rounded-lg overflow-hidden flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-800 bg-black/30 backdrop-blur-sm">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <Target className="h-5 w-5 text-cyan-400" />
                        System Analytics
                    </h2>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setSelectedView('overview')}
                            className={`px-3 py-1 rounded text-sm ${selectedView === 'overview'
                                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                                : 'bg-gray-800 text-gray-400'
                                }`}
                        >
                            Overview
                        </button>
                        <button
                            onClick={() => setSelectedView('detailed')}
                            className={`px-3 py-1 rounded text-sm ${selectedView === 'detailed'
                                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                                : 'bg-gray-800 text-gray-400'
                                }`}
                        >
                            Detailed
                        </button>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {selectedView === 'overview' ? (
                    <OverviewView
                        metrics={metrics}
                        radarData={radarData}
                        memoryDistribution={memoryDistribution}
                        timeSeriesData={timeSeriesData}
                    />
                ) : (
                    <DetailedView
                        metrics={metrics}
                        timeSeriesData={timeSeriesData}
                    />
                )}
            </div>
        </div>
    );
}

// ============================================================================
// Overview View
// ============================================================================

interface OverviewViewProps {
    metrics: SystemMetrics;
    radarData: Array<{ metric: string; value: number; fullMark: number }>;
    memoryDistribution: MemoryDistributionDatum[];
    timeSeriesData: TimeSeriesPoint[];
}

function OverviewView({
    metrics,
    radarData,
    memoryDistribution,
    timeSeriesData,
}: OverviewViewProps) {
    return (
        <>
            {/* Key Performance Indicators */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-6">
                <KPICard
                    label="Feedback Score"
                    value={`${(metrics.rlhf.approval_rate * 100).toFixed(0)}%`}
                    icon={<ThumbsUp className="h-4 w-4 text-green-400" />}
                    trend={metrics.rlhf.trend || 'N/A'}
                    color="text-green-400"
                />
                <KPICard
                    label="Avg Latency"
                    value={`${metrics.performance.avg_latency_ms.toFixed(0)}ms`}
                    icon={<Clock className="h-4 w-4 text-blue-400" />}
                    trend={metrics.performance.latency_trend !== undefined ? `${metrics.performance.latency_trend > 0 ? '+' : ''}${metrics.performance.latency_trend.toFixed(1)}%` : 'N/A'}
                    color="text-blue-400"
                />
                <KPICard
                    label="Total Memories"
                    value={metrics.memory.total_memories.toString()}
                    icon={<Database className="h-4 w-4 text-purple-400" />}
                    trend={metrics.memory.memory_trend !== undefined ? `${metrics.memory.memory_trend > 0 ? '+' : ''}${metrics.memory.memory_trend.toFixed(1)}%` : 'N/A'}
                    color="text-purple-400"
                />
                <KPICard
                    label="Generation"
                    value={`#${metrics.evolution.current_generation}`}
                    icon={<Dna className="h-4 w-4 text-pink-400" />}
                    trend={metrics.evolution.evolution_trend || 'N/A'}
                    color="text-pink-400"
                />
                <KPICard
                    label="Cache Hit"
                    value={`${(metrics.operations.cache_hit_rate * 100).toFixed(0)}%`}
                    icon={<Zap className="h-4 w-4 text-yellow-400" />}
                    trend="N/A"
                    color="text-yellow-400"
                />
                <KPICard
                    label="Requests"
                    value={metrics.performance.total_requests.toString()}
                    icon={<Activity className="h-4 w-4 text-cyan-400" />}
                    trend={metrics.performance.requests_trend !== undefined ? `${metrics.performance.requests_trend > 0 ? '+' : ''}${metrics.performance.requests_trend.toFixed(1)}%` : 'N/A'}
                    color="text-cyan-400"
                />
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                {/* System Health Radar */}
                <div className="bg-gray-900/50 rounded-lg p-4">
                    <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                        <Target className="h-4 w-4 text-cyan-400" />
                        System Health
                    </h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <RadarChart data={radarData}>
                            <PolarGrid stroke="#333" />
                            <PolarAngleAxis dataKey="metric" tick={{ fill: '#888', fontSize: 12 }} />
                            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#888' }} />
                            <Radar
                                name="Health Score"
                                dataKey="value"
                                stroke="#00F0FF"
                                fill="#00F0FF"
                                fillOpacity={0.3}
                            />
                            <Tooltip contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }} />
                        </RadarChart>
                    </ResponsiveContainer>
                </div>

                {/* Memory Distribution */}
                <div className="bg-gray-900/50 rounded-lg p-4">
                    <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                        <Brain className="h-4 w-4 text-purple-400" />
                        Memory Distribution
                    </h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                            <Pie
                                data={memoryDistribution}
                                dataKey="value"
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                            >
                                {memoryDistribution.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Multi-Metric Time Series */}
            <div className="bg-gray-900/50 rounded-lg p-4">
                <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-green-400" />
                    System Growth Over Time
                </h3>
                {timeSeriesData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                        <AreaChart data={timeSeriesData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                            <XAxis dataKey="time" stroke="#666" />
                            <YAxis stroke="#666" />
                            <Tooltip contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }} />
                            <Legend />
                            <Area
                                type="monotone"
                                dataKey="memories"
                                stackId="1"
                                stroke="#8b5cf6"
                                fill="#8b5cf6"
                                fillOpacity={0.6}
                                name="Memories"
                            />
                            <Area
                                type="monotone"
                                dataKey="feedback"
                                stackId="2"
                                stroke="#10b981"
                                fill="#10b981"
                                fillOpacity={0.6}
                                name="Feedback"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-[250px] flex items-center justify-center text-gray-500">
                        Collecting data...
                    </div>
                )}
            </div>
        </>
    );
}

// ============================================================================
// Detailed View
// ============================================================================

interface DetailedViewProps {
    metrics: SystemMetrics;
    timeSeriesData: TimeSeriesPoint[];
}

function DetailedView({ metrics, timeSeriesData }: DetailedViewProps) {
    return (
        <>
            {/* RLHF Metrics */}
            <div className="bg-gray-900/50 rounded-lg p-4">
                <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                    <Award className="h-4 w-4 text-yellow-400" />
                    RLHF Metrics
                </h3>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    <MetricDetail label="Total Feedback" value={metrics.rlhf.total_feedback} />
                    <MetricDetail label="Approval Rate" value={`${(metrics.rlhf.approval_rate * 100).toFixed(1)}%`} />
                    <MetricDetail label="Avg Rating" value={metrics.rlhf.avg_rating.toFixed(2)} />
                </div>
            </div>

            {/* Evolution Metrics */}
            <div className="bg-gray-900/50 rounded-lg p-4">
                <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                    <Dna className="h-4 w-4 text-pink-400" />
                    Evolution Progress
                </h3>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    <MetricDetail label="Generation" value={`#${metrics.evolution.current_generation}`} />
                    <MetricDetail label="Best Fitness" value={metrics.evolution.best_fitness.toFixed(3)} />
                    <MetricDetail label="Avg Fitness" value={metrics.evolution.avg_fitness.toFixed(3)} />
                </div>
                <div className="mt-4">
                    <ResponsiveContainer width="100%" height={150}>
                        <LineChart data={timeSeriesData.slice(-10)}>
                            <XAxis dataKey="time" stroke="#666" />
                            <YAxis stroke="#666" />
                            <Tooltip contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }} />
                            <Line type="monotone" dataKey="generation" stroke="#ec4899" strokeWidth={2} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Performance & Operations */}
            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                <div className="bg-gray-900/50 rounded-lg p-4">
                    <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                        <Cpu className="h-4 w-4 text-blue-400" />
                        Performance
                    </h3>
                    <div className="space-y-3">
                        <MetricDetail label="Avg Latency" value={`${metrics.performance.avg_latency_ms.toFixed(1)}ms`} />
                        <MetricDetail label="Success Rate" value={`${(metrics.performance.success_rate * 100).toFixed(1)}%`} />
                        <MetricDetail label="Total Requests" value={metrics.performance.total_requests} />
                    </div>
                </div>

                <div className="bg-gray-900/50 rounded-lg p-4">
                    <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                        <Activity className="h-4 w-4 text-cyan-400" />
                        Operations
                    </h3>
                    <div className="space-y-3">
                        <MetricDetail label="Cache Hit Rate" value={`${(metrics.operations.cache_hit_rate * 100).toFixed(1)}%`} />
                        <MetricDetail label="Circuit Breaker" value={metrics.operations.circuit_breaker_state.toUpperCase()} />
                        <MetricDetail label="Active Traces" value={metrics.operations.active_traces} />
                    </div>
                </div>
            </div>
        </>
    );
}

// ============================================================================
// Helper Components
// ============================================================================

interface KPICardProps {
    label: string;
    value: string;
    icon: React.ReactNode;
    trend: string;
    color: string;
}

function KPICard({ label, value, icon, trend, color }: KPICardProps) {
    return (
        <div className="bg-gray-900/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
                {icon}
                <span className="text-xs text-gray-400">{label}</span>
            </div>
            <div className={`text-xl font-bold ${color}`}>{value}</div>
            <div className="text-xs text-gray-500 mt-1">{trend}</div>
        </div>
    );
}

function MetricDetail({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="flex justify-between items-center">
            <span className="text-sm text-gray-400">{label}:</span>
            <span className="text-white font-semibold">{value}</span>
        </div>
    );
}
