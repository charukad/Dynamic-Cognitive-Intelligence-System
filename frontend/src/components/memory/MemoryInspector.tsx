/**
 * MemoryInspector Component
 * 
 * Advanced visualization of agent memory systems:
 * - 3D Knowledge Graph (Cytoscape)
 * - Episodic Timeline
 * - Semantic Memory Browser
 * - Real-time search and filtering
 */

'use client';

import React, { useEffect, useRef, useState } from 'react';
import cytoscape, { Core, ElementDefinition } from 'cytoscape';
import fcose from 'cytoscape-fcose';
import { motion } from 'framer-motion';
import {
    Brain,
    Clock,
    Search,
    Filter,
    Download,
    RefreshCw,
    Network,
    Activity
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

// Register Cytoscape extensions
if (typeof cytoscape !== 'undefined') {
    cytoscape.use(fcose);
}

// ============================================================================
// Types
// ============================================================================

interface GraphNode {
    id: string;
    label: string;
    type: string;
    properties: Record<string, any>;
    importance: number;
}

interface GraphEdge {
    source: string;
    target: string;
    relationship: string;
    properties: Record<string, any>;
}

interface KnowledgeGraph {
    nodes: GraphNode[];
    edges: GraphEdge[];
    stats: Record<string, number>;
}

interface TimelineEvent {
    id: string;
    timestamp: string;
    content: string;
    session_id: string | null;
    importance: number;
    tags: string[];
}

interface MemoryStats {
    total_memories: number;
    episodic_count: number;
    semantic_count: number;
    graph_nodes: number;
    graph_relationships: number;
    avg_importance: number;
}

import { MemoryHealthDashboard } from './MemoryHealthDashboard';

// ============================================================================
// Main Component
// ============================================================================

export function MemoryInspector() {
    const [activeView, setActiveView] = useState<'graph' | 'timeline' | 'search' | 'health'>('graph');
    const [graphData, setGraphData] = useState<KnowledgeGraph | null>(null);
    const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
    const [stats, setStats] = useState<MemoryStats | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [isLoading, setIsLoading] = useState(true);

    const cyContainerRef = useRef<HTMLDivElement>(null);
    const cyRef = useRef<Core | null>(null);

    // Fetch data
    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const [graphRes, timelineRes, statsRes] = await Promise.all([
                    apiClient.get('/v1/memory/visualization/graph'),
                    apiClient.get('/v1/memory/visualization/timeline'),
                    apiClient.get('/v1/memory/visualization/stats'),
                ]);

                setGraphData(graphRes.data || graphRes);
                setTimeline(timelineRes.data || timelineRes);
                setStats(statsRes.data || statsRes);
            } catch (error) {
                console.error('Failed to fetch memory data:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, []);

    // Initialize Cytoscape graph
    useEffect(() => {
        if (!cyContainerRef.current || !graphData || activeView !== 'graph') return;

        // Convert data to Cytoscape format
        const elements: ElementDefinition[] = [
            ...graphData.nodes.map(node => ({
                data: {
                    id: node.id,
                    label: node.label,
                    type: node.type,
                    importance: node.importance,
                },
            })),
            ...graphData.edges.map(edge => ({
                data: {
                    id: `${edge.source}-${edge.target}`,
                    source: edge.source,
                    target: edge.target,
                    label: edge.relationship,
                },
            })),
        ];

        // Initialize Cytoscape
        const cy = cytoscape({
            container: cyContainerRef.current,
            elements,
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': (ele: any) => {
                            const importance = ele.data('importance');
                            if (importance > 0.8) return '#10b981';
                            if (importance > 0.6) return '#3b82f6';
                            return '#6b7280';
                        },
                        'label': 'data(label)',
                        'color': '#fff',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'font-size': '12px',
                        'width': (ele: any) => 30 + (ele.data('importance') * 30),
                        'height': (ele: any) => 30 + (ele.data('importance') * 30),
                    },
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': '#667eea',
                        'target-arrow-color': '#667eea',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(label)',
                        'font-size': '10px',
                        'color': '#9ca3af',
                        'text-rotation': 'autorotate',
                    },
                },
            ],
            layout: {
                name: 'fcose',
                quality: 'proof',
                randomize: false,
                animate: true,
                animationDuration: 500,
                fit: true,
                padding: 50,
                nodeSeparation: 100,
            } as any,
        });

        // Add interactivity
        cy.on('tap', 'node', (evt) => {
            const node = evt.target;
            console.log('Selected node:', node.data());
        });

        cyRef.current = cy;

        return () => {
            cy.destroy();
        };
    }, [graphData, activeView]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-400">Loading memory systems...</div>
            </div>
        );
    }

    return (
        <div className="h-full w-full bg-black/50 rounded-lg overflow-hidden flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-800 bg-black/30 backdrop-blur-sm">
                <h2 className="text-xl font-bold text-white mb-3 flex items-center gap-2">
                    <Brain className="h-5 w-5 text-purple-400" />
                    Memory Inspector
                </h2>

                {/* Stats */}
                {stats && (
                    <div className="grid grid-cols-6 gap-2">
                        <StatCard label="Total" value={stats.total_memories} color="text-blue-400" />
                        <StatCard label="Episodic" value={stats.episodic_count} color="text-green-400" />
                        <StatCard label="Semantic" value={stats.semantic_count} color="text-purple-400" />
                        <StatCard label="Nodes" value={stats.graph_nodes} color="text-cyan-400" />
                        <StatCard label="Relations" value={stats.graph_relationships} color="text-orange-400" />
                        <StatCard label="Avg ★" value={stats.avg_importance.toFixed(2)} color="text-yellow-400" />
                    </div>
                )}

                {/* View Tabs */}
                <div className="flex gap-2 mt-4">
                    <TabButton
                        active={activeView === 'graph'}
                        onClick={() => setActiveView('graph')}
                        icon={<Network size={16} />}
                        label="Knowledge Graph"
                    />
                    <TabButton
                        active={activeView === 'timeline'}
                        onClick={() => setActiveView('timeline')}
                        icon={<Clock size={16} />}
                        label="Timeline"
                    />
                    <TabButton
                        active={activeView === 'search'}
                        onClick={() => setActiveView('search')}
                        icon={<Search size={16} />}
                        label="Search"
                    />
                    <TabButton
                        active={activeView === 'health'}
                        onClick={() => setActiveView('health')}
                        icon={<Activity size={16} />}
                        label="Health"
                    />
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-hidden">
                {activeView === 'graph' && (
                    <div ref={cyContainerRef} className="w-full h-full bg-gray-950" />
                )}

                {activeView === 'timeline' && (
                    <div className="p-4 h-full overflow-y-auto">
                        <div className="space-y-3">
                            {timeline.map((event) => (
                                <TimelineEventCard key={event.id} event={event} />
                            ))}
                        </div>
                    </div>
                )}

                {activeView === 'search' && (
                    <div className="p-4">
                        <div className="flex gap-2 mb-4">
                            <Input
                                placeholder="Search memories..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="flex-1"
                            />
                            <Button variant="outline">
                                <Search size={16} />
                            </Button>
                        </div>
                        <div className="text-gray-400 text-sm">
                            Enter a query to search across all memory types
                        </div>
                    </div>
                )}

                {activeView === 'health' && (
                    <MemoryHealthDashboard />
                )}
            </div>
        </div>
    );
}

