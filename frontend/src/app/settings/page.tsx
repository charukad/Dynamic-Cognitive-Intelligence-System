'use client';

/**
 * Settings Page
 * 
 * Allows users to configure:
 * - LLM model selection (OpenAI/Anthropic/Local)
 * - System parameters
 * - Performance tuning
 */

import React, { useState, useEffect } from 'react';
import { Save, AlertCircle, CheckCircle2 } from 'lucide-react';
import { apiClient } from '@/lib/api/client';

interface SystemSettings {
    llm_provider: 'openai' | 'anthropic' | 'local' | 'vllm';
    model_name: string;
    temperature: number;
    max_tokens: number;
    top_p: number;
    frequency_penalty: number;
    presence_penalty: number;
}

interface PerformanceSettings {
    cache_enabled: boolean;
    cache_ttl: number;
    max_concurrent_requests: number;
    request_timeout: number;
}

export default function SettingsPage() {
    const [systemSettings, setSystemSettings] = useState<SystemSettings>({
        llm_provider: 'vllm',
        model_name: 'mistralai/Mistral-7B-Instruct-v0.2',
        temperature: 0.7,
        max_tokens: 2048,
        top_p: 0.9,
        frequency_penalty: 0.0,
        presence_penalty: 0.0,
    });

    const [performanceSettings, setPerformanceSettings] = useState<PerformanceSettings>({
        cache_enabled: true,
        cache_ttl: 3600,
        max_concurrent_requests: 10,
        request_timeout: 30,
    });

    const [saving, setSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const llmProviders = [
        { value: 'vllm', label: 'vLLM (Local)', description: 'High-performance local inference' },
        { value: 'openai', label: 'OpenAI', description: 'GPT-4, GPT-3.5' },
        { value: 'anthropic', label: 'Anthropic', description: 'Claude models' },
        { value: 'local', label: 'Local LLM', description: 'Custom local models' },
    ];

    const modelsByProvider = {
        vllm: [
            'mistralai/Mistral-7B-Instruct-v0.2',
            'meta-llama/Llama-2-7b-chat-hf',
            'meta-llama/Llama-2-13b-chat-hf',
        ],
        openai: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
        anthropic: ['claude-3-opus', 'claude-3-sonnet', 'claude-2.1'],
        local: ['custom-model-1', 'custom-model-2'],
    };

    const handleSystemSettingChange = (key: keyof SystemSettings, value: any) => {
        setSystemSettings(prev => ({ ...prev, [key]: value }));
        setSaveSuccess(false);
    };

    const handlePerformanceSettingChange = (key: keyof PerformanceSettings, value: any) => {
        setPerformanceSettings(prev => ({ ...prev, [key]: value }));
        setSaveSuccess(false);
    };

    const handleSave = async () => {
        setSaving(true);
        setError(null);

        try {
            // Save settings (would actually call API)
            await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API call

            // Store in localStorage for now
            localStorage.setItem('dcis_system_settings', JSON.stringify(systemSettings));
            localStorage.setItem('dcis_performance_settings', JSON.stringify(performanceSettings));

            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 3000);
        } catch (err: any) {
            setError(err.message || 'Failed to save settings');
        } finally {
            setSaving(false);
        }
    };

    // Load settings on mount
    useEffect(() => {
        const loadedSystem = localStorage.getItem('dcis_system_settings');
        const loadedPerf = localStorage.getItem('dcis_performance_settings');

        if (loadedSystem) {
            setSystemSettings(JSON.parse(loadedSystem));
        }
        if (loadedPerf) {
            setPerformanceSettings(JSON.parse(loadedPerf));
        }
    }, []);

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-white mb-2">System Settings</h1>
                    <p className="text-gray-400">Configure LLM providers, models, and system parameters</p>
                </div>

                {/* Save Status */}
                {saveSuccess && (
                    <div className="mb-6 p-4 bg-green-900/30 border border-green-500 rounded-lg flex items-center gap-3">
                        <CheckCircle2 className="text-green-400" size={20} />
                        <span className="text-green-400">Settings saved successfully!</span>
                    </div>
                )}

                {error && (
                    <div className="mb-6 p-4 bg-red-900/30 border border-red-500 rounded-lg flex items-center gap-3">
                        <AlertCircle className="text-red-400" size={20} />
                        <span className="text-red-400">{error}</span>
                    </div>
                )}

                {/* LLM Provider Selection */}
                <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl p-6 mb-6">
                    <h2 className="text-2xl font-bold text-white mb-4">LLM Configuration</h2>

                    <div className="space-y-4">
                        {/* Provider Selection */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                LLM Provider
                            </label>
                            <select
                                value={systemSettings.llm_provider}
                                onChange={(e) => handleSystemSettingChange('llm_provider', e.target.value as any)}
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
                            >
                                {llmProviders.map(provider => (
                                    <option key={provider.value} value={provider.value} className="bg-gray-800">
                                        {provider.label} - {provider.description}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Model Selection */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Model
                            </label>
                            <select
                                value={systemSettings.model_name}
                                onChange={(e) => handleSystemSettingChange('model_name', e.target.value)}
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
                            >
                                {modelsByProvider[systemSettings.llm_provider].map(model => (
                                    <option key={model} value={model} className="bg-gray-800">
                                        {model}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Temperature */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Temperature: {systemSettings.temperature.toFixed(2)}
                            </label>
                            <input
                                type="range"
                                min="0"
                                max="2"
                                step="0.1"
                                value={systemSettings.temperature}
                                onChange={(e) => handleSystemSettingChange('temperature', parseFloat(e.target.value))}
                                className="w-full"
                            />
                            <div className="flex justify-between text-xs text-gray-400 mt-1">
                                <span>Focused</span>
                                <span>Creative</span>
                            </div>
                        </div>

                        {/* Max Tokens */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Max Tokens
                            </label>
                            <input
                                type="number"
                                min="256"
                                max="8192"
                                step="256"
                                value={systemSettings.max_tokens}
                                onChange={(e) => handleSystemSettingChange('max_tokens', parseInt(e.target.value))}
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
                            />
                        </div>

                        {/* Top P */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Top P: {systemSettings.top_p.toFixed(2)}
                            </label>
                            <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.05"
                                value={systemSettings.top_p}
                                onChange={(e) => handleSystemSettingChange('top_p', parseFloat(e.target.value))}
                                className="w-full"
                            />
                        </div>
                    </div>
                </div>

                {/* Performance Settings */}
                <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl p-6 mb-6">
                    <h2 className="text-2xl font-bold text-white mb-4">Performance Tuning</h2>

                    <div className="space-y-4">
                        {/* Cache Enable */}
                        <div className="flex items-center justify-between">
                            <div>
                                <label className="text-sm font-medium text-gray-300">Enable Caching</label>
                                <p className="text-xs text-gray-400">Cache responses for faster retrieval</p>
                            </div>
                            <input
                                type="checkbox"
                                checked={performanceSettings.cache_enabled}
                                onChange={(e) => handlePerformanceSettingChange('cache_enabled', e.target.checked)}
                                className="w-6 h-6"
                            />
                        </div>

                        {/* Cache TTL */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Cache TTL (seconds)
                            </label>
                            <input
                                type="number"
                                min="60"
                                max="86400"
                                step="60"
                                value={performanceSettings.cache_ttl}
                                onChange={(e) => handlePerformanceSettingChange('cache_ttl', parseInt(e.target.value))}
                                disabled={!performanceSettings.cache_enabled}
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500 disabled:opacity-50"
                            />
                        </div>

                        {/* Max Concurrent Requests */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Max Concurrent Requests
                            </label>
                            <input
                                type="number"
                                min="1"
                                max="50"
                                value={performanceSettings.max_concurrent_requests}
                                onChange={(e) => handlePerformanceSettingChange('max_concurrent_requests', parseInt(e.target.value))}
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
                            />
                        </div>

                        {/* Request Timeout */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Request Timeout (seconds)
                            </label>
                            <input
                                type="number"
                                min="5"
                                max="300"
                                value={performanceSettings.request_timeout}
                                onChange={(e) => handlePerformanceSettingChange('request_timeout', parseInt(e.target.value))}
                                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500"
                            />
                        </div>
                    </div>
                </div>

                {/* Save Button */}
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold py-4 rounded-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <Save size={20} />
                    {saving ? 'Saving...' : 'Save Settings'}
                </button>

                {/* Info Footer */}
                <div className="mt-6 p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg">
                    <p className="text-sm text-blue-300">
                        <strong>Note:</strong> Changes to LLM provider and model will take effect immediately for new agent sessions.
                        Performance settings may require a system restart.
                    </p>
                </div>
            </div>
        </div>
    );
}
