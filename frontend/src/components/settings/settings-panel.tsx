"use client"

import * as React from "react"
import { Settings, Cpu, Monitor } from "lucide-react"
import { useUIStore } from "@/store/uiStore"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Button } from "@/components/ui/button"
// import { Switch } from "@/components/ui/switch"
// Note: I don't have Switch installed so I will use button toggles or install Switch.
// I'll stick to button toggles for simplicity since I didn't verify Switch installation.
// Actually, I can simulate a switch with a styled button.

export function SettingsPanel() {
    const { settings, toggleSetting } = useUIStore()

    return (
        <GlassPanel className="w-full h-full flex flex-col p-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-100">
            <div className="flex items-center justify-between mb-8 border-b border-white/10 pb-4">
                <div className="flex items-center gap-2">
                    <Settings className="w-6 h-6 text-cyan-400" />
                    <h2 className="text-xl font-mono text-cyan-100 uppercase tracking-widest">System Configuration</h2>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl">

                {/* Graphics Settings */}
                <div className="space-y-4">
                    <h3 className="text-sm font-mono text-cyan-500 uppercase flex items-center gap-2">
                        <Monitor className="w-4 h-4" /> Graphics & Rendering
                    </h3>

                    <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/5">
                        <div className="space-y-1">
                            <div className="text-sm font-medium text-white">Post-Processing</div>
                            <div className="text-xs text-white/50">Bloom, Chromatic Aberration</div>
                        </div>
                        <Button
                            variant={settings.enablePostProcessing ? "default" : "outline"}
                            className={settings.enablePostProcessing ? "bg-cyan-600 hover:bg-cyan-500" : ""}
                            onClick={() => toggleSetting('enablePostProcessing')}
                        >
                            {settings.enablePostProcessing ? "ON" : "OFF"}
                        </Button>
                    </div>

                    <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/5">
                        <div className="space-y-1">
                            <div className="text-sm font-medium text-white">Performance Stats</div>
                            <div className="text-xs text-white/50">Show FPS & Memory usage</div>
                        </div>
                        <Button
                            variant={settings.showStats ? "default" : "outline"}
                            className={settings.showStats ? "bg-cyan-600 hover:bg-cyan-500" : ""}
                            onClick={() => toggleSetting('showStats')}
                        >
                            {settings.showStats ? "VISIBLE" : "HIDDEN"}
                        </Button>
                    </div>
                </div>

                {/* System Settings */}
                <div className="space-y-4">
                    <h3 className="text-sm font-mono text-cyan-500 uppercase flex items-center gap-2">
                        <Cpu className="w-4 h-4" /> System Performance
                    </h3>

                    <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/5">
                        <div className="space-y-1">
                            <div className="text-sm font-medium text-white">Low Power Mode</div>
                            <div className="text-xs text-white/50">Reduce particle count & animations</div>
                        </div>
                        <Button
                            variant={settings.lowPowerMode ? "default" : "outline"}
                            className={settings.lowPowerMode ? "bg-yellow-600 hover:bg-yellow-500" : ""}
                            onClick={() => toggleSetting('lowPowerMode')}
                        >
                            {settings.lowPowerMode ? "ACTIVE" : "DISABLED"}
                        </Button>
                    </div>
                </div>

            </div>

            <div className="mt-auto pt-4 border-t border-white/10 text-center">
                <p className="text-xs font-mono text-white/30">DCIS Frontend v0.1.0 • Build 2026.01.29</p>
            </div>

        </GlassPanel>
    )
}
