'use client';

import { useState, useEffect } from 'react';
import { useChatStore } from '@/store/chatStore';
import {
    MessageSquare,
    Plus,
    Settings,
    ChevronLeft,
    Box,
    Zap,
    History
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface SidebarProps {
    className?: string;
}

export function Sidebar({ className }: SidebarProps) {
    const [isOpen, setIsOpen] = useState(true);
    const [recentSessions, setRecentSessions] = useState<string[]>([]);

    // In a real app, this would come from a global store or router
    const activeSessionId = 'current';

    useEffect(() => {
        fetchSessions();
    }, []);

    const fetchSessions = async () => {
        try {
            const response = await fetch('/api/v1/memory/sessions?limit=5');
            const data = await response.json();
            if (data.sessions) {
                setRecentSessions(data.sessions);
            }
        } catch (error) {
            console.error('Failed to fetch sessions:', error);
        }
    };

    const sidebarVariants = {
        open: { width: 280, opacity: 1 },
        closed: { width: 64, opacity: 1 }
    };

    return (
        <motion.div
            initial="open"
            animate={isOpen ? "open" : "closed"}
            variants={sidebarVariants}
            className={`h-full bg-[#050505] border-r border-[#1a1a1a] flex flex-col pt-4 pb-4 transition-all duration-300 ${className}`}
        >
            {/* Logo / Header */}
            <div className={`flex items-center px-4 mb-8 ${isOpen ? 'justify-between' : 'justify-center'}`}>
                {isOpen && (
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white font-bold text-xs">
                            DC
                        </div>
                        <span className="font-semibold text-white tracking-wide">DCIS</span>
                    </div>
                )}

                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="p-2 hover:bg-[#1a1a1a] rounded-lg text-gray-400 transition-colors"
                >
                    {isOpen ? <ChevronLeft size={16} /> : <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 text-white flex items-center justify-center font-bold">D</div>}
                </button>
            </div>

            {/* New Chat Button */}
            <div className="px-3 mb-6">
                <button className={`flex items-center gap-3 w-full bg-[#1a1a1a] hover:bg-[#252525] text-white p-3 rounded-xl transition-all border border-[#333] group ${!isOpen && 'justify-center'}`}>
                    <Plus size={20} className="group-hover:text-cyan-400 transition-colors" />
                    {isOpen && <span className="font-medium">New Project</span>}
                </button>
            </div>

            {/* Navigation Sections */}
            <div className="flex-1 overflow-y-auto px-3 space-y-6">
                {/* Recents */}
                <div>
                    {isOpen && <h3 className="text-xs font-mono text-gray-500 mb-3 px-2 uppercase tracking-wider">Recents</h3>}
                    <div className="space-y-1">
                        {recentSessions.length > 0 ? (
                            recentSessions.map((session) => (
                                <button
                                    key={session}
                                    className="flex items-center gap-3 w-full p-2 hover:bg-[#111] rounded-lg text-gray-400 hover:text-white transition-colors text-left group"
                                >
                                    <MessageSquare size={16} className="text-gray-600 group-hover:text-cyan-400" />
                                    {isOpen && (
                                        <div className="truncate text-sm">
                                            {session.substring(0, 8)}...
                                        </div>
                                    )}
                                </button>
                            ))
                        ) : (
                            isOpen && <div className="px-2 text-sm text-gray-600 italic">No history found</div>
                        )}
                    </div>
                </div>

                {/* Modules */}
                <div>
                    {isOpen && <h3 className="text-xs font-mono text-gray-500 mb-3 px-2 uppercase tracking-wider">Modules</h3>}
                    <div className="space-y-1">
                        <NavItem icon={<Box size={16} />} label="Agents" isOpen={isOpen} />
                        <NavItem icon={<Zap size={16} />} label="Workflows" isOpen={isOpen} />
                        <NavItem icon={<History size={16} />} label="Memory" isOpen={isOpen} />
                    </div>
                </div>
            </div>

            {/* Footer / Settings */}
            <div className="px-3 mt-auto">
                <button className="flex items-center gap-3 w-full p-2 hover:bg-[#111] rounded-lg text-gray-400 transition-colors">
                    <Settings size={18} />
                    {isOpen && <span className="text-sm">Settings</span>}
                </button>
            </div>
        </motion.div>
    );
}

function NavItem({ icon, label, isOpen }: { icon: any, label: string, isOpen: boolean }) {
    return (
        <button className="flex items-center gap-3 w-full p-2 hover:bg-[#111] rounded-lg text-gray-400 hover:text-white transition-colors group">
            <span className="text-gray-600 group-hover:text-cyan-400 transition-colors">{icon}</span>
            {isOpen && <span className="text-sm">{label}</span>}
        </button>
    );
}
