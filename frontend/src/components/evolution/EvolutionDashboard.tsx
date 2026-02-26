'use client';

/**
 * Evolution Dashboard - GAIA Genetic Algorithm Visualization
 * 
 * Advanced visualization of agent evolution:
 * - Fitness progression charts
 * - Population diversity metrics
 * - Genome comparison
 * - Generation timeline
 * - Meta-learning strategy browser
 */

'use client';

import React, { useCallback, useEffect, useState } from 'react';
import {
    Dna,
    TrendingUp,
    Users,
    Award,
    BarChart3,
    Lightbulb,
    RefreshCw
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { Button } from '@/components/ui/button';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';

// ============================================================================
// Types
// ============================================================================

interface EvolutionStats {
    current_generation: number;
    population_size: number;
    avg_fitness: number;
    best_fitness: number;
    best_genome: {
        agent_id: string;
        system_prompt: string;
        temperature: number;
        capabilities: string[];
        fitness_score: number;
        generation: number;
    } | null;
}

interface MetaLearningStats {
    total_strategies: number;
    domains: string[];
    avg_success_rate: number;
    most_used: unknown;
}

const INITIAL_FITNESS_HISTORY = [
    { generation: 0, avg: 0.45, best: 0.62 },
    { generation: 1, avg: 0.52, best: 0.71 },
    { generation: 2, avg: 0.58, best: 0.75 },
    { generation: 3, avg: 0.63, best: 0.79 },
    { generation: 4, avg: 0.67, best: 0.83 },
];

// ============================================================================
// Main Component
// ============================================================================

export function EvolutionDashboard() {
    const [stats, setStats] = useState<EvolutionStats | null>(null);
    const [metaStats, setMetaStats] = useState<MetaLearningStats | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isEvolving, setIsEvolving] = useState(false);
    const fitnessHistory = INITIAL_FITNESS_HISTORY;

    // Fetch data
    const fetchData = useCallback(async () => {
        setIsLoading(true);
        try {
            const [statsRes, metaStatsRes] = await Promise.all([
                apiClient.get('/v1/gaia/evolution/stats'),
                apiClient.get('/v1/gaia/evolution/meta-learn/stats'),
            ]);

            setStats(statsRes.data || statsRes);
            setMetaStats(metaStatsRes.data || metaStatsRes);
        } catch (error) {
            console.error('Failed to fetch evolution data:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        const initialFetchTimer = setTimeout(() => {
            void fetchData();
        }, 0);
        const interval = setInterval(() => {
            void fetchData();
        }, 5000);

        return () => {
            clearTimeout(initialFetchTimer);
            clearInterval(interval);
        };
    }, [fetchData]);

    const handleEvolve = async () => {
        setIsEvolving(true);
        try {
            // Mock evolution request
            const mockMetrics = Array.from({ length: 20 }, (_, i) => ({
                agent_id: `00000000-0000-0000-0000-${String(i).padStart(12, '0')}`,
                success_rate: Math.random(),
                avg_response_time: Math.random() * 2000,
                user_satisfaction: Math.random(),
                task_completion: Math.random(),
                elo_rating: 1000 + Math.random() * 500,
            }));

            await apiClient.post('/v1/gaia/evolution/evolve', mockMetrics);
            await fetchData();
        } catch (error) {
            console.error('Evolution failed:', error);
        } finally {
            setIsEvolving(false);
        }
    };

    if (isLoading && !stats) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-400">Loading evolution data...</div>
            </div>
        );
    }

    return (
        <div className="h-full w-full overflow-hidden rounded-2xl border border-emerald-500/20 bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.14),_transparent_42%),linear-gradient(180deg,rgba(7,20,19,0.96),rgba(10,22,38,0.8))] shadow-[0_22px_64px_rgba(0,0,0,0.45)] flex flex-col">
            {/* Header */}
            <div className="border-b border-emerald-500/15 bg-black/25 p-4 backdrop-blur-md md:p-5">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <h2 className="flex items-center gap-2 text-lg font-semibold tracking-tight text-white sm:text-xl">
                        <Dna className="h-5 w-5 text-green-400" />
                        GAIA Evolution Engine
                    </h2>
                    <Button
                        onClick={handleEvolve}
                        disabled={isEvolving}
                        className="flex items-center gap-2 bg-gradient-to-r from-emerald-600 via-cyan-600 to-blue-600 hover:from-emerald-500 hover:via-cyan-500 hover:to-blue-500"
                    >
                        <RefreshCw className={`h-4 w-4 ${isEvolving ? 'animate-spin' : ''}`} />
                        {isEvolving ? 'Evolving...' : 'Evolve Generation'}
                    </Button>
                </div>

                {/* Stats Grid */}
                {stats && (
                    <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
                        <StatCard
                            icon={<BarChart3 className="h-5 w-5" />}
                            label="Generation"
                            value={stats.current_generation}
                            color="text-cyan-400"
                        />
                        <StatCard
                            icon={<Users className="h-5 w-5" />}
                            label="Population"
                            value={stats.population_size}
                            color="text-blue-400"
                        />
                        <StatCard
                            icon={<TrendingUp className="h-5 w-5" />}
                            label="Avg Fitness"
                            value={stats.avg_fitness.toFixed(3)}
                            color="text-green-400"
                        />
                        <StatCard
                            icon={<Award className="h-5 w-5" />}
                            label="Best Fitness"
                            value={stats.best_fitness.toFixed(3)}
                            color="text-yellow-400"
                        />
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="flex-1 space-y-5 overflow-y-auto p-4 md:p-5">
                {/* Fitness Chart */}
                <div className="rounded-xl border border-emerald-500/12 bg-slate-950/55 p-4 md:p-5">
                    <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-green-400" />
                        Fitness Evolution
                    </h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <LineChart data={fitnessHistory}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                            <XAxis dataKey="generation" stroke="#9ca3af" />
                            <YAxis stroke="#9ca3af" domain={[0, 1]} />
                            <Tooltip
                                contentStyle={{
                                    background: 'rgba(31, 31, 58, 0.9)',
                                    border: '1px solid rgba(102, 126, 234, 0.3)',
                                    borderRadius: '0.5rem',
                                }}
                            />
                            <Legend />
                            <Line
                                type="monotone"
                                dataKey="best"
                                stroke="#10b981"
                                strokeWidth={3}
                                name="Best Fitness"
                                dot={{ r: 4 }}
                            />
                            <Line
                                type="monotone"
                                dataKey="avg"
                                stroke="#3b82f6"
                                strokeWidth={2}
                                name="Avg Fitness"
                                dot={{ r: 3 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Best Genome */}
                {stats?.best_genome && (
                    <div className="rounded-xl border border-emerald-500/30 bg-slate-950/55 p-4 md:p-5">
                        <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                            <Award className="h-4 w-4 text-yellow-400" />
                            Champion Genome (Gen {stats.best_genome.generation})
                        </h3>
                        <div className="space-y-2 text-sm">
                            <div>
                                <span className="text-gray-400">Fitness:</span>
                                <span className="text-green-400 ml-2 font-bold">
                                    {stats.best_genome.fitness_score.toFixed(3)}
                                </span>
                            </div>
                            <div>
                                <span className="text-gray-400">Temperature:</span>
                                <span className="text-blue-400 ml-2">{stats.best_genome.temperature}</span>
                            </div>
                            <div>
                                <span className="text-gray-400">Capabilities:</span>
                                <div className="mt-1 flex flex-wrap gap-1">
                                    {stats.best_genome.capabilities.map((cap) => (
                                        <span key={cap} className="rounded-full border border-emerald-400/20 bg-emerald-950/30 px-2 py-0.5 text-xs text-emerald-200">
                                            {cap}
                                        </span>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <span className="text-gray-400">System Prompt:</span>
                                <p className="mt-1 rounded-lg border border-white/10 bg-black/30 p-2 text-xs text-white">
                                    {stats.best_genome.system_prompt.substring(0, 200)}...
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Meta-Learning Stats */}
                {metaStats && (
                    <div className="rounded-xl border border-emerald-500/12 bg-slate-950/55 p-4 md:p-5">
                        <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                            <Lightbulb className="h-4 w-4 text-yellow-400" />
                            Meta-Learning Intelligence
                        </h3>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                            <div>
                                <div className="text-xs text-gray-400">Total Strategies</div>
                                <div className="text-2xl font-bold text-cyan-400">{metaStats.total_strategies}</div>
                            </div>
                            <div>
                                <div className="text-xs text-gray-400">Avg Success</div>
                                <div className="text-2xl font-bold text-green-400">
                                    {(metaStats.avg_success_rate * 100).toFixed(1)}%
                                </div>
                            </div>
                            <div>
                                <div className="text-xs text-gray-400">Domains</div>
                                <div className="mt-1 text-sm text-white">
                                    {metaStats.domains.join(', ') || 'None'}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// ============================================================================
// Helper Components
// ============================================================================

function StatCard({
    icon,
    label,
    value,
    color
}: {
    icon: React.ReactNode;
    label: string;
    value: number | string;
    color: string;
}) {
    return (
        <div className="rounded-xl border border-white/8 bg-slate-950/55 px-3 py-2 transition-colors hover:border-emerald-400/25 hover:bg-slate-900/70">
            <div className="flex items-center gap-2 mb-1">
                <div className={color}>{icon}</div>
                <div className="text-xs uppercase tracking-wide text-gray-400">{label}</div>
            </div>
            <div className={`text-xl font-bold ${color}`}>{value}</div>
        </div>
    );
}
