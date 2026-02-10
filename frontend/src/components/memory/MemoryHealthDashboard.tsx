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

import React, { useEffect, useState } from 'react';
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

// ============================================================================
// Main Component
// ============================================================================

export function MemoryHealthDashboard() {
    const [health, setHealth] = useState<MemoryHealth | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isOptimizing, setIsOptimizing] = useState(false);
    const [lastOptimization, setLastOptimization] = useState<OptimizationResult | null>(null);
    const [selectedAgentId, setSelectedAgentId] = useState('default-agent');

    // Fetch health data
    useEffect(() => {
        fetchHealth();
        const interval = setInterval(fetchHealth, 10000);
        return () => clearInterval(interval);
    }, [selectedAgentId]);

    const fetchHealth = async () => {
        try {
            const res = await apiClient.get(`/v1/memory/management/health/${selectedAgentId}`);
            setHealth(res.data || res);
        } catch (error) {
            console.error('Failed to fetch memory health:', error);
        } finally {
            setIsLoading(false);
        }
    };

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
            setLastOptimization({
                operation: 'optimize-all',
                success: res.data?.success || res.success,
                items_processed: 0,
                items_affected: res.data?.total_items_affected || res.total_items_affected || 0,
                storage_saved_mb: res.data?.total_storage_saved_mb || res.total_storage_saved_mb || 0,
                message: res.data?.message || res.message || 'Optimization complete',
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
        <div className="h-full w-full bg-black/50 rounded-lg overflow-hidden flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-800 bg-black/30 backdrop-blur-sm">
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
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
                <div className="grid grid-cols-4 gap-2">
                    <Button
                        onClick={handlePrune}
                        disabled={isOptimizing}
                        variant="outline"
                        className="flex items-center gap-2"
                    >
                        <Trash2 className="h-4 w-4" />
                        Prune
                    </Button>
                    <Button
                        onClick={handleCompress}
                        disabled={isOptimizing}
                        variant="outline"
                        className="flex items-center gap-2"
                    >
                        <Archive className="h-4 w-4" />
                        Compress
                    </Button>
                    <Button
                        disabled={isOptimizing}
                        variant="outline"
                        className="flex items-center gap-2"
                    >
                        <Share2 className="h-4 w-4" />
                        Share
                    </Button>
                    <Button
                        onClick={handleOptimizeAll}
                        disabled={isOptimizing}
                        className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600"
                    >
                        <Zap className="h-4 w-4" />
                        Optimize All
                    </Button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Stats Grid */}
                {health && (
                    <div className="grid grid-cols-4 gap-3">
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

                <div className="grid grid-cols-2 gap-4">
                    {/* Type Distribution */}
                    <div className="bg-gray-900/50 rounded-lg p-4">
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
                        <div className="bg-gray-900/50 rounded-lg p-4">
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
                        className="bg-gray-900/50 rounded-lg p-4 border border-green-500/30"
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
                                <div className="grid grid-cols-3 gap-4 text-xs">
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
        <div className="bg-gray-900/50 rounded px-3 py-2">
            <div className="flex items-center gap-2 mb-1">
                <div className={color}>{icon}</div>
                <div className="text-xs text-gray-400">{label}</div>
            </div>
            <div className={`text-xl font-bold ${color}`}>{value}</div>
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
        <div className="flex items-center justify-between p-2 bg-black/30 rounded">
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