// ============================================================================
// Helper Components
// ============================================================================

function StatCard({ label, value, color }: { label: string; value: number | string; color: string }) {
    return (
        <div className="bg-gray-900/50 rounded px-2 py-1.5">
            <div className="text-xs text-gray-400">{label}</div>
            <div className={`text-sm font-bold ${color}`}>{value}</div>
        </div>
    );
}

function TabButton({
    active,
    onClick,
    icon,
    label
}: {
    active: boolean;
    onClick: () => void;
    icon: React.ReactNode;
    label: string;
}) {
    return (
        <button
            onClick={onClick}
            className={`
                flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm
                transition-all duration-200
                ${active
                    ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/30'
                    : 'bg-gray-800/50 text-gray-400 hover:bg-gray-700/50'
                }
            `}
        >
            {icon}
            {label}
        </button>
    );
}

function TimelineEventCard({ event }: { event: TimelineEvent }) {
    return (
        <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-gray-900/50 rounded-lg p-4 border border-gray-800"
        >
            <div className="flex items-start justify-between mb-2">
                <div className="text-xs text-gray-400">
                    {new Date(event.timestamp).toLocaleString()}
                </div>
                <div className="text-xs text-yellow-400">
                    ★ {event.importance.toFixed(2)}
                </div>
            </div>
            <div className="text-white mb-2">{event.content}</div>
            <div className="flex gap-1">
                {event.tags.map((tag) => (
                    <span key={tag} className="text-xs bg-purple-900/30 text-purple-300 px-2 py-0.5 rounded">
                        {tag}
                    </span>
                ))}
            </div>
        </motion.div>
    );
}
