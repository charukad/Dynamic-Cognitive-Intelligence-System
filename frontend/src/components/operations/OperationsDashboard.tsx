/**
 * Operations Dashboard - Production Monitoring & Health
 * 
 * Real-time monitoring of:
 * - Performance metrics (latency, throughput)
 * - Circuit breaker health
 * - Cache performance
 * - Distributed traces
 * - System health
 */

'use client';

import React, { useEffect, useState } from 'react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Zap, Database, Shield, Clock, TrendingUp, AlertCircle, CheckCircle2 } from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { Button } from '@/components/ui/button';

// ============================================================================
// Types
// ============================================================================

interface DashboardData {
    timestamp: string;
    metrics: {
        total_requests: number;
        avg_latency_ms: number;
        error_rate: number;
    };
    circuit_breaker: {
        state: string;
        success_rate: number;
        failure_rate: number;
    };
    cache: {
        hit_rate: number;
        size: number;
        utilization: number;
    };
    tracing: {
        active_traces: number;
        recent_traces: number;
    };
}

interface CacheStats {
    l1: {
        hits: number;
        misses: number;
        hit_rate: number;
        current_size: number;
        max_size: number;
        utilization: number;
    };
}

// ============================================================================
// Main Component
// ============================================================================

export function OperationsDashboard() {
    const [data, setData] = useState<DashboardData | null>(null);
    const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
    const [latencyHistory, setLatencyHistory] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000); // Every 5 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const [overviewRes, cacheRes] = await Promise.all([
                apiClient.get('/v1/monitoring/dashboard/overview'),
                apiClient.get('/v1/monitoring/cache/stats'),
            ]);

            const overview = overviewRes.data || overviewRes;

            // Validate and set data with defaults
            if (overview && overview.metrics) {
                setData(overview);

                // Update latency history only if metrics exist
                setLatencyHistory(prev => [
                    ...prev.slice(-19),
                    {
                        timestamp: new Date().toLocaleTimeString(),
                        latency: overview.metrics.avg_latency_ms || 0,
                    }
                ]);
            } else {
                // Set placeholder data if API returns invalid structure
                setData({
                    timestamp: new Date().toISOString(),
                    metrics: {
                        total_requests: 0,
                        avg_latency_ms: 0,
                        error_rate: 0,
                    },
                    circuit_breaker: {
                        state: 'closed',
                        success_rate: 1.0,
                        failure_rate: 0.0,
                    },
                    cache: {
                        hit_rate: 0,
                        size: 0,
                        utilization: 0,
                    },
                    tracing: {
                        active_traces: 0,
                        recent_traces: 0,
                    },
                });
            }

            setCacheStats(cacheRes.data || cacheRes);
            setIsLoading(false);
        } catch (error) {
            console.error('Failed to fetch monitoring data:', error);
            // Set default data on error to prevent crashes
            setData({
                timestamp: new Date().toISOString(),
                metrics: {
                    total_requests: 0,
                    avg_latency_ms: 0,
                    error_rate: 0,
                },
                circuit_breaker: {
                    state: 'closed',
                    success_rate: 1.0,
                    failure_rate: 0.0,
                },
                cache: {
                    hit_rate: 0,
                    size: 0,
                    utilization: 0,
                },
                tracing: {
                    active_traces: 0,
                    recent_traces: 0,
                },
            });
            setIsLoading(false);
        }
    };

    const handleClearCache = async () => {
        try {
            await apiClient.delete('/v1/monitoring/cache/clear');
            await fetchData();
        } catch (error) {
            console.error('Failed to clear cache:', error);
        }
    };

    const handleResetCircuitBreaker = async () => {
        try {
            await apiClient.post('/v1/monitoring/circuit-breaker/reset');
            await fetchData();
        } catch (error) {
            console.error('Failed to reset circuit breaker:', error);
        }
    };

    if (isLoading || !data) {
        return (
            <div className="h-full flex items-center justify-center">
                <div className="text-gray-400">Loading monitoring data...</div>
            </div>
        );
    }

    const circuitState = data.circuit_breaker.state;
    const isHealthy = circuitState === 'closed';

    return (
        <div className="h-full w-full bg-black/50 rounded-lg overflow-hidden flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-800 bg-black/30 backdrop-blur-sm">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <Activity className="h-5 w-5 text-green-400" />
                        Production Operations
                    </h2>
                    <div className="flex items-center gap-2">
                        {isHealthy ? (
                            <div className="flex items-center gap-2 text-green-400">
                                <CheckCircle2 className="h-5 w-5" />
                                <span className="text-sm font-medium">System Healthy</span>
                            </div>
                        ) : (
                            <div className="flex items-center gap-2 text-yellow-400">
                                <AlertCircle className="h-5 w-5" />
                                <span className="text-sm font-medium">Degraded</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Key Metrics */}
                <div className="grid grid-cols-4 gap-3">
                    <MetricCard
                        label="Avg Latency"
                        value={`${data.metrics.avg_latency_ms.toFixed(1)}ms`}
                        icon={<Clock className="h-4 w-4 text-blue-400" />}
                        color="text-blue-400"
                    />
                    <MetricCard
                        label="Total Requests"
                        value={data.metrics.total_requests.toString()}
                        icon={<TrendingUp className="h-4 w-4 text-purple-400" />}
                        color="text-purple-400"
                    />
                    <MetricCard
                        label="Cache Hit Rate"
                        value={`${(data.cache.hit_rate * 100).toFixed(1)}%`}
                        icon={<Database className="h-4 w-4 text-green-400" />}
                        color="text-green-400"
                    />
                    <MetricCard
                        label="Active Traces"
                        value={data.tracing.active_traces.toString()}
                        icon={<Activity className="h-4 w-4 text-cyan-400" />}
                        color="text-cyan-400"
                    />
                </div>

                {/* Latency Chart */}
                <div className="bg-gray-900/50 rounded-lg p-4">
                    <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                        <Clock className="h-4 w-4 text-blue-400" />
                        Latency Over Time
                    </h3>
                    <ResponsiveContainer width="100%" height={200}>
                        <LineChart data={latencyHistory}>
                            <XAxis dataKey="timestamp" stroke="#666" />
                            <YAxis stroke="#666" />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                            />
                            <Line type="monotone" dataKey="latency" stroke="#3b82f6" strokeWidth={2} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    {/* Circuit Breaker */}
                    <div className="bg-gray-900/50 rounded-lg p-4">
                        <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                            <Shield className="h-4 w-4 text-yellow-400" />
                            Circuit Breaker
                        </h3>

                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">State:</span>
                                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${circuitState === 'closed' ? 'bg-green-500/20 text-green-400' :
                                    circuitState === 'half_open' ? 'bg-yellow-500/20 text-yellow-400' :
                                        'bg-red-500/20 text-red-400'
                                    }`}>
                                    {circuitState.replace('_', ' ').toUpperCase()}
                                </span>
                            </div>

                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">Success Rate:</span>
                                <span className="text-white font-semibold">
                                    {(data.circuit_breaker.success_rate * 100).toFixed(1)}%
                                </span>
                            </div>

                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">Failure Rate:</span>
                                <span className="text-white font-semibold">
                                    {(data.circuit_breaker.failure_rate * 100).toFixed(1)}%
                                </span>
                            </div>

                            {circuitState !== 'closed' && (
                                <Button
                                    onClick={handleResetCircuitBreaker}
                                    variant="outline"
                                    className="w-full mt-2"
                                    size="sm"
                                >
                                    Reset Circuit Breaker
                                </Button>
                            )}
                        </div>
                    </div>

                    {/* Cache Performance */}
                    <div className="bg-gray-900/50 rounded-lg p-4">
                        <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                            <Database className="h-4 w-4 text-green-400" />
                            Cache Performance
                        </h3>

                        <div className="space-y-3">
                            {cacheStats && (
                                <>
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-gray-400">Hit Rate:</span>
                                        <span className="text-white font-semibold">
                                            {(cacheStats.l1.hit_rate * 100).toFixed(1)}%
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-gray-400">Size:</span>
                                        <span className="text-white font-semibold">
                                            {cacheStats.l1.current_size} / {cacheStats.l1.max_size}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-gray-400">Utilization:</span>
                                        <span className="text-white font-semibold">
                                            {(cacheStats.l1.utilization * 100).toFixed(1)}%
                                        </span>
                                    </div>

                                    <div className="w-full bg-gray-800 rounded-full h-2 mt-2">
                                        <div
                                            className="bg-green-500 h-2 rounded-full transition-all"
                                            style={{ width: `${cacheStats.l1.utilization * 100}%` }}
                                        />
                                    </div>
                                </>
                            )}

                            <Button
                                onClick={handleClearCache}
                                variant="outline"
                                className="w-full mt-2"
                                size="sm"
                            >
                                Clear Cache
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ============================================================================
// Helper Components
// ============================================================================

function MetricCard({ label, value, icon, color }: any) {
    return (
        <div className="bg-gray-900/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
                {icon}
                <span className="text-xs text-gray-400">{label}</span>
            </div>
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
        </div>
    );
}
