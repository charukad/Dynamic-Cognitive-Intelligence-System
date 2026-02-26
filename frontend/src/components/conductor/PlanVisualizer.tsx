'use client';

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
    NodeProps,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { apiClient } from '@/lib/api/client';
import {
    CheckCircle2,
    Circle,
    Clock,
    AlertCircle,
    GitBranch,
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

interface TaskNodeData {
    label: string;
    status: PlanNode['status'];
    priority: PlanNode['priority'];
    is_primitive: boolean;
    agent_type_hint?: string;
}

// ============================================================================
// Custom Node Component
// ============================================================================

const STATUS_STYLES: Record<PlanNode['status'], { icon: React.ReactNode; ring: string }> = {
    completed: { icon: <CheckCircle2 className="h-4 w-4 text-emerald-400" />, ring: 'ring-emerald-400/40' },
    in_progress: { icon: <Clock className="h-4 w-4 animate-pulse text-cyan-300" />, ring: 'ring-cyan-400/45' },
    failed: { icon: <AlertCircle className="h-4 w-4 text-rose-400" />, ring: 'ring-rose-400/45' },
    pending: { icon: <Circle className="h-4 w-4 text-slate-400" />, ring: 'ring-slate-500/35' },
};

const PRIORITY_STYLES: Record<PlanNode['priority'], string> = {
    critical: 'border-rose-500/55 bg-rose-950/35',
    high: 'border-orange-500/50 bg-orange-950/32',
    medium: 'border-cyan-500/45 bg-cyan-950/25',
    low: 'border-slate-500/45 bg-slate-950/35',
};

const CustomTaskNode = ({ data }: NodeProps<TaskNodeData>) => {
    const statusStyle = STATUS_STYLES[data.status] ?? STATUS_STYLES.pending;
    const priorityStyle = PRIORITY_STYLES[data.priority] ?? PRIORITY_STYLES.low;

    const nodeTypeLabel = data.is_primitive ? 'Primitive Task' : 'Compound Task';

    return (
        <div
            className={`min-w-[210px] rounded-xl border px-4 py-3 backdrop-blur-md transition-all duration-300 hover:-translate-y-0.5 hover:border-cyan-300/50 hover:shadow-[0_10px_24px_rgba(0,0,0,0.28)] ${priorityStyle} ${statusStyle.ring} ring-1`}
        >
            <div className="mb-2 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                    {statusStyle.icon}
                    <span className="text-[0.68rem] uppercase tracking-wide text-slate-300">
                        {data.status.replace('_', ' ')}
                    </span>
                </div>
                <span className="rounded-full border border-white/15 bg-slate-900/45 px-2 py-0.5 text-[0.62rem] uppercase tracking-wider text-slate-300">
                    {data.priority}
                </span>
            </div>

            <div className="mb-1 text-sm font-semibold leading-snug text-white">
                {data.label}
            </div>

            <div className="mb-1 text-[0.7rem] uppercase tracking-wide text-slate-400">
                {nodeTypeLabel}
            </div>

            {data.agent_type_hint && (
                <div className="text-xs text-slate-400">
                    Agent: <span className="font-medium text-fuchsia-300">{data.agent_type_hint}</span>
                </div>
            )}
        </div>
    );
};

const nodeTypes = {
    taskNode: CustomTaskNode,
};

function getNodeColor(status: unknown): string {
    switch (status) {
        case 'completed':
            return '#10b981';
        case 'in_progress':
            return '#22d3ee';
        case 'failed':
            return '#f43f5e';
        default:
            return '#64748b';
    }
}

function getEdgeColor(status: PlanNode['status']) {
    switch (status) {
        case 'completed':
            return '#10b981';
        case 'in_progress':
            return '#22d3ee';
        case 'failed':
            return '#f43f5e';
        default:
            return '#4f46e5';
    }
}

function createFallbackPlan(): ExecutionPlan {
    return {
        root_task: null,
        total_nodes: 0,
        primitive_count: 0,
        compound_count: 0,
        status_breakdown: {},
    };
}

// ============================================================================
// Main Component
// ============================================================================

interface PlanVisualizerProps {
    taskId?: string;
}

export function PlanVisualizer({ taskId = 'demo' }: PlanVisualizerProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState<TaskNodeData>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [plan, setPlan] = useState<ExecutionPlan | null>(createFallbackPlan());
    const [isLoading, setIsLoading] = useState(true);

    // Build React Flow graph from plan tree
    const buildGraph = useCallback((planData: ExecutionPlan) => {
        if (!planData.root_task) return;

        const newNodes: Node<TaskNodeData>[] = [];
        const newEdges: Edge[] = [];
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
                        stroke: getEdgeColor(node.status),
                        strokeWidth: 2,
                    },
                    markerEnd: {
                        type: MarkerType.ArrowClosed,
                        color: getEdgeColor(node.status),
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
                setPlan(createFallbackPlan());
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
        <div className="flex h-full w-full flex-col overflow-hidden rounded-2xl border border-cyan-500/20 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.13),_transparent_40%),linear-gradient(180deg,rgba(7,16,36,0.96),rgba(2,8,24,0.82))] shadow-[0_22px_64px_rgba(0,0,0,0.45)]">
            {/* Stats Header */}
            <div className="border-b border-cyan-500/15 bg-black/25 p-4 backdrop-blur-md md:p-5">
                <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold tracking-tight text-white sm:text-xl">
                    <GitBranch className="h-5 w-5 text-cyan-400" />
                    Execution Plan Visualization
                </h2>

                {plan && (
                    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
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
            <div className="min-h-0 flex-1">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    nodeTypes={nodeTypes}
                    fitView
                    className="bg-gradient-to-b from-slate-950/35 to-black/35"
                    attributionPosition="bottom-left"
                >
                    <Background color="#334155" gap={20} size={1.2} />
                    <Controls className="rounded-lg border border-cyan-500/20 bg-slate-950/70 text-slate-100" />
                    <MiniMap
                        className="rounded-lg border border-cyan-500/20 bg-slate-950/75"
                        nodeColor={(node) => {
                            const data = node.data as TaskNodeData | undefined;
                            return getNodeColor(data?.status);
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
        <div className="rounded-xl border border-white/8 bg-slate-950/55 px-3 py-2 transition-colors hover:border-cyan-400/30 hover:bg-slate-900/70">
            <div className="mb-1 text-xs uppercase tracking-wide text-gray-400">{label}</div>
            <div className={`text-lg font-bold ${color}`}>{value}</div>
        </div>
    );
}
