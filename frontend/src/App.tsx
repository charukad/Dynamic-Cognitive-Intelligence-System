/**
 * Enhanced Main App with Keyboard Shortcuts
 */

import { useState, useEffect } from 'react';
import { OrbitScene } from './components/orbit/OrbitScene';
import { CortexScene } from './components/cortex/CortexScene';
import { WebSocketProvider } from './lib/websocket/client';
import './App.css';

type SceneType = 'orbit' | 'cortex';

function SceneNavigation({
    currentScene,
    onSceneChange,
}: {
    currentScene: SceneType;
    onSceneChange: (scene: SceneType) => void;
}) {
    return (
        <nav
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                height: 60,
                background: 'rgba(0, 0, 0, 0.95)',
                backdropFilter: 'blur(10px)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0 30px',
                zIndex: 100,
            }}
        >
            <div
                style={{
                    fontSize: 24,
                    fontWeight: 700,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    fontFamily: 'system-ui',
                }}
            >
                DCIS
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
                {(['orbit', 'cortex'] as const).map((scene) => (
                    <button
                        key={scene}
                        onClick={() => onSceneChange(scene)}
                        style={{
                            padding: '10px 20px',
                            background: currentScene === scene
                                ? (scene === 'orbit' ? '#667eea' : '#764ba2')
                                : 'transparent',
                            color: 'white',
                            border: currentScene === scene ? 'none' : '1px solid rgba(255, 255, 255, 0.2)',
                            borderRadius: 8,
                            cursor: 'pointer',
                            fontSize: 14,
                            fontWeight: 500,
                            transition: 'all 0.2s ease',
                            fontFamily: 'system-ui',
                        }}
                    >
                        {scene === 'orbit' ? '🌐 Orbit' : '🧠 Cortex'}
                    </button>
                ))}
            </div>

            <div style={{ fontSize: 12, color: '#aaa', fontFamily: 'monospace' }}>
                v1.0.0
            </div>
        </nav>
    );
}

function App() {
    const [currentScene, setCurrentScene] = useState<SceneType>('orbit');

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyPress = (e: KeyboardEvent) => {
            if (e.key === '1') setCurrentScene('orbit');
            if (e.key === '2') setCurrentScene('cortex');
        };

        window.addEventListener('keydown', handleKeyPress);
        return () => window.removeEventListener('keydown', handleKeyPress);
    }, []);

    return (
        <WebSocketProvider>
            <div className="app">
                <SceneNavigation currentScene={currentScene} onSceneChange={setCurrentScene} />

                <div style={{ paddingTop: 60, height: '100vh' }} className="scene-transition">
                    {currentScene === 'orbit' ? <OrbitScene /> : <CortexScene />}
                </div>

                <div
                    style={{
                        position: 'fixed',
                        bottom: 70,
                        left: 20,
                        background: 'rgba(0, 0, 0, 0.8)',
                        color: 'white',
                        padding: '12px 16px',
                        borderRadius: 8,
                        fontSize: 13,
                        maxWidth: 300,
                        fontFamily: 'system-ui',
                        lineHeight: 1.6,
                    }}
                >
                    {currentScene === 'orbit' ? (
                        <>
                            <div style={{ fontWeight: 600, marginBottom: 6 }}>🌐 Orbit View</div>
                            <div style={{ fontSize: 12, color: '#ccc' }}>
                                Visualizing agent swarm in 3D space. Watch agents collaborate in real-time.
                            </div>
                        </>
                    ) : (
                        <>
                            <div style={{ fontWeight: 600, marginBottom: 6 }}>🧠 Cortex View</div>
                            <div style={{ fontSize: 12, color: '#ccc' }}>
                                Explore the knowledge graph. Click nodes to see connections.
                            </div>
                        </>
                    )}
                </div>

                <div
                    style={{
                        position: 'fixed',
                        bottom: 20,
                        left: 20,
                        background: 'rgba(0, 0, 0, 0.6)',
                        color: '#888',
                        padding: '6px 10px',
                        borderRadius: 6,
                        fontSize: 11,
                        fontFamily: 'monospace',
                    }}
                >
                    Press <kbd>1</kbd> or <kbd>2</kbd> to switch scenes
                </div>
            </div>
        </WebSocketProvider>
    );
}

export default App;
