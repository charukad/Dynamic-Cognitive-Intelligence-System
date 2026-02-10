"use client";

import { useMemo } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";

export function LoadingSpinner() {
    return (
        <div className="flex h-screen items-center justify-center">
            <div className="relative h-16 w-16">
                <div className="absolute inset-0 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                <div className="absolute inset-2 animate-pulse rounded-full bg-primary/20" />
            </div>
        </div>
    );
}

export function LoadingDots() {
    return (
        <div className="flex items-center gap-1">
            <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]" />
            <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]" />
            <div className="h-2 w-2 animate-bounce rounded-full bg-primary" />
        </div>
    );
}

export function LoadingPulse() {
    return (
        <div className="flex items-center gap-2">
            <div className="h-3 w-3 animate-pulse rounded-full bg-blue-500" />
            <div className="h-3 w-3 animate-pulse rounded-full bg-purple-500 [animation-delay:150ms]" />
            <div className="h-3 w-3 animate-pulse rounded-full bg-pink-500 [animation-delay:300ms]" />
        </div>
    );
}

export function AgentsListSkeleton() {
    return (
        <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
                <Card key={i} className="p-6">
                    <div className="flex items-start gap-4">
                        <Skeleton className="h-12 w-12 rounded-full" />
                        <div className="flex-1 space-y-2">
                            <Skeleton className="h-5 w-32" />
                            <Skeleton className="h-4 w-full" />
                            <Skeleton className="h-4 w-3/4" />
                            <div className="flex gap-2 pt-2">
                                <Skeleton className="h-6 w-16 rounded-full" />
                                <Skeleton className="h-6 w-16 rounded-full" />
                            </div>
                        </div>
                    </div>
                </Card>
            ))}
        </div>
    );
}

export function ChatSkeleton() {
    return (
        <div className="flex h-full flex-col">
            {/* Header */}
            <div className="border-b p-4">
                <div className="flex items-center gap-3">
                    <Skeleton className="h-10 w-10 rounded-full" />
                    <div className="flex-1">
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="mt-1 h-3 w-20" />
                    </div>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 space-y-4 p-4">
                {Array.from({ length: 4 }).map((_, i) => (
                    <div
                        key={i}
                        className={`flex ${i % 2 === 0 ? "justify-end" : "justify-start"}`}
                    >
                        <div className={`flex max-w-[70%] gap-2 ${i % 2 === 0 ? "flex-row-reverse" : ""}`}>
                            <Skeleton className="h-8 w-8 rounded-full" />
                            <div className="space-y-2">
                                <Skeleton className="h-4 w-40" />
                                <Skeleton className="h-16 w-64 rounded-2xl" />
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Input */}
            <div className="border-t p-4">
                <Skeleton className="h-12 w-full rounded-full" />
            </div>
        </div>
    );
}

export function OrbitSkeleton() {
    // Generate particle positions once using useMemo to avoid purity violations
    const randomizedParticles = useMemo(() =>
        Array.from({ length: 20 }, (_, i): { id: number; left: number; top: number; delay: number } => ({
            id: i,
            left: Math.random() * 100,
            top: Math.random() * 100,
            delay: Math.random() * 2,
        }))
        , []);

    return (
        <div className="relative h-screen w-full overflow-hidden bg-gradient-to-br from-slate-950 via-blue-950 to-purple-950">
            {/* Animated particles */}
            <div className="absolute inset-0">
                {randomizedParticles.map((particle) => (
                    <div
                        key={particle.id}
                        className="absolute h-2 w-2 animate-pulse rounded-full bg-blue-500/30"
                        style={{
                            left: `${particle.left}%`,
                            top: `${particle.top}%`,
                            animationDelay: `${particle.delay}s`,
                        }}
                    />
                ))}
            </div>

            {/* Loading text */}
            <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                    <LoadingSpinner />
                    <p className="mt-4 text-lg text-white/60">Initializing Orbit...</p>
                </div>
            </div>
        </div>
    );
}

export function DashboardSkeleton() {
    return (
        <div className="space-y-6 p-6">
            {/* Header */}
            <div>
                <Skeleton className="h-8 w-64" />
                <Skeleton className="mt-2 h-4 w-96" />
            </div>

            {/* Stats Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {Array.from({ length: 4 }).map((_, i) => (
                    <Card key={i} className="p-6">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="mt-2 h-8 w-16" />
                        <Skeleton className="mt-2 h-3 w-32" />
                    </Card>
                ))}
            </div>

            {/* Content Grid */}
            <div className="grid gap-6 lg:grid-cols-2">
                <Card className="p-6">
                    <Skeleton className="h-6 w-32" />
                    <div className="mt-4 space-y-3">
                        {Array.from({ length: 5 }).map((_, i) => (
                            <Skeleton key={i} className="h-12 w-full" />
                        ))}
                    </div>
                </Card>

                <Card className="p-6">
                    <Skeleton className="h-6 w-32" />
                    <Skeleton className="mt-4 h-64 w-full" />
                </Card>
            </div>
        </div>
    );
}

export function PageLoadingState({ message = "Loading..." }: { message?: string }) {
    return (
        <div className="flex h-screen flex-col items-center justify-center gap-4">
            <LoadingSpinner />
            <p className="text-muted-foreground">{message}</p>
        </div>
    );
}
