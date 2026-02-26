'use client';

/**
 * Memory Health Dashboard
 * 
 * Advanced memory management interface:
 * - Real-time health monitoring
 * - One-click optimization (prune, compress, share)
 * - Storage analytics
 * - Optimization history
 */

'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
    Database,
    Trash2,
    Archive,
    Share2,
    Zap,
    TrendingDown,
    AlertCircle,
    CheckCircle,
    Activity
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
    PieChart,
    Pie,
    Cell,
    ResponsiveContainer,
    Legend,
    Tooltip
} from 'recharts';

// ============================================================================
// Types
// ============================================================================

interface MemoryHealth {
    total_memories: number;
    episodic_count: number;
    semantic_count: number;
    avg_importance: number;
    storage_mb: number;
    old_memories_count: number;
    low_importance_count: number;
    health_score: number;
}

interface OptimizationResult {
    operation: string;
    success: boolean;
    items_processed: number;
    items_affected: number;
    storage_saved_mb: number;
    message: string;
}

interface OptimizeAllResponse {
    success?: boolean;
    total_items_affected?: number;
    total_storage_saved_mb?: number;
    message?: string;
}

// ============================================================================
// Main Component
// ============================================================================

export function MemoryHealthDashboard() {
    const [health, setHealth] = useState<MemoryHealth | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isOptimizing, setIsOptimizing] = useState(false);
    const [lastOptimization, setLastOptimization] = useState<OptimizationResult | null>(null);
    const selectedAgentId = 'default-agent';

    const fetchHealth = useCallback(async () => {
        try {
            const res = await apiClient.get(`/v1/memory/management/health/${selectedAgentId}`);
            setHealth(res.data || res);
        } catch (error) {
            console.error('Failed to fetch memory health:', error);
        } finally {
            setIsLoading(false);
        }
    }, [selectedAgentId]);

    // Fetch health data
    useEffect(() => {
        const initialFetchTimer = setTimeout(() => {
            void fetchHealth();
        }, 0);
        const interval = setInterval(() => {
            void fetchHealth();
        }, 10000);

        return () => {
            clearTimeout(initialFetchTimer);
            clearInterval(interval);
        };
    }, [fetchHealth]);

    const handlePrune = async () => {
        setIsOptimizing(true);
        try {
            const res = await apiClient.post('/v1/memory/management/prune', {
                agent_id: selectedAgentId,
                max_keep: 1000,
                force_prune: false,
            });
            setLastOptimization(res.data || res);
            await fetchHealth();
        } catch (error) {
            console.error('Pruning failed:', error);
        } finally {
            setIsOptimizing(false);
        }
    };

    const handleCompress = async () => {
        setIsOptimizing(true);
        try {
            const res = await apiClient.post('/v1/memory/management/compress', {
                agent_id: selectedAgentId,
                min_age_days: 30,
            });
            setLastOptimization(res.data || res);
            await fetchHealth();
        } catch (error) {
            console.error('Compression failed:', error);
        } finally {
            setIsOptimizing(false);
        }
    };

    const handleOptimizeAll = async () => {
        setIsOptimizing(true);
        try {
            const res = await apiClient.post(`/v1/memory/management/optimize-all/${selectedAgentId}`);
            const data = (res.data || res) as OptimizeAllResponse;
            setLastOptimization({
                operation: 'optimize-all',
                success: data.success || false,
                items_processed: 0,
                items_affected: data.total_items_affected || 0,
                storage_saved_mb: data.total_storage_saved_mb || 0,
                message: data.message || 'Optimization complete',
            });
            await fetchHealth();
        } catch (error) {
            console.error('Optimization failed:', error);
        } finally {
            setIsOptimizing(false);
        }
    };

    if (isLoading && !health) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-400">Loading memory health...</div>
            </div>
        );
    }

    // Prepare chart data
    const typeDistribution = health ? [
        { name: 'Episodic', value: health.episodic_count, color: '#3b82f6' },
        { name: 'Semantic', value: health.semantic_count, color: '#a855f7' },
    ] : [];

    const healthColor = health ? (
        health.health_score >= 0.7 ? 'text-green-400' :
            health.health_score >= 0.4 ? 'text-yellow-400' :
                'text-red-400'
    ) : 'text-gray-400';

    return (
        <div className="h-full w-full overflow-hidden rounded-2xl border border-indigo-500/20 bg-[radial-gradient(circle_at_top,_rgba(99,102,241,0.14),_transparent_40%),linear-gradient(180deg,rgba(4,8,24,0.96),rgba(15,23,42,0.78))] shadow-[0_22px_64px_rgba(0,0,0,0.48)] flex flex-col">
            {/* Header */}
            <div className="border-b border-indigo-500/15 bg-black/25 p-4 backdrop-blur-md md:p-5">
                <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold tracking-tight text-white sm:text-xl">
                    <Database className="h-5 w-5 text-blue-400" />
                    Memory Health Dashboard
                </h2>

                {/* Health Score */}
                {health && (
                    <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-gray-400">Overall Health</span>
                            <span className={`text-2xl font-bold ${healthColor}`}>
                                {(health.health_score * 100).toFixed(0)}%
                            </span>
                        </div>
                        <Progress value={health.health_score * 100} className="h-2" />
                    </div>
                )}

                {/* Quick Actions */}
                <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
                    <Button
                        onClick={handlePrune}
                        disabled={isOptimizing}
                        variant="outline"
                        className="flex items-center gap-2 border-blue-400/30 text-blue-200 hover:border-blue-300/60 hover:bg-blue-500/10"
                    >
                        <Trash2 className="h-4 w-4" />
                        Prune
                    </Button>
                    <Button
                        onClick={handleCompress}
                        disabled={isOptimizing}
                        variant="outline"
                        className="flex items-center gap-2 border-violet-400/30 text-violet-200 hover:border-violet-300/60 hover:bg-violet-500/10"
                    >
                        <Archive className="h-4 w-4" />
                        Compress
                    </Button>
                    <Button
                        disabled={isOptimizing}
                        variant="outline"
                        className="flex items-center gap-2 border-cyan-400/30 text-cyan-200 hover:border-cyan-300/60 hover:bg-cyan-500/10"
                    >
                        <Share2 className="h-4 w-4" />
                        Share
                    </Button>
                    <Button
                        onClick={handleOptimizeAll}
                        disabled={isOptimizing}
                        className="flex items-center gap-2 bg-gradient-to-r from-blue-600 via-indigo-500 to-cyan-500 hover:from-blue-500 hover:via-indigo-400 hover:to-cyan-400"
                    >
                        <Zap className="h-4 w-4" />
                        Optimize All
                    </Button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 space-y-4 overflow-y-auto p-4 md:space-y-5 md:p-5">
                {/* Stats Grid */}
                {health && (
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
                        <MetricCard
                            icon={<Database className="h-5 w-5" />}
                            label="Total Memories"
                            value={health.total_memories}
                            color="text-blue-400"
                        />
                        <MetricCard
                            icon={<Activity className="h-5 w-5" />}
                            label="Avg Importance"
                            value={health.avg_importance.toFixed(2)}
                            color="text-green-400"
                        />
                        <MetricCard
                            icon={<TrendingDown className="h-5 w-5" />}
                            label="Storage"
                            value={`${health.storage_mb.toFixed(1)} MB`}
                            color="text-cyan-400"
                        />
                        <MetricCard
                            icon={<AlertCircle className="h-5 w-5" />}
                            label="Old Memories"
                            value={health.old_memories_count}
                            color="text-orange-400"
                        />
                    </div>
                )}

                <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                    {/* Type Distribution */}
                    <div className="rounded-xl border border-indigo-500/10 bg-slate-950/55 p-4 md:p-5">
                        <h3 className="text-white font-semibold mb-4">Memory Distribution</h3>
                        <ResponsiveContainer width="100%" height={200}>
                            <PieChart>
                                <Pie
                                    data={typeDistribution}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={50}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {typeDistribution.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        background: 'rgba(31, 31, 58, 0.9)',
                                        border: '1px solid rgba(102, 126, 234, 0.3)',
                                        borderRadius: '0.5rem',
                                    }}
                                />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Optimization Opportunities */}
                    {health && (
                        <div className="rounded-xl border border-indigo-500/10 bg-slate-950/55 p-4 md:p-5">
                            <h3 className="text-white font-semibold mb-4">Optimization Opportunities</h3>
                            <div className="space-y-3">
                                <OpportunityCard
                                    icon={<Trash2 className="h-4 w-4" />}
                                    title="Low Importance Memories"
                                    count={health.low_importance_count}
                                    action="Prune to save space"
                                    severity={health.low_importance_count > 100 ? 'high' : 'medium'}
                                />
                                <OpportunityCard
                                    icon={<Archive className="h-4 w-4" />}
                                    title="Old Episodes"
                                    count={health.old_memories_count}
                                    action="Compress to summaries"
                                    severity={health.old_memories_count > 200 ? 'high' : 'low'}
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* Last Optimization Result */}
                {lastOptimization && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="rounded-xl border border-emerald-500/30 bg-slate-950/55 p-4 md:p-5"
                    >
                        <div className="flex items-start gap-3">
                            <CheckCircle className="h-5 w-5 text-green-400 mt-0.5" />
                            <div className="flex-1">
                                <div className="text-white font-semibold mb-1">
                                    {lastOptimization.operation.toUpperCase()} Complete
                                </div>
                                <div className="text-sm text-gray-400 mb-2">
                                    {lastOptimization.message}
                                </div>
                                <div className="grid grid-cols-1 gap-3 text-xs sm:grid-cols-2">
                                    <div>
                                        <span className="text-gray-500">Items Affected:</span>
                                        <span className="text-blue-400 ml-1 font-bold">
                                            {lastOptimization.items_affected}
                                        </span>
                                    </div>
                                    <div>
                                        <span className="text-gray-500">Storage Saved:</span>
                                        <span className="text-green-400 ml-1 font-bold">
                                            {lastOptimization.storage_saved_mb.toFixed(1)} MB
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </div>
        </div>
    );
}

