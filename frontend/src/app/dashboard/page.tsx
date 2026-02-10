/**
 * DCIS Dashboard - Main Application Page
 * 
 * Integrates all Phase 2 components:
 * - Multi-modal Viewer
 * - Tournament Bracket
 * - Performance Dashboard
 * - Chat Interface
 */

'use client';

import React, { useState, Suspense } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import {
    Home,
    Upload,
    Trophy,
    BarChart3,
    MessageSquare,
    Settings,
    Dna,
    Brain,
    Activity,
    GitBranch,
    Menu,
    X
} from 'lucide-react';

// Import components
import { MultiModalViewer } from '@/components/multimodal/MultiModalViewer';
import { TournamentBracket } from '@/components/gaia/TournamentBracket';
import { PerformanceDashboard } from '@/components/analytics/PerformanceDashboard';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { PlanVisualizer } from '@/components/conductor/PlanVisualizer';
import { MemoryInspector } from '@/components/memory/MemoryInspector';
import { EvolutionDashboard } from '@/components/evolution/EvolutionDashboard';
import { MetacognitionDashboard } from '@/components/intelligence/MetacognitionDashboard';
import { OperationsDashboard } from '@/components/operations/OperationsDashboard';
import { UnifiedAnalyticsDashboard } from '@/components/analytics/UnifiedAnalyticsDashboard';
import './dashboard.css';

// ============================================================================
// Types
// ============================================================================

type Tab = 'overview' | 'multimodal' | 'tournaments' | 'analytics' | 'conductor' | 'memory' | 'evolution' | 'intelligence' | 'operations' | 'unified' | 'chat';

interface NavItem {
    id: Tab;
    label: string;
    icon: React.ReactNode;
}

// ============================================================================
// Dashboard Component
// ============================================================================

// ============================================================================
// Dashboard Component
// ============================================================================

export default function DashboardPage() {
    return (
        <Suspense fallback={<div className="flex h-screen items-center justify-center text-white">Loading DCIS...</div>}>
            <DashboardContent />
        </Suspense>
    );
}

function DashboardContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const pathname = usePathname();

    // Get active tab from URL or default to 'chat'
    const activeTab = (searchParams.get('tab') as Tab) || 'chat';
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    const updateTab = (tab: Tab) => {
        const params = new URLSearchParams(searchParams.toString());
        params.set('tab', tab);
        router.push(`${pathname}?${params.toString()}`);
    };

    const navItems: NavItem[] = [
        { id: 'overview', label: 'Overview', icon: <Home size={20} /> },
        { id: 'multimodal', label: 'Multi-modal', icon: <Upload size={20} /> },
        { id: 'tournaments', label: 'Tournaments', icon: <Trophy size={20} /> },
        { id: 'analytics', label: 'Analytics', icon: <BarChart3 size={20} /> },
        { id: 'conductor', label: 'Conductor', icon: <GitBranch size={20} /> },
        { id: 'memory', label: 'Memory', icon: <Brain size={20} /> },
        { id: 'evolution', label: 'Evolution', icon: <Dna size={20} /> },
        { id: 'intelligence', label: 'Intelligence', icon: <Brain size={20} /> },
        { id: 'operations', label: 'Operations', icon: <Activity size={20} /> },
        { id: 'unified', label: 'Analytics', icon: <BarChart3 size={20} /> },
        { id: 'chat', label: 'Chat', icon: <MessageSquare size={20} /> },
    ];

    return (
        <div className="dashboard-container">
            {/* Sidebar */}
            <aside className={`sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
                <div className="sidebar-header">
                    <h1 className="sidebar-title">DCIS</h1>
                    <button
                        className="sidebar-toggle"
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    >
                        {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
                    </button>
                </div>

                <nav className="sidebar-nav">
                    {navItems.map((item) => (
                        <motion.button
                            key={item.id}
                            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                            onClick={() => updateTab(item.id)}
                            whileHover={{ x: 4 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            <span className="nav-icon">{item.icon}</span>
                            {isSidebarOpen && <span className="nav-label">{item.label}</span>}
                        </motion.button>
                    ))}
                </nav>

                {isSidebarOpen && (
                    <div className="sidebar-footer">
                        <p className="sidebar-version">v1.0.0</p>
                        <p className="sidebar-status">
                            <span className="status-dot online" />
                            All Systems Online
                        </p>
                    </div>
                )}
            </aside>

            {/* Main Content */}
            <main className="main-content">
                <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                    className="content-wrapper"
                >
                    {activeTab === 'overview' && <OverviewPage />}
                    {activeTab === 'multimodal' && <MultiModalViewer />}
                    {activeTab === 'tournaments' && <TournamentBracket tournamentId="latest" />}
                    {activeTab === 'analytics' && <PerformanceDashboard />}
                    {activeTab === 'conductor' && <PlanVisualizer />}
                    {activeTab === 'memory' && <MemoryInspector />}
                    {activeTab === 'evolution' && <EvolutionDashboard />}
                    {activeTab === 'intelligence' && <MetacognitionDashboard />}
                    {activeTab === 'operations' && <OperationsDashboard />}
                    {activeTab === 'unified' && <UnifiedAnalyticsDashboard />}
                    {activeTab === 'chat' && <ChatInterface />}
                </motion.div>
            </main>
        </div>
    );
}

// ============================================================================
// Overview Page
// ============================================================================

function OverviewPage() {
    return (
        <div className="overview-page">
            <div className="overview-header">
                <h1>Dynamic Cognitive Intelligence System</h1>
                <p>Enterprise AI Orchestration Platform</p>
            </div>

            <div className="features-grid">
                <FeatureCard
                    title="4 Specialized Agents"
                    description="Data Analyst, Designer, Translator, Financial Advisor"
                    icon="🤖"
                    gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
                />

                <FeatureCard
                    title="Multi-modal Processing"
                    description="Image & Audio analysis with AI"
                    icon="🖼️"
                    gradient="linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
                />

                <FeatureCard
                    title="Tournament System"
                    description="Agent vs Agent competitive matches"
                    icon="🏆"
                    gradient="linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
                />

                <FeatureCard
                    title="Real-time Analytics"
                    description="3D visualizations & performance metrics"
                    icon="📊"
                    gradient="linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"
                />

                <FeatureCard
                    title="Live Chat"
                    description="Real-time messaging with agents"
                    icon="💬"
                    gradient="linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
                />

                <FeatureCard
                    title="Dream Cycles"
                    description="Self-improving AI through simulation"
                    icon="🌙"
                    gradient="linear-gradient(135deg, #30cfd0 0%, #330867 100%)"
                />
            </div>

            <div className="stats-overview">
                <StatBox label="Total LOC" value="33,000+" />
                <StatBox label="API Endpoints" value="50+" />
                <StatBox label="Agents" value="7" />
                <StatBox label="Components" value="25+" />
            </div>
        </div>
    );
}

// ============================================================================
// Sub-components
// ============================================================================

interface FeatureCardProps {
    title: string;
    description: string;
    icon: string;
    gradient: string;
}

function FeatureCard({ title, description, icon, gradient }: FeatureCardProps) {
    return (
        <motion.div
            className="feature-card"
            whileHover={{ scale: 1.05, y: -4 }}
            transition={{ duration: 0.2 }}
        >
            <div className="feature-icon" style={{ background: gradient }}>
                {icon}
            </div>
            <h3>{title}</h3>
            <p>{description}</p>
        </motion.div>
    );
}

function StatBox({ label, value }: { label: string; value: string }) {
    return (
        <div className="stat-box">
            <div className="stat-value">{value}</div>
            <div className="stat-label">{label}</div>
        </div>
    );
}
