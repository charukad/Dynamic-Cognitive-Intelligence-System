"use client"

import * as React from "react"
import { LayoutDashboard, Network, MessageSquare, Activity, Settings, Database } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { GlassPanel } from "@/components/ui/glass-panel"

import { useUIStore } from "@/store/uiStore"

export function Sidebar({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    const { activeView, setActiveView } = useUIStore()

    const navItems = [
        { id: 'orbit', icon: LayoutDashboard, label: 'The Orbit' },
        { id: 'cortex', icon: Network, label: 'The Cortex' },
        { id: 'neural-link', icon: MessageSquare, label: 'Neural Link' },
        { id: 'conductor', icon: Activity, label: 'Conductor' },
        { id: 'settings', icon: Settings, label: 'Settings' },
    ] as const;

    return (
        <GlassPanel
            variant="thin"
            className={cn("w-16 flex flex-col items-center py-4 gap-4 z-50", className)}
            {...props}
        >
            <div className="mb-4">
                {/* Logo Placeholder */}
                <div className="w-10 h-10 rounded-full bg-cyan-500/20 border border-cyan-500/50 flex items-center justify-center animate-pulse">
                    <Database className="w-5 h-5 text-cyan-400" />
                </div>
            </div>

            <div className="flex-1 flex flex-col gap-2 w-full px-2">
                {navItems.map((item) => (
                    <Button
                        key={item.id}
                        variant="ghost"
                        size="icon"
                        className={cn(
                            "w-full aspect-square rounded-lg transition-all duration-300 hover:bg-cyan-500/20 hover:text-cyan-400",
                            activeView === item.id
                                ? "bg-cyan-500/10 text-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.3)]"
                                : "text-muted-foreground"
                        )}
                        onClick={() => setActiveView(item.id)}
                        title={item.label}
                    >
                        <item.icon className="w-5 h-5" />
                    </Button>
                ))}
            </div>

            <div className="mt-auto">
                {/* Status Indicator */}
                <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]" title="System Online" />
            </div>
        </GlassPanel>
    )
}
