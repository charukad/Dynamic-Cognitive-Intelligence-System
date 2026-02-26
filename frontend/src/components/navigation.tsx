'use client';

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { ChatInterface } from "@/components/chat/ChatInterface";
import {
    LayoutDashboard,
    Layers,
    Trophy,
    BarChart2,
    Activity,
    Music2,
    Brain,
    Dna,
    Sparkles,
    Bot,
    Settings2,
    MessageSquare,
    BrainCircuitIcon,
} from "lucide-react";

const navItems = [
    { name: "Overview", href: "/", icon: LayoutDashboard },
    { name: "Multi-modal", href: "/multimodal", icon: Layers },
    { name: "Tournaments", href: "/tournaments", icon: Trophy },
    { name: "Analytics", href: "/analytics", icon: BarChart2 },
    { name: "Conductor", href: "/conductor", icon: Music2 },
    { name: "Memory", href: "/memory", icon: Brain },
    { name: "Evolution", href: "/evolution", icon: Dna },
    { name: "Intelligence", href: "/intelligence", icon: Sparkles },
    { name: "Operations", href: "/operations", icon: Activity },
    { name: "Agents", href: "/agents", icon: Bot },
    { name: "Settings", href: "/settings", icon: Settings2 },
];

const CHAT_PANEL_WIDTH_KEY = "dcis.chat.panel.width";
const MIN_CHAT_PANEL_WIDTH = 360;
const MAX_CHAT_PANEL_WIDTH = 760;

export function Navigation() {
    const pathname = usePathname();
    const [chatOpen, setChatOpen] = useState(false);
    const [chatPanelWidth, setChatPanelWidth] = useState(420);
    const [isResizingChat, setIsResizingChat] = useState(false);
    const chatPanelWidthRef = useRef(chatPanelWidth);

    useEffect(() => {
        chatPanelWidthRef.current = chatPanelWidth;
    }, [chatPanelWidth]);

    useEffect(() => {
        const savedWidth = window.localStorage.getItem(CHAT_PANEL_WIDTH_KEY);
        if (!savedWidth) return;

        const parsedWidth = Number(savedWidth);
        if (!Number.isFinite(parsedWidth)) return;

        const viewportMax = Math.max(280, window.innerWidth - 24);
        const nextWidth = Math.min(parsedWidth, viewportMax);
        if (nextWidth === chatPanelWidthRef.current) return;

        window.requestAnimationFrame(() => {
            setChatPanelWidth(nextWidth);
        });
    }, []);

    useEffect(() => {
        if (!isResizingChat) return;

        const handlePointerMove = (event: PointerEvent) => {
            const viewportWidth = window.innerWidth;
            const minWidth = Math.max(280, Math.min(MIN_CHAT_PANEL_WIDTH, viewportWidth - 24));
            const maxWidth = Math.max(minWidth, Math.min(MAX_CHAT_PANEL_WIDTH, viewportWidth - 24));
            const nextWidth = viewportWidth - event.clientX;
            const clampedWidth = Math.min(maxWidth, Math.max(minWidth, nextWidth));
            setChatPanelWidth(clampedWidth);
        };

        const handlePointerUp = () => {
            setIsResizingChat(false);
            window.localStorage.setItem(CHAT_PANEL_WIDTH_KEY, String(Math.round(chatPanelWidthRef.current)));
        };

        window.addEventListener("pointermove", handlePointerMove);
        window.addEventListener("pointerup", handlePointerUp);
        document.body.style.cursor = "col-resize";
        document.body.style.userSelect = "none";

        return () => {
            window.removeEventListener("pointermove", handlePointerMove);
            window.removeEventListener("pointerup", handlePointerUp);
            document.body.style.cursor = "";
            document.body.style.userSelect = "";
        };
    }, [isResizingChat]);

    const handleResizeStart = (event: ReactPointerEvent<HTMLDivElement>) => {
        if (event.button !== 0) return;
        event.preventDefault();
        setIsResizingChat(true);
    };

    return (
        <>
            {/* Top Navigation Bar */}
            <nav className="fixed top-0 left-0 right-0 z-50 h-14 border-b border-white/10 bg-black/80 backdrop-blur-md">
                <div className="flex h-full items-center px-4 gap-1">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2 mr-6 shrink-0">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600">
                            <BrainCircuitIcon className="h-4 w-4 text-white" />
                        </div>
                        <span className="text-sm font-bold text-white tracking-wider hidden sm:block">DCIS</span>
                    </Link>

                    {/* Nav Links */}
                    <div className="flex items-center gap-0.5 flex-1 overflow-x-auto scrollbar-none">
                        {navItems.map((item) => {
                            const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
                            const Icon = item.icon;
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={cn(
                                        "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all whitespace-nowrap",
                                        isActive
                                            ? "bg-cyan-500/15 text-cyan-400 border border-cyan-500/30"
                                            : "text-gray-400 hover:text-white hover:bg-white/5"
                                    )}
                                >
                                    <Icon className="h-3.5 w-3.5 shrink-0" />
                                    <span>{item.name}</span>
                                </Link>
                            );
                        })}
                    </div>

                    {/* Right side — status + Chat trigger */}
                    <div className="flex items-center gap-3 ml-4 shrink-0">
                        {/* Online indicator */}
                        <div className="relative hidden md:block">
                            <div className="h-2 w-2 rounded-full bg-green-500" />
                            <div className="absolute inset-0 h-2 w-2 animate-ping rounded-full bg-green-400 opacity-75" />
                        </div>

                        {/* Chat toggle */}
                        <button
                            onClick={() => setChatOpen(!chatOpen)}
                            className={cn(
                                "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all border",
                                chatOpen
                                    ? "bg-cyan-500/20 text-cyan-400 border-cyan-500/40"
                                    : "text-gray-400 border-white/10 hover:text-white hover:bg-white/5 hover:border-white/20"
                            )}
                        >
                            <MessageSquare className="h-3.5 w-3.5" />
                            <span>Chat</span>
                        </button>
                    </div>
                </div>
            </nav>

            {/* Chat Side Panel */}
            <div
                className={cn(
                    "fixed top-14 right-0 z-40 h-[calc(100vh-3.5rem)] flex flex-col border-l border-white/10 bg-black/95 backdrop-blur-md transition-transform duration-300",
                    chatOpen ? "translate-x-0" : "translate-x-full"
                )}
                style={{ width: `${chatPanelWidth}px`, maxWidth: "100vw" }}
            >
                <div
                    role="separator"
                    aria-orientation="vertical"
                    aria-label="Resize chat panel"
                    className={cn(
                        "absolute inset-y-0 left-0 w-2 -translate-x-1 cursor-col-resize touch-none transition-colors",
                        isResizingChat ? "bg-cyan-400/30" : "bg-transparent hover:bg-cyan-400/20"
                    )}
                    onPointerDown={handleResizeStart}
                />

                <div className="h-full overflow-hidden">
                    <ChatInterface embedded />
                </div>
            </div>

            {/* Overlay when chat is open (mobile) */}
            {chatOpen && (
                <div
                    className="fixed inset-0 z-30 bg-black/40 md:hidden"
                    onClick={() => setChatOpen(false)}
                />
            )}
        </>
    );
}
