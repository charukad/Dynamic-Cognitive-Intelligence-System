/**
 * PlanVisualizer Component
 * 
 * Advanced interactive visualization of HTN Planner execution tree.
 * Uses React Flow for graph rendering with real-time updates.
 */

'use client';

import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
    Node,
    Edge,
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    Position,
    MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { motion } from 'framer-motion';
import { apiClient } from '@/lib/api/client';
import {
    CheckCircle2,
    Circle,
    Clock,
    AlertCircle,
    GitBranch,
    Layers
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

interface PlanNode {
    id: string;
    description: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    priority: 'low' | 'medium' | 'high' | 'critical';
    is_primitive: boolean;
    agent_type_hint?: string;
    children: PlanNode[];
}

interface ExecutionPlan {
    root_task: PlanNode | null;
    total_nodes: number;
    primitive_count: number;
    compound_count: number;
    status_breakdown: Record<string, number>;
}

// ============================================================================
// Custom Node Component
// ============================================================================

const CustomTaskNode = ({ data }: any) => {
    const StatusIcon = () => {
        switch (data.status) {
            case 'completed':
                return <CheckCircle2 className="h-4 w-4 text-green-500" />;
            case 'in_progress':
                return <Clock className="h-4 w-4 text-blue-500 animate-pulse" />;
            case 'failed':
                return <AlertCircle className="h-4 w-4 text-red-500" />;
            default:
                return <Circle className="h-4 w-4 text-gray-500" />;
        }
    };

    const priorityColors: Record<string, string> = {
        critical: 'border-red-500 bg-red-950/30',
        high: 'border-orange-500 bg-orange-950/30',
        medium: 'border-blue-500 bg-blue-950/30',
        low: 'border-gray-500 bg-gray-950/30',
    };

    const priorityColor = priorityColors[data.priority] || 'border-gray-500 bg-gray-950/30';

    return (
        <div
            className={`px-4 py-3 rounded-lg border-2 ${priorityColor} backdrop-blur-sm min-w-[200px]`}
        >
            <div className="flex items-center gap-2 mb-2">
                <StatusIcon />
                <div className="flex items-center gap-1">
                    {data.is_primitive ? (
                        <Circle className="h-3 w-3 text-purple-400" />
                    ) : (
                        <Layers className="h-3 w-3 text-cyan-400" />
                    )}
                </div>
            </div>

            <div className="text-sm font-medium text-white mb-1">
                {data.label}
            </div>

            {data.agent_type_hint && (
                <div className="text-xs text-gray-400">
                    Agent: <span className="text-purple-400">{data.agent_type_hint}</span>
                </div>
            )}
        </div>
    );
};

const nodeTypes = {
    taskNode: CustomTaskNode,
};

// ============================================================================
// Main Component
// ============================================================================

interface PlanVisualizerProps {
    taskId?: string;
}

export function PlanVisualizer({ taskId = 'demo' }: PlanVisualizerProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [plan, setPlan] = useState<ExecutionPlan | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Build React Flow graph from plan tree
    const buildGraph = useCallback((planData: ExecutionPlan) => {
        if (!planData.root_task) return;

        const newNodes: Node[] = [];
        const newEdges: Edge[] = [];
        let yOffset = 0;
        const levelSpacing = 150;

        const processNode = (
            node: PlanNode,
            depth: number,
            xOffset: number,
            parentId?: string
        ) => {
            const nodeId = node.id;

            // Create React Flow node
            newNodes.push({
                id: nodeId,
                type: 'taskNode',
                position: { x: xOffset, y: depth * levelSpacing },
                data: {
                    label: node.description,
                    status: node.status,
                    priority: node.priority,
                    is_primitive: node.is_primitive,
                    agent_type_hint: node.agent_type_hint,
                },
                sourcePosition: Position.Bottom,
                targetPosition: Position.Top,
            });

            // Create edge to parent
            if (parentId) {
                newEdges.push({
                    id: `e-${parentId}-${nodeId}`,
                    source: parentId,
                    target: nodeId,
                    type: 'smoothstep',
                    animated: node.status === 'in_progress',
                    style: {
                        stroke: node.status === 'completed' ? '#10b981' : '#667eea',
                        strokeWidth: 2,
                    },
                    markerEnd: {
                        type: MarkerType.ArrowClosed,
                        color: node.status === 'completed' ? '#10b981' : '#667eea',
                    },
                });
            }

            // Process children
            const childCount = node.children.length;
            const childSpacing = 300;
            const totalWidth = childCount * childSpacing;
            const startX = xOffset - (totalWidth / 2) + (childSpacing / 2);

            node.children.forEach((child, idx) => {
                const childX = startX + (idx * childSpacing);
                processNode(child, depth + 1, childX, nodeId);
            });
        };

        processNode(planData.root_task, 0, 400);

        setNodes(newNodes);
        setEdges(newEdges);
    }, [setNodes, setEdges]);

    // Fetch plan data
    useEffect(() => {
        const fetchPlan = async () => {
            setIsLoading(true);
            try {
                const response = await apiClient.get(`/v1/orchestrator/plan/${taskId}`);
                const data: ExecutionPlan = response.data || response;
                setPlan(data);
                buildGraph(data);
            } catch (error) {
                console.error('Failed to fetch execution plan:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchPlan();

        // Poll for updates every 2 seconds
        const interval = setInterval(fetchPlan, 2000);
        return () => clearInterval(interval);
    }, [taskId, buildGraph]);

    if (isLoading && !plan) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-400">Loading execution plan...</div>
            </div>
        );
    }

    return (
        <div className="h-full w-full bg-black/50 rounded-lg overflow-hidden">
            {/* Stats Header */}
            <div className="p-4 border-b border-gray-800 bg-black/30 backdrop-blur-sm">
                <h2 className="text-xl font-bold text-white mb-3 flex items-center gap-2">
                    <GitBranch className="h-5 w-5 text-cyan-400" />
                    Execution Plan Visualization
                </h2>

                {plan && (
                    <div className="grid grid-cols-4 gap-4">
                        <StatBadge
                            label="Total Nodes"
                            value={plan.total_nodes}
                            color="text-blue-400"
                        />
                        <StatBadge
                            label="Primitives"
                            value={plan.primitive_count}
                            color="text-purple-400"
                        />
                        <StatBadge
                            label="Completed"
                            value={plan.status_breakdown.completed || 0}
                            color="text-green-400"
                        />
                        <StatBadge
                            label="In Progress"
                            value={plan.status_breakdown.in_progress || 0}
                            color="text-orange-400"
                        />
                    </div>
                )}
            </div>

            {/* React Flow Canvas */}
            <div className="h-[calc(100%-120px)]">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    nodeTypes={nodeTypes}
                    fitView
                    attributionPosition="bottom-left"
                >
                    <Background color="#334155" gap={16} />
                    <Controls className="bg-black/50 border border-gray-700" />
                    <MiniMap
                        className="bg-black/50 border border-gray-700"
                        nodeColor={(node) => {
                            switch (node.data.status) {
                                case 'completed': return '#10b981';
                                case 'in_progress': return '#3b82f6';
                                case 'failed': return '#ef4444';
                                default: return '#6b7280';
                            }
                        }}
                    />
                </ReactFlow>
            </div>
        </div>
    );
}

// ============================================================================
// Helper Components
// ============================================================================

function StatBadge({ label, value, color }: { label: string; value: number; color: string }) {
    return (
        <div className="bg-gray-900/50 rounded px-3 py-2">
            <div className="text-xs text-gray-400 mb-1">{label}</div>
            <div className={`text-lg font-bold ${color}`}>{value}</div>
        </div>
    );
}
