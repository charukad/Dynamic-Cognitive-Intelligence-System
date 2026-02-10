"use client"

import * as React from "react"
import { Sidebar } from "./sidebar"

interface DashboardLayoutProps {
    children: React.ReactNode
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
    return (
        <div className="relative w-full h-full flex overflow-hidden pointer-events-none">
            {/* Pointer events none allows clicks to pass through to 3D canvas where no UI exists */}

            {/* Sidebar - Left Rail */}
            <div className="h-full p-4 pointer-events-auto">
                <Sidebar className="h-full" />
            </div>

            {/* Main Content Area - Overlay */}
            <main className="flex-1 h-full p-4 pl-0 pointer-events-auto overflow-hidden flex flex-col">
                {children}
            </main>
        </div>
    )
}
