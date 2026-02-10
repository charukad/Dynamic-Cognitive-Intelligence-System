"use client";

import { useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    BrainCircuitIcon,
    SparklesIcon,
    BookOpenIcon,
    AlertCircleIcon,
    CodeIcon,
    BriefcaseIcon,
} from "lucide-react";

interface DebateArgument {
    agentId: string;
    agentName: string;
    agentType: string;
    content: string;
    round: number;
    timestamp: Date;
    stance: "for" | "against" | "neutral";
}

interface DebateVisualizationProps {
    topic: string;
    arguments?: DebateArgument[];
    isActive?: boolean;
}

const AGENT_ICONS = {
    logician: BrainCircuitIcon,
    creative: SparklesIcon,
    scholar: BookOpenIcon,
    critic: AlertCircleIcon,
    coder: CodeIcon,
    executive: BriefcaseIcon,
};

const AGENT_COLORS = {
    logician: "bg-blue-500/10 text-blue-500 border-blue-500/20",
    creative: "bg-pink-500/10 text-pink-500 border-pink-500/20",
    scholar: "bg-purple-500/10 text-purple-500 border-purple-500/20",
    critic: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
    coder: "bg-green-500/10 text-green-500 border-green-500/20",
    executive: "bg-orange-500/10 text-orange-500 border-orange-500/20",
};

export function DebateVisualization({
    topic,
    arguments: debateArguments = [],
    isActive = false,
}: DebateVisualizationProps) {
    const [selectedRound, setSelectedRound] = useState<number | null>(null);
    const maxRound = Math.max(...debateArguments.map((a) => a.round), 0);

    // Derive current round from debate arguments instead of using setState in effect
    const currentRound = useMemo(() => {
        if (selectedRound !== null) return selectedRound;
        if (isActive && debateArguments.length > 0) {
            return debateArguments[debateArguments.length - 1].round;
        }
        return 1;
    }, [selectedRound, debateArguments, isActive]);

    const filterByRound = (round: number) => {
        return debateArguments.filter((arg) => arg.round === round);
    };

    const getAgentIcon = (type: string) => {
        const Icon = AGENT_ICONS[type as keyof typeof AGENT_ICONS] || BrainCircuitIcon;
        return Icon;
    };

    const getAgentColor = (type: string) => {
        return AGENT_COLORS[type as keyof typeof AGENT_COLORS] || AGENT_COLORS.logician;
    };

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold">Multi-Agent Debate</h2>
                    <p className="text-sm text-muted-foreground">{topic}</p>
                </div>
                {isActive && (
                    <Badge variant="outline" className="animate-pulse">
                        <span className="mr-2 h-2 w-2 rounded-full bg-green-500" />
                        Live
                    </Badge>
                )}
            </div>

            {/* Round selector */}
            {maxRound > 0 && (
                <div className="flex gap-2 overflow-x-auto pb-2">
                    {Array.from({ length: maxRound }, (_, i) => i + 1).map((round) => (
                        <button
                            key={round}
                            onClick={() => setSelectedRound(round)}
                            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${currentRound === round
                                ? "bg-primary text-primary-foreground"
                                : "bg-muted hover:bg-muted/80"
                                }`}
                        >
                            Round {round}
                        </button>
                    ))}
                </div>
            )}

            {/* Arguments */}
            <ScrollArea className="h-[600px]">
                <div className="space-y-4 pr-4">
                    {debateArguments.length === 0 ? (
                        <Card className="p-8 text-center">
                            <p className="text-muted-foreground">
                                No arguments yet. The debate will begin shortly...
                            </p>
                        </Card>
                    ) : (
                        filterByRound(currentRound).map((argument, idx) => {
                            const Icon = getAgentIcon(argument.agentType);
                            const colorClass = getAgentColor(argument.agentType);

                            return (
                                <Card
                                    key={`${argument.agentId}-${argument.round}-${idx}`}
                                    className={`border-l-4 p-4 transition-all ${argument.stance === "for"
                                        ? "border-l-green-500"
                                        : argument.stance === "against"
                                            ? "border-l-red-500"
                                            : "border-l-gray-500"
                                        }`}
                                >
                                    <div className="flex gap-3">
                                        {/* Agent Avatar */}
                                        <Avatar className={`h-10 w-10 ${colorClass}`}>
                                            <AvatarFallback className={colorClass}>
                                                <Icon className="h-5 w-5" />
                                            </AvatarFallback>
                                        </Avatar>

                                        <div className="flex-1 space-y-2">
                                            {/* Agent Header */}
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-semibold">
                                                        {argument.agentName}
                                                    </span>
                                                    <Badge
                                                        variant="outline"
                                                        className={`text-xs ${colorClass}`}
                                                    >
                                                        {argument.agentType}
                                                    </Badge>
                                                </div>

                                                <div className="flex items-center gap-2">
                                                    {argument.stance !== "neutral" && (
                                                        <Badge
                                                            variant={
                                                                argument.stance === "for"
                                                                    ? "default"
                                                                    : "destructive"
                                                            }
                                                        >
                                                            {argument.stance === "for" ? "For" : "Against"}
                                                        </Badge>
                                                    )}
                                                    <span className="text-xs text-muted-foreground">
                                                        Round {argument.round}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Argument Content */}
                                            <p className="text-sm leading-relaxed">
                                                {argument.content}
                                            </p>

                                            {/* Timestamp */}
                                            <p className="text-xs text-muted-foreground">
                                                {argument.timestamp.toLocaleTimeString()}
                                            </p>
                                        </div>
                                    </div>
                                </Card>
                            );
                        })
                    )}
                </div>
            </ScrollArea>

            {/* Summary Footer */}
            {debateArguments.length > 0 && (
                <Card className="bg-muted/50 p-4">
                    <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                            <p className="text-2xl font-bold">{maxRound}</p>
                            <p className="text-xs text-muted-foreground">Rounds</p>
                        </div>
                        <div>
                            <p className="text-2xl font-bold">{debateArguments.length}</p>
                            <p className="text-xs text-muted-foreground">Arguments</p>
                        </div>
                        <div>
                            <p className="text-2xl font-bold">
                                {new Set(debateArguments.map((a) => a.agentId)).size}
                            </p>
                            <p className="text-xs text-muted-foreground">Agents</p>
                        </div>
                    </div>
                </Card>
            )}
        </div>
    );
}
