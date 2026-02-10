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

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
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
    BarChart,
    Bar,
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

interface Strategy {
    id: string;
    task_pattern: string;
    strategy_description: string;
    avg_success_rate: number;
    usage_count: number;
}

interface MetaLearningStats {
    total_strategies: number;
    domains: string[];
    avg_success_rate: number;
    most_used: any;
}

// ============================================================================
// Main Component
// ============================================================================

export function EvolutionDashboard() {
    const [stats, setStats] = useState<EvolutionStats | null>(null);
    const [strategies, setStrategies] = useState<Strategy[]>([]);
    const [metaStats, setMetaStats] = useState<MetaLearningStats | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isEvolving, setIsEvolving] = useState(false);

    // Mock fitness history for demo
    const [fitnessHistory, setFitnessHistory] = useState([
        { generation: 0, avg: 0.45, best: 0.62 },
        { generation: 1, avg: 0.52, best: 0.71 },
        { generation: 2, avg: 0.58, best: 0.75 },
        { generation: 3, avg: 0.63, best: 0.79 },
        { generation: 4, avg: 0.67, best: 0.83 },
    ]);

    // Fetch data
    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
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
    };

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
        <div className="h-full w-full bg-black/50 rounded-lg overflow-hidden flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-800 bg-black/30 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <Dna className="h-5 w-5 text-green-400" />
                        GAIA Evolution Engine
                    </h2>
                    <Button
                        onClick={handleEvolve}
                        disabled={isEvolving}
                        className="flex items-center gap-2"
                    >
                        <RefreshCw className={`h-4 w-4 ${isEvolving ? 'animate-spin' : ''}`} />
                        {isEvolving ? 'Evolving...' : 'Evolve Generation'}
                    </Button>
                </div>

                {/* Stats Grid */}
                {stats && (
                    <div className="grid grid-cols-4 gap-3">
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
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {/* Fitness Chart */}
                <div className="bg-gray-900/50 rounded-lg p-4">
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
                    <div className="bg-gray-900/50 rounded-lg p-4 border border-green-500/30">
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
                                <div className="flex gap-1 mt-1">
                                    {stats.best_genome.capabilities.map((cap) => (
                                        <span key={cap} className="bg-purple-900/30 text-purple-300 px-2 py-0.5 rounded text-xs">
                                            {cap}
                                        </span>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <span className="text-gray-400">System Prompt:</span>
                                <p className="text-white mt-1 text-xs bg-black/30 p-2 rounded">
                                    {stats.best_genome.system_prompt.substring(0, 200)}...
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Meta-Learning Stats */}
                {metaStats && (
                    <div className="bg-gray-900/50 rounded-lg p-4">
                        <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                            <Lightbulb className="h-4 w-4 text-yellow-400" />
                            Meta-Learning Intelligence
                        </h3>
                        <div className="grid grid-cols-3 gap-4">
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
                                <div className="text-sm text-white mt-1">
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
        <div className="bg-gray-900/50 rounded px-3 py-2">
            <div className="flex items-center gap-2 mb-1">
                <div className={color}>{icon}</div>
                <div className="text-xs text-gray-400">{label}</div>
            </div>
            <div className={`text-xl font-bold ${color}`}>{value}</div>
        </div>
    );
}
