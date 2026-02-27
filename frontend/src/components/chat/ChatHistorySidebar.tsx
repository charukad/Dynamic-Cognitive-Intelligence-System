'use client';

/**
 * ChatGPT-style sidebar showing persisted chat sessions from the chat store.
 */

import React, { useState } from 'react';
import { MessageSquare, Plus, Trash2, ChevronLeft } from 'lucide-react';

import { deleteChatSession } from '@/lib/chatApi';
import { useChatStore } from '@/store/chatStore';

import './ChatHistorySidebar.css';

interface Props {
    onSessionSelect: (sessionId: string) => void;
    onNewChat: () => void;
}

export default function ChatHistorySidebar({ onSessionSelect, onNewChat }: Props) {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const sessions = useChatStore((state) => state.sessions);
    const currentSessionId = useChatStore((state) => state.currentSessionId);
    const isBootstrapping = useChatStore((state) => state.isBootstrapping);
    const removeSession = useChatStore((state) => state.removeSession);

    async function handleDeleteSession(sessionId: string, event: React.MouseEvent) {
        event.stopPropagation();

        if (!window.confirm('Delete this conversation?')) {
            return;
        }

        try {
            await deleteChatSession(sessionId);
            removeSession(sessionId);

            if (sessionId === currentSessionId) {
                onNewChat();
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    }

    function formatDate(dateStr: string) {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        return date.toLocaleDateString();
    }

    if (isCollapsed) {
        return (
            <div className="chat-sidebar collapsed">
                <button
                    type="button"
                    className="expand-btn"
                    onClick={() => setIsCollapsed(false)}
                    title="Show chat history"
                    aria-label="Show chat history"
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
                    type="button"
                    className="collapse-btn"
                    onClick={() => setIsCollapsed(true)}
                    title="Hide sidebar"
                    aria-label="Hide chat history"
                >
                    <ChevronLeft size={18} />
                </button>
            </div>

            <button type="button" className="new-chat-sidebar-btn" onClick={onNewChat}>
                <Plus size={18} />
                New Chat
            </button>

            <div className="sessions-list" role="list" aria-label="Saved conversations">
                {isBootstrapping ? (
                    <div className="loading" role="status" aria-live="polite">Loading chats...</div>
                ) : sessions.length === 0 ? (
                    <div className="empty-state">
                        <MessageSquare size={48} />
                        <p>No chat history yet</p>
                        <p className="hint">Start a new conversation</p>
                    </div>
                ) : (
                    sessions.map((session) => (
                        <div
                            key={session.id}
                            className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
                            role="listitem"
                        >
                            <button
                                type="button"
                                className="session-button"
                                onClick={() => onSessionSelect(session.id)}
                                aria-current={session.id === currentSessionId ? 'page' : undefined}
                                aria-label={`Open conversation ${session.title}`}
                            >
                                <div className="session-content">
                                    <div className="session-title">{session.title}</div>
                                    <div className="session-meta">
                                        {formatDate(session.updated_at)} • {session.message_count} msgs
                                    </div>
                                </div>
                            </button>
                            <button
                                type="button"
                                className="delete-btn"
                                onClick={(event) => {
                                    void handleDeleteSession(session.id, event);
                                }}
                                title="Delete conversation"
                                aria-label={`Delete conversation ${session.title}`}
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
