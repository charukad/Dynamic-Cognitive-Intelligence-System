"use client"

import * as React from "react"
import { Activity, CheckCircle, Clock, AlertCircle } from "lucide-react"
import { useSwarmStore } from "@/store/swarmStore"
import { GlassPanel } from "@/components/ui/glass-panel"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"

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
        <GlassPanel className="w-full h-full flex flex-col p-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-100">
            <div className="flex items-center justify-between mb-4 border-b border-white/10 pb-4">
                <div className="flex items-center gap-2">
                    <Activity className="w-6 h-6 text-cyan-400" />
                    <h2 className="text-xl font-mono text-cyan-100 uppercase tracking-widest">Conductor // Workflow</h2>
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
                        <div className="h-40 flex items-center justify-center text-white/30 font-mono text-sm border border-dashed border-white/10 rounded-lg">
                            No active tasks assigned.
                        </div>
                    )}

                    {tasks.map((task) => {
                        const StatusIcon = statusIcons[task.status].icon
                        return (
                            <div
                                key={task.id}
                                className="group relative p-4 bg-white/5 hover:bg-white/10 border border-white/5 hover:border-cyan-500/30 rounded-lg transition-all"
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div className="space-y-1">
                                        <h3 className="font-medium text-cyan-50">{task.description}</h3>
                                        {task.subtasks.length > 0 && (
                                            <p className="text-xs text-white/40 font-mono">
                                                {task.subtasks.filter(s => s.status === 'completed').length} / {task.subtasks.length} Subtasks
                                            </p>
                                        )}
                                    </div>

                                    <Badge variant="outline" className={`font-mono uppercase text-xs flex items-center gap-2 pl-2 pr-3 py-1 ${statusColors[task.status]}`}>
                                        <StatusIcon className="w-3 h-3" />
                                        {task.status.replace('_', ' ')}
                                    </Badge>
                                </div>

                                {/* Assigned Agent */}
                                {task.assignedTo && (
                                    <div className="mt-3 flex items-center gap-2 pt-3 border-t border-white/5">
                                        <div className="text-xs text-white/40">Assigned:</div>
                                        <div className="text-xs font-mono text-cyan-400 bg-cyan-950/30 px-2 py-0.5 rounded border border-cyan-500/20">
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
