"use client"

import * as React from "react"
import { Activity, CheckCircle, Clock, AlertCircle } from "lucide-react"
import { useSwarmStore } from "@/store/swarmStore"
import { GlassPanel } from "@/components/ui/glass-panel"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Task } from "@/types/agent"

const statusIcons = {
    pending: { icon: Clock, color: "text-yellow-500" },
    in_progress: { icon: Activity, color: "text-cyan-500" },
    completed: { icon: CheckCircle, color: "text-green-500" },
    failed: { icon: AlertCircle, color: "text-red-500" },
}

const statusColors = {
    pending: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
    in_progress: "bg-cyan-500/10 text-cyan-500 border-cyan-500/20",
    completed: "bg-green-500/10 text-green-500 border-green-500/20",
    failed: "bg-red-500/10 text-red-500 border-red-500/20",
}

export function TaskPanel() {
    const { tasks } = useSwarmStore()

    // Group tasks by status or just list them? 
    // For now, a clean list with status indicators.

    return (
        <GlassPanel className="flex h-full w-full flex-col rounded-2xl border border-cyan-500/20 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_transparent_42%),linear-gradient(180deg,rgba(5,15,30,0.96),rgba(2,8,20,0.78))] p-4 shadow-[0_20px_60px_rgba(0,0,0,0.42)] animate-in fade-in slide-in-from-bottom-4 duration-500 delay-100">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-cyan-500/15 pb-4">
                <div className="flex items-center gap-2.5">
                    <Activity className="w-6 h-6 text-cyan-400" />
                    <h2 className="text-lg font-semibold tracking-wide text-cyan-100 sm:text-xl">Conductor Workflow</h2>
                </div>
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
                        <span className="text-xs text-white/50">{tasks.filter(t => t.status === 'in_progress').length} Active</span>
                    </div>
                    <div className="w-px h-4 bg-white/20" />
                    <span className="text-xs text-white/50">{tasks.length} Total</span>
                </div>
            </div>

            <ScrollArea className="flex-1 pr-4">
                <div className="space-y-3">
                    {tasks.length === 0 && (
                        <div className="flex h-40 items-center justify-center rounded-xl border border-dashed border-cyan-500/25 bg-slate-950/45 text-sm text-slate-400">
                            No active tasks assigned.
                        </div>
                    )}

                    {tasks.map((task) => {
                        const statusKey = task.status as keyof typeof statusIcons;
                        const StatusIcon = statusIcons[statusKey]?.icon || Clock;
                        return (
                            <div
                                key={task.id}
                                className="group relative rounded-xl border border-white/10 bg-slate-950/55 p-4 transition-all duration-250 hover:-translate-y-0.5 hover:border-cyan-400/30 hover:bg-slate-900/72"
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div className="space-y-1">
                                        <h3 className="font-medium text-cyan-50">{task.description}</h3>
                                        {task.subtasks && task.subtasks.length > 0 && (
                                            <p className="text-xs text-white/40 font-mono">
                                                {task.subtasks.filter((s: Task) => s.status === 'completed').length} / {task.subtasks.length} Subtasks
                                            </p>
                                        )}
                                    </div>

                                    <Badge variant="outline" className={`font-mono uppercase text-xs flex items-center gap-2 pl-2 pr-3 py-1 ${statusColors[statusKey] || ''}`}>
                                        <StatusIcon className="w-3 h-3" />
                                        {task.status.replace('_', ' ')}
                                    </Badge>
                                </div>

                                {/* Assigned Agent */}
                                {task.assignedTo && (
                                    <div className="mt-3 flex items-center gap-2 border-t border-cyan-500/10 pt-3">
                                        <div className="text-xs text-white/40">Assigned:</div>
                                        <div className="rounded-md border border-cyan-500/20 bg-cyan-950/30 px-2 py-0.5 text-xs font-mono text-cyan-300">
                                            {task.assignedTo}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>
            </ScrollArea>
        </GlassPanel>
    )
}
