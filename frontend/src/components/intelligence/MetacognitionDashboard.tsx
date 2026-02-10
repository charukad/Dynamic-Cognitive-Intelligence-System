/**
 * Metacognition Dashboard - Advanced Intelligence Visualization
 * 
 * Showcases:
 * - Mirror Protocol self-reflection
 * - Neurosymbolic reasoning proof trees
 * - Temporal knowledge timelines
 * - Confidence calibration metrics
 */

'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Brain,
    Lightbulb,
    GitMerge,
    Clock,
    TrendingUp,
    AlertTriangle,
    CheckCircle2,
    XCircle,
    Timer
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

// ============================================================================
// Types
// ============================================================================

interface SelfCritique {
    id: string;
    critique_type: string;
    identified_issues: string[];
    suggested_improvements: string[];
    confidence_adjustment: number;
    timestamp: string;
}

interface NeurosymbolicStats {
    total_rules: number;
    total_patterns: number;
    total_facts: number;
    avg_rule_confidence: number;
    avg_pattern_confidence: number;
}

interface TemporalStats {
    total_facts: number;
    total_events: number;
    ongoing_facts: number;
    ongoing_events: number;
    avg_fact_confidence: number;
}

// ============================================================================
// Main Component
// ============================================================================

export function MetacognitionDashboard() {
    const [activeTab, setActiveTab] = useState<'mirror' | 'neuro' | 'temporal'>('mirror');

    // Mirror Protocol state
    const [reasoning, setReasoning] = useState('');
    const [conclusion, setConclusion] = useState('');
    const [confidence, setConfidence] = useState(0.7);
    const [critique, setCritique] = useState<SelfCritique | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    // Neurosymbolic state
    const [neuroStats, setNeuroStats] = useState<NeurosymbolicStats | null>(null);
    const [query, setQuery] = useState('');
    const [facts, setFacts] = useState('');
    const [proofResult, setProofResult] = useState<any>(null);

    // Temporal state
    const [temporalStats, setTemporalStats] = useState<TemporalStats | null>(null);
    const [timeline, setTimeline] = useState<any[]>([]);

    // Fetch stats
    useEffect(() => {
        fetchStats();
        const interval = setInterval(fetchStats, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchStats = async () => {
        try {
            const [neuroRes, tempRes] = await Promise.all([
                apiClient.get('/v1/intelligence/neurosymbolic/stats'),
                apiClient.get('/v1/intelligence/temporal/stats'),
            ]);

            setNeuroStats(neuroRes.data || neuroRes);
            setTemporalStats(tempRes.data || tempRes);
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        }
    };

    const handleAnalyzeReasoning = async () => {
        if (!reasoning || !conclusion) return;

        setIsAnalyzing(true);
        try {
            const res = await apiClient.post('/v1/intelligence/mirror/analyze', {
                task_description: "User reasoning task",
                steps: [{ step_name: "reasoning", reasoning: reasoning }],
                final_conclusion: conclusion,
                confidence: confidence,
            });

            setCritique((res.data || res).critique);
        } catch (error) {
            console.error('Analysis failed:', error);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleProveGoal = async () => {
        if (!query) return;

        try {
            const factList = facts.split('\n').filter(f => f.trim());
            const res = await apiClient.post('/v1/intelligence/neurosymbolic/backward-chain', {
                goal: query,
                facts: factList,
                max_depth: 5,
            });

            setProofResult(res.data || res);
        } catch (error) {
            console.error('Proof failed:', error);
        }
    };

    return (
        <div className="h-full w-full bg-black/50 rounded-lg overflow-hidden flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-800 bg-black/30 backdrop-blur-sm">
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <Brain className="h-5 w-5 text-purple-400" />
                    Metacognition & Advanced Intelligence
                </h2>

                {/* Tabs */}
                <div className="flex gap-2">
                    <TabButton
                        active={activeTab === 'mirror'}
                        onClick={() => setActiveTab('mirror')}
                        icon={<Lightbulb className="h-4 w-4" />}
                        label="Mirror Protocol"
                    />
                    <TabButton
                        active={activeTab === 'neuro'}
                        onClick={() => setActiveTab('neuro')}
                        icon={<GitMerge className="h-4 w-4" />}
                        label="Neurosymbolic"
                    />
                    <TabButton
                        active={activeTab === 'temporal'}
                        onClick={() => setActiveTab('temporal')}
                        icon={<Clock className="h-4 w-4" />}
                        label="Temporal KG"
                    />
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
                <AnimatePresence mode="wait">
                    {activeTab === 'mirror' && (
                        <motion.div
                            key="mirror"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            className="space-y-4"
                        >
                            <div className="bg-gray-900/50 rounded-lg p-4">
                                <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                                    <Brain className="h-4 w-4 text-purple-400" />
                                    Self-Reflection Analysis
                                </h3>

                                <div className="space-y-3">
                                    <div>
                                        <label className="text-sm text-gray-400 mb-1 block">Reasoning Steps</label>
                                        <Textarea
                                            value={reasoning}
                                            onChange={(e) => setReasoning(e.target.value)}
                                            placeholder="Describe your reasoning process..."
                                            className="min-h-[100px]"
                                        />
                                    </div>

                                    <div>
                                        <label className="text-sm text-gray-400 mb-1 block">Conclusion</label>
                                        <Textarea
                                            value={conclusion}
                                            onChange={(e) => setConclusion(e.target.value)}
                                            placeholder="What did you conclude?"
                                            rows={2}
                                        />
                                    </div>

                                    <div>
                                        <label className="text-sm text-gray-400 mb-1 block">
                                            Confidence: {(confidence * 100).toFixed(0)}%
                                        </label>
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={confidence * 100}
                                            onChange={(e) => setConfidence(Number(e.target.value) / 100)}
                                            className="w-full"
                                        />
                                    </div>

                                    <Button
                                        onClick={handleAnalyzeReasoning}
                                        disabled={isAnalyzing}
                                        className="w-full"
                                    >
                                        {isAnalyzing ? 'Analyzing...' : 'Analyze Reasoning'}
                                    </Button>
                                </div>
                            </div>

                            {/* Critique Results */}
                            {critique && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="bg-gray-900/50 rounded-lg p-4 border border-purple-500/30"
                                >
                                    <h4 className="text-white font-semibold mb-3">Self-Critique</h4>

                                    <div className="space-y-3">
                                        {/* Issues */}
                                        {critique.identified_issues.length > 0 && (
                                            <div>
                                                <div className="text-sm text-red-400 mb-2 flex items-center gap-2">
                                                    <AlertTriangle className="h-4 w-4" />
                                                    Identified Issues
                                                </div>
                                                <ul className="space-y-1">
                                                    {critique.identified_issues.map((issue, i) => (
                                                        <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                                                            <XCircle className="h-3 w-3 text-red-400 mt-0.5 flex-shrink-0" />
                                                            {issue}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {/* Improvements */}
                                        {critique.suggested_improvements.length > 0 && (
                                            <div>
                                                <div className="text-sm text-green-400 mb-2 flex items-center gap-2">
                                                    <Lightbulb className="h-4 w-4" />
                                                    Suggestions
                                                </div>
                                                <ul className="space-y-1">
                                                    {critique.suggested_improvements.map((improvement, i) => (
                                                        <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                                                            <CheckCircle2 className="h-3 w-3 text-green-400 mt-0.5 flex-shrink-0" />
                                                            {improvement}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {/* Confidence Adjustment */}
                                        <div className="pt-2 border-t border-gray-700">
                                            <div className="text-sm text-gray-400">Confidence Adjustment:</div>
                                            <div className={`text-2xl font-bold ${critique.confidence_adjustment > 0 ? 'text-green-400' :
                                                critique.confidence_adjustment < 0 ? 'text-red-400' :
                                                    'text-gray-400'
                                                }`}>
                                                {critique.confidence_adjustment > 0 ? '+' : ''}
                                                {(critique.confidence_adjustment * 100).toFixed(1)}%
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </motion.div>
                    )}

                    {activeTab === 'neuro' && (
                        <motion.div
                            key="neuro"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            className="space-y-4"
                        >
                            {/* Stats */}
                            {neuroStats && (
                                <div className="grid grid-cols-3 gap-3">
                                    <StatCard label="Rules" value={neuroStats.total_rules} color="text-blue-400" />
                                    <StatCard label="Patterns" value={neuroStats.total_patterns} color="text-purple-400" />
                                    <StatCard label="Facts" value={neuroStats.total_facts} color="text-green-400" />
                                </div>
                            )}

                            {/* Proof Interface */}
                            <div className="bg-gray-900/50 rounded-lg p-4">
                                <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                                    <GitMerge className="h-4 w-4 text-blue-400" />
                                    Logical Proof Engine
                                </h3>

                                <div className="space-y-3">
                                    <div>
                                        <label className="text-sm text-gray-400 mb-1 block">Goal to Prove</label>
                                        <input
                                            type="text"
                                            value={query}
                                            onChange={(e) => setQuery(e.target.value)}
                                            placeholder="e.g., Q"
                                            className="w-full bg-black/30 border border-gray-700 rounded px-3 py-2 text-white"
                                        />
                                    </div>

                                    <div>
                                        <label className="text-sm text-gray-400 mb-1 block">Known Facts (one per line)</label>
                                        <Textarea
                                            value={facts}
                                            onChange={(e) => setFacts(e.target.value)}
                                            placeholder="P\nP implies Q"
                                            rows={4}
                                        />
                                    </div>

                                    <Button onClick={handleProveGoal} className="w-full">
                                        Prove Goal
                                    </Button>
                                </div>
                            </div>

                            {/* Proof Result */}
                            {proofResult && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`bg-gray-900/50 rounded-lg p-4 border ${proofResult.proved ? 'border-green-500/30' : 'border-red-500/30'
                                        }`}
                                >
                                    <div className="flex items-center gap-2 mb-3">
                                        {proofResult.proved ? (
                                            <CheckCircle2 className="h-5 w-5 text-green-400" />
                                        ) : (
                                            <XCircle className="h-5 w-5 text-red-400" />
                                        )}
                                        <span className="text-white font-semibold">
                                            {proofResult.proved ? 'Proof Successful' : 'Proof Failed'}
                                        </span>
                                    </div>

                                    <div className="space-y-1 font-mono text-xs">
                                        {proofResult.proof_steps?.map((step: string, i: number) => (
                                            <div key={i} className="text-gray-300">{step}</div>
                                        ))}
                                    </div>
                                </motion.div>
                            )}
                        </motion.div>
                    )}

                    {activeTab === 'temporal' && (
                        <motion.div
                            key="temporal"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            className="space-y-4"
                        >
                            {/* Stats */}
                            {temporalStats && (
                                <div className="grid grid-cols-3 gap-3">
                                    <StatCard label="Total Facts" value={temporalStats.total_facts} color="text-cyan-400" />
                                    <StatCard label="Events" value={temporalStats.total_events} color="text-blue-400" />
                                    <StatCard label="Ongoing" value={temporalStats.ongoing_facts} color="text-green-400" />
                                </div>
                            )}

                            <div className="bg-gray-900/50 rounded-lg p-4">
                                <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                                    <Clock className="h-4 w-4 text-cyan-400" />
                                    Time-Aware Knowledge
                                </h3>
                                <p className="text-sm text-gray-400">
                                    Temporal knowledge graph tracks facts and events with validity periods,
                                    enabling historical state reconstruction and temporal reasoning.
                                </p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}

// ============================================================================
// Helper Components
// ============================================================================

function TabButton({ active, onClick, icon, label }: any) {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${active
                ? 'bg-purple-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
        >
            {icon}
            <span>{label}</span>
        </button>
    );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
    return (
        <div className="bg-gray-900/50 rounded px-3 py-2">
            <div className="text-xs text-gray-400 mb-1">{label}</div>
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
        </div>
    );
}
