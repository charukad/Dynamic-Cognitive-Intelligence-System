/**
 * Chat History Sidebar
 * 
 * ChatGPT-Style sidebar showing list of previous chat sessions
 */

import React, { useState, useEffect } from 'react';
import { MessageSquare, Plus, Trash2, ChevronLeft } from 'lucide-react';
import './ChatHistorySidebar.css';

interface ChatSession {
    session_id: string;
    title: string;
    created_at: string;
    updated_at: string;
    message_count: number;
    last_message: string;
}

interface Props {
    currentSessionId: string | null;
    onSessionSelect: (sessionId: string) => void;
    onNewChat: () => void;
}

export default function ChatHistorySidebar({ currentSessionId, onSessionSelect, onNewChat }: Props) {
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadSessions();
    }, []);

    const loadSessions = async () => {
        try {
            const response = await fetch('http://localhost:8008/api/v1/chat/sessions');
            if (response.ok) {
                const data = await response.json();
                setSessions(data.sessions);
                console.log(`📚 Loaded ${data.count} chat sessions`);
            }
        } catch (error) {
            console.error('Failed to load sessions:', error);
        } finally {
            setLoading(false);
        }
    };

    const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
        e.stopPropagation();

        if (!window.confirm('Delete this conversation?')) return;

        try {
            const response = await fetch(`http://localhost:8008/api/v1/chat/history/${sessionId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                setSessions(prev => prev.filter(s => s.session_id !== sessionId));
                console.log(`🗑️ Deleted session: ${sessionId}`);

                // If deleted current session, create new one
                if (sessionId === currentSessionId) {
                    onNewChat();
                }
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        return date.toLocaleDateString();
    };

    if (isCollapsed) {
        return (
            <div className="chat-sidebar collapsed">
                <button
                    className="expand-btn"
                    onClick={() => setIsCollapsed(false)}
                    title="Show chat history"
                >
                    <MessageSquare size={20} />
                </button>
            </div>
        );
    }

    return (
        <div className="chat-sidebar">
            <div className="sidebar-header">
                <h3>
                    <MessageSquare size={18} />
                    Chat History
                </h3>
                <button
                    className="collapse-btn"
                    onClick={() => setIsCollapsed(true)}
                    title="Hide sidebar"
                >
                    <ChevronLeft size={18} />
                </button>
            </div>

            <button className="new-chat-sidebar-btn" onClick={onNewChat}>
                <Plus size={18} />
                New Chat
            </button>

            <div className="sessions-list">
                {loading ? (
                    <div className="loading">Loading chats...</div>
                ) : sessions.length === 0 ? (
                    <div className="empty-state">
                        <MessageSquare size={48} />
                        <p>No chat history yet</p>
                        <p className="hint">Start a new conversation</p>
                    </div>
                ) : (
                    sessions.map(session => (
                        <div
                            key={session.session_id}
                            className={`session-item ${session.session_id === currentSessionId ? 'active' : ''}`}
                            onClick={() => onSessionSelect(session.session_id)}
                        >
                            <div className="session-content">
                                <div className="session-title">{session.title}</div>
                                <div className="session-meta">
                                    {formatDate(session.updated_at)} • {session.message_count} msgs
                                </div>
                            </div>
                            <button
                                className="delete-btn"
                                onClick={(e) => deleteSession(session.session_id, e)}
                                title="Delete conversation"
                            >
                                <Trash2 size={16} />
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
