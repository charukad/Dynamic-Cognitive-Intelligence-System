'use client';

/**
 * Feedback Analytics Dashboard
 * 
 * Visualize RLHF data:
 * - Agent performance ratings
 * - Feedback trends over time
 * - Top-rated agents leaderboard
 * - Feedback distribution
 */

'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { ThumbsUp, TrendingUp, Award, BarChart3, Activity } from 'lucide-react';
import { apiClient } from '@/lib/api/client';

// ============================================================================
// Types
// ============================================================================

interface FeedbackStats {
    total_feedback: number;
    total_agents_with_models: number;
    avg_rating_overall: number;
    thumbs_up_count: number;
    thumbs_down_count: number;
    approval_rate: number;
}

interface AgentRating {
    agent_id: string;
    avg_rating: number;
    accuracy: number;
    total_ratings: number;
}

interface FeedbackTrends {
    period_days: number;
    total_feedback: number;
    daily_average: number;
    trend: string;
    daily_counts: Record<string, number>;
}

// ============================================================================
// Main Component
// ============================================================================

export function FeedbackAnalyticsDashboard() {
    const [stats, setStats] = useState<FeedbackStats | null>(null);
    const [topAgents, setTopAgents] = useState<AgentRating[]>([]);
    const [trends, setTrends] = useState<FeedbackTrends | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchData = useCallback(async () => {
        try {
            const [statsRes, topAgentsRes, trendsRes] = await Promise.all([
                apiClient.get('/v1/rlhf/stats'),
                apiClient.get('/v1/rlhf/feedback/top-agents?limit=5'),
                apiClient.get('/v1/rlhf/feedback/trends?days=7'),
            ]);

            setStats(statsRes.data || statsRes);
            setTopAgents(topAgentsRes.data?.top_agents || []);
            setTrends(trendsRes.data || trendsRes);

            setIsLoading(false);
        } catch (error) {
            console.error('Failed to fetch feedback data:', error);
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        const initialFetchTimer = setTimeout(() => {
            void fetchData();
        }, 0);
        const interval = setInterval(() => {
            void fetchData();
        }, 10000); // Every 10 seconds

        return () => {
            clearTimeout(initialFetchTimer);
            clearInterval(interval);
        };
    }, [fetchData]);

    if (isLoading || !stats) {
        return (
            <div className="h-full flex items-center justify-center">
                <div className="text-gray-400">Loading feedback analytics...</div>
            </div>
        );
    }

    // Prepare chart data
    const feedbackDistribution = [
        { name: 'Thumbs Up', value: stats.thumbs_up_count, color: '#10b981' },
        { name: 'Thumbs Down', value: stats.thumbs_down_count, color: '#ef4444' },
    ];

    const trendData = trends ? Object.entries(trends.daily_counts).map(([date, count]) => ({
        date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        feedback: count,
    })) : [];

    return (
        <div className="h-full w-full bg-black/50 rounded-lg overflow-hidden flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-800 bg-black/30 backdrop-blur-sm">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <Award className="h-5 w-5 text-yellow-400" />
                    Feedback Analytics (RLHF)
                </h2>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Key Metrics */}
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
                    <MetricCard
                        label="Total Feedback"
                        value={stats.total_feedback.toString()}
                        icon={<Activity className="h-4 w-4 text-blue-400" />}
                        color="text-blue-400"
                    />
                    <MetricCard
                        label="Approval Rate"
                        value={`${(stats.approval_rate * 100).toFixed(1)}%`}
                        icon={<ThumbsUp className="h-4 w-4 text-green-400" />}
                        color="text-green-400"
                    />
                    <MetricCard
                        label="Avg Rating"
                        value={stats.avg_rating_overall.toFixed(2)}
                        icon={<Award className="h-4 w-4 text-yellow-400" />}
                        color="text-yellow-400"
                    />
                    <MetricCard
                        label="Agents Trained"
                        value={stats.total_agents_with_models.toString()}
                        icon={<BarChart3 className="h-4 w-4 text-purple-400" />}
                        color="text-purple-400"
                    />
                </div>

                <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                    {/* Feedback Distribution */}
                    <div className="bg-gray-900/50 rounded-lg p-4">
                        <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                            <Activity className="h-4 w-4 text-cyan-400" />
                            Feedback Distribution
                        </h3>
                        <ResponsiveContainer width="100%" height={200}>
                            <PieChart>
                                <Pie
                                    data={feedbackDistribution}
                                    dataKey="value"
                                    nameKey="name"
                                    cx="50%"
                                    cy="50%"
                                    outerRadius={80}
                                    label
                                >
                                    {feedbackDistribution.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                                />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Feedback Trends */}
                    <div className="bg-gray-900/50 rounded-lg p-4">
                        <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-green-400" />
                            Feedback Trends (7 Days)
                        </h3>
                        {trendData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={200}>
                                <LineChart data={trendData}>
                                    <XAxis dataKey="date" stroke="#666" />
                                    <YAxis stroke="#666" />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="feedback"
                                        stroke="#10b981"
                                        strokeWidth={2}
                                        dot={{ fill: '#10b981' }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-[200px] flex items-center justify-center text-gray-500">
                                No trend data available
                            </div>
                        )}
                    </div>
                </div>

                {/* Top-Rated Agents Leaderboard */}
                <div className="bg-gray-900/50 rounded-lg p-4">
                    <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                        <Award className="h-4 w-4 text-yellow-400" />
                        Top-Rated Agents
                    </h3>

                    {topAgents.length > 0 ? (
                        <div className="space-y-2">
                            {topAgents.map((agent, index) => (
                                <div
                                    key={agent.agent_id}
                                    className="flex items-center justify-between p-3 bg-black/30 rounded-lg hover:bg-black/50 transition-colors"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`text-2xl font-bold ${index === 0 ? 'text-yellow-400' :
                                                index === 1 ? 'text-gray-400' :
                                                    index === 2 ? 'text-orange-600' :
                                                        'text-gray-600'
                                            }`}>
                                            #{index + 1}
                                        </div>
                                        <div>
                                            <div className="text-white font-medium">
                                                {agent.agent_id.substring(0, 8)}...
                                            </div>
                                            <div className="text-xs text-gray-400">
                                                {agent.total_ratings} ratings
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-4">
                                        <div className="text-right">
                                            <div className="text-sm text-gray-400">Rating</div>
                                            <div className="text-lg font-bold text-green-400">
                                                {agent.avg_rating.toFixed(2)}
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-sm text-gray-400">Success</div>
                                            <div className="text-lg font-bold text-blue-400">
                                                {(agent.accuracy * 100).toFixed(0)}%
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500">
                            No agents with sufficient ratings yet
                        </div>
                    )}
                </div>

                {/* Trend Indicator */}
                {trends && (
                    <div className="bg-gray-900/50 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-white font-semibold">Overall Trend</h3>
                            <div className="flex items-center gap-2">
                                <TrendingUp className={`h-5 w-5 ${trends.trend === 'improving' ? 'text-green-400' :
                                        trends.trend === 'declining' ? 'text-red-400' :
                                            'text-gray-400'
                                    }`} />
                                <span className={`text-lg font-bold ${trends.trend === 'improving' ? 'text-green-400' :
                                        trends.trend === 'declining' ? 'text-red-400' :
                                            'text-gray-400'
                                    }`}>
                                    {trends.trend.replace('_', ' ').toUpperCase()}
                                </span>
                            </div>
                        </div>
                        <div className="mt-2 text-sm text-gray-400">
                            Daily average: {trends.daily_average.toFixed(1)} feedback items
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

interface MetricCardProps {
    label: string;
    value: string;
    icon: React.ReactNode;
    color: string;
}

function MetricCard({ label, value, icon, color }: MetricCardProps) {
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