// ============================================================================
// Helper Components
// ============================================================================

function MetricCard({
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
        <div className="rounded-xl border border-white/8 bg-slate-950/55 px-3 py-2 transition-all duration-300 hover:-translate-y-0.5 hover:border-indigo-400/25 hover:bg-slate-900/75">
            <div className="flex items-center gap-2 mb-1">
                <div className={color}>{icon}</div>
                <div className="text-xs uppercase tracking-wide text-gray-400">{label}</div>
            </div>
            <div className={`text-xl font-bold leading-none ${color}`}>{value}</div>
        </div>
    );
}

function OpportunityCard({
    icon,
    title,
    count,
    action,
    severity,
}: {
    icon: React.ReactNode;
    title: string;
    count: number;
    action: string;
    severity: 'low' | 'medium' | 'high';
}) {
    const severityColor = {
        low: 'text-blue-400',
        medium: 'text-yellow-400',
        high: 'text-red-400',
    }[severity];

    return (
        <div className="flex items-center justify-between rounded-lg border border-white/8 bg-black/30 p-2.5 transition-colors hover:border-indigo-400/20 hover:bg-indigo-950/20">
            <div className="flex items-center gap-2">
                <div className={severityColor}>{icon}</div>
                <div>
                    <div className="text-sm text-white">{title}</div>
                    <div className="text-xs text-gray-400">{action}</div>
                </div>
            </div>
            <div className={`text-lg font-bold ${severityColor}`}>{count}</div>
        </div>
    );
}
