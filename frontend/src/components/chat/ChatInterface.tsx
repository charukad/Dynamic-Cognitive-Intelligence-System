'use client';

/**
 * Real-time Chat Interface
 * 
 * Advanced features:
 * - WebSocket real-time messaging
 * - Typing indicators (animated dots)
 * - Message bubbles with animations
 * - Agent selector
 * - Markdown rendering
 * - Code syntax highlighting
 * - Chat history persistence
 * - Auto-scroll to latest
 * - Message timestamps
 */

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { saveMessageToHistory } from '@/lib/chatHistory';
import ChatHistorySidebar from './ChatHistorySidebar';
import { apiPath, wsUrl } from '@/lib/runtime';
import {
    Send,
    Bot,
    Check,
    CheckCheck,
    Clock,
    Sparkles,
    ThumbsUp,
    ThumbsDown,
    PlusCircle
} from 'lucide-react';
import './ChatInterface.css';

// ============================================================================
// Types
// ============================================================================

interface Message {
    id: string;
    sender: 'user' | 'agent';
    agent_id?: string;
    agent_name?: string;
    content: string;
    timestamp: Date;
    status: 'sending' | 'sent' | 'delivered' | 'error';
    isStreaming?: boolean;
    feedback?: 'thumbs_up' | 'thumbs_down' | null;
}

interface Agent {
    id: string;
    name: string;
    specialty: string;
    status: 'online' | 'busy' | 'offline';
    avatar_color: string;
}

interface RawChatMessage {
    id: string;
    sender: 'user' | 'agent';
    agent_id?: string;
    agent_name?: string;
    content: string;
    timestamp: string;
}

interface RawAgent {
    id: string;
    name: string;
    description: string;
}

// ============================================================================
// Chat Interface Component
// ============================================================================

export function ChatInterface({ embedded = false }: { embedded?: boolean }) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputText, setInputText] = useState('');
    const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [availableAgents, setAvailableAgents] = useState<Agent[]>([]);
    const [isTyping, setIsTyping] = useState(false);
    const [ws, setWs] = useState<WebSocket | null>(null);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Initialize WebSocket and load data
    useEffect(() => {
        fetchAgents();
        loadChatHistory();
        const websocket = initializeWebSocket();

        return () => {
            websocket?.close();
        };
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const loadChatHistory = async () => {
        try {
            // Get or create session ID
            let sessionId = localStorage.getItem('chat_session_id');
            if (!sessionId) {
                sessionId = generateId();
                localStorage.setItem('chat_session_id', sessionId);
            }

            setCurrentSessionId(sessionId);

            // Fetch chat history from API
            const response = await fetch(apiPath(`/v1/chat/history/${sessionId}`));

            if (response.ok) {
                const data = await response.json();

                if (Array.isArray(data.messages) && data.messages.length > 0) {
                    // Convert to Message format
                    const loadedMessages: Message[] = (data.messages as RawChatMessage[]).map((msg) => ({
                        id: msg.id,
                        sender: msg.sender,  // 'user' or 'agent'
                        agent_id: msg.agent_id,
                        agent_name: msg.agent_name,
                        content: msg.content,
                        timestamp: new Date(msg.timestamp),
                        status: 'delivered' as const
                    }));

                    setMessages(loadedMessages);
                }
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    };

    const initializeWebSocket = (): WebSocket => {
        const websocket = new WebSocket(wsUrl('/ws/ai-services'));

        websocket.onopen = () => {
            console.log('WebSocket connected');
        };

        websocket.onmessage = (event) => {
            const payload = JSON.parse(event.data) as {
                type?: string;
                id?: string;
                agent_id?: string;
                agent_name?: string;
                content?: string;
                timestamp?: string;
                message_id?: string;
                chunk?: string;
                is_typing?: boolean;
                data?: {
                    is_typing?: boolean;
                    message?: string;
                };
            };
            const data = payload.data ?? {};

            if (payload.type === 'message') {
                addMessage({
                    id: payload.id || generateId(),
                    sender: 'agent',
                    agent_id: payload.agent_id,
                    agent_name: payload.agent_name,
                    content: payload.content || '',
                    timestamp: new Date(payload.timestamp || Date.now()),
                    status: 'delivered'
                });
                setIsTyping(false);
            } else if (payload.type === 'typing') {
                setIsTyping(Boolean(data.is_typing ?? payload.is_typing));
            } else if (payload.type === 'stream_chunk' && payload.message_id && payload.chunk) {
                updateStreamingMessage(payload.message_id, payload.chunk);
            } else if (payload.type === 'error') {
                console.error('WebSocket chat error:', data.message || 'Unknown WebSocket error');
                setIsTyping(false);
            }
        };

        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        setWs(websocket);
        return websocket;
    };

    const fetchAgents = async () => {
        try {
            const response = await fetch(apiPath('/v1/agents'));
            const data = await response.json();

            // Map agents - API returns {id, name, description, capabilities}
            const agents: Agent[] = Array.isArray(data) ? (data as RawAgent[]).map((a) => ({
                id: a.id,
                name: a.name,
                specialty: a.description,
                status: 'online' as const,
                avatar_color: getAgentColor(a.id)
            })) : [];

            setAvailableAgents(agents);
            if (agents.length > 0) {
                setSelectedAgent(agents[0]);
            }
        } catch (error) {
            console.error('Failed to fetch agents:', error);
        }
    };

    const addMessage = (message: Message) => {
        setMessages(prev => [...prev, message]);
        scrollToBottom();
    };

    const updateStreamingMessage = (messageId: string, chunk: string) => {
        setMessages(prev =>
            prev.map(msg =>
                msg.id === messageId
                    ? { ...msg, content: msg.content + chunk }
                    : msg
            )
        );
        scrollToBottom();
    };

    const sendMessage = async () => {
        const messageText = inputText.trim();
        if (!messageText) return;

        const userMessage: Message = {
            id: generateId(),
            sender: 'user',
            content: messageText,
            timestamp: new Date(),
            status: 'sending'
        };

        addMessage(userMessage);
        setInputText('');

        let sessionId = localStorage.getItem('chat_session_id');
        if (!sessionId) {
            sessionId = generateId();
            localStorage.setItem('chat_session_id', sessionId);
            setCurrentSessionId(sessionId);
        }
        const activeSessionId = sessionId;

        const shouldUseWebSocket =
            Boolean(ws && ws.readyState === WebSocket.OPEN) &&
            Boolean(selectedAgent?.id) &&
            isUuidLike(selectedAgent?.id || '');

        // Try WebSocket first
        if (shouldUseWebSocket && ws && selectedAgent) {
            ws.send(JSON.stringify({
                type: 'chat',
                data: {
                    agent_id: selectedAgent.id,
                    message: messageText,
                    message_id: userMessage.id,
                    session_id: activeSessionId
                }
            }));

            // Update status to sent
            setTimeout(() => {
                setMessages(prev =>
                    prev.map(msg =>
                        msg.id === userMessage.id
                            ? { ...msg, status: 'sent' }
                            : msg
                    )
                );
            }, 500);
        } else {
            // WebSocket not available - use HTTP API fallback
            console.warn('WebSocket unavailable for current chat context, using HTTP API fallback');

            try {
                const response = await fetch(apiPath('/v1/chat/completions'), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        messages: messages.map(m => ({ role: m.sender === 'user' ? 'user' : 'assistant', content: m.content }))
                            .concat([{ role: 'user', content: messageText }]),
                        stream: false
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();

                // Add assistant response
                const assistantMessage: Message = {
                    id: generateId(),
                    sender: 'agent', // Changed from 'assistant' to 'agent' to match existing type
                    content: data.content || data.message || '',
                    timestamp: new Date(),
                    status: 'delivered'
                };

                addMessage(assistantMessage);

                // Save both messages to history
                await saveMessageToHistory(
                    activeSessionId,
                    userMessage.id,
                    'user',
                    messageText,
                    selectedAgent?.id,
                    selectedAgent?.name
                );
                await saveMessageToHistory(
                    activeSessionId,
                    assistantMessage.id,
                    'agent',
                    assistantMessage.content,
                    selectedAgent?.id,
                    selectedAgent?.name
                );

                // Update user message status
                setMessages(prev =>
                    prev.map(msg =>
                        msg.id === userMessage.id
                            ? { ...msg, status: 'sent' }
                            : msg
                    )
                );
            } catch (error) {
                console.error('HTTP fallback failed:', error);
                // Update message to show error
                setMessages(prev =>
                    prev.map(msg =>
                        msg.id === userMessage.id
                            ? { ...msg, status: 'error' }
                            : msg
                    )
                );
            }
        }

        // Focus back on input
        inputRef.current?.focus();
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleSessionSelect = async (sessionId: string) => {
        try {
            // Save session ID
            localStorage.setItem('chat_session_id', sessionId);
            setCurrentSessionId(sessionId);

            // Load session history
            const response = await fetch(apiPath(`/v1/chat/history/${sessionId}`));
            if (response.ok) {
                const data = await response.json();

                if (Array.isArray(data.messages) && data.messages.length > 0) {
                    const loadedMessages = (data.messages as RawChatMessage[]).map((msg) => ({
                        id: msg.id,
                        sender: msg.sender,
                        agent_id: msg.agent_id,
                        agent_name: msg.agent_name,
                        content: msg.content,
                        timestamp: new Date(msg.timestamp),
                        status: 'delivered' as const
                    }));

                    setMessages(loadedMessages);
                }
            }
        } catch (error) {
            console.error('Failed to switch session:', error);
        }
    };

    const handleNewChat = () => {
        try {
            // Clear current messages
            setMessages([]);

            // Generate new session ID
            const newSessionId = generateId();
            console.log('🔵 Generated new session ID:', newSessionId);
            localStorage.setItem('chat_session_id', newSessionId);
            setCurrentSessionId(newSessionId);
        } catch (error) {
            console.error('Error starting new chat:', error);
            alert('Failed to start new chat. Please try again.');
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <>
            {!embedded && (
                <ChatHistorySidebar
                    currentSessionId={currentSessionId}
                    onSessionSelect={handleSessionSelect}
                    onNewChat={handleNewChat}
                />
            )}
            <div className={`chat-interface dcis-chat ${embedded ? 'embedded' : ''}`}>
                {/* Header */}
                <div className="chat-header">
                    <div className="agent-selector">
                        <Bot className="bot-icon" size={24} />
                        <select
                            value={selectedAgent?.id || ''}
                            onChange={(e) => {
                                const agent = availableAgents.find(a => a.id === e.target.value);
                                setSelectedAgent(agent || null);
                            }}
                            className="agent-dropdown"
                        >
                            <option value="">Select Agent...</option>
                            {availableAgents.map(agent => (
                                <option key={agent.id} value={agent.id}>
                                    {agent.name} - {agent.specialty}
                                </option>
                            ))}
                        </select>
                    </div>

                    {selectedAgent && (
                        <div className="agent-status">
                            <span className={`chat-status-dot ${selectedAgent.status}`} />
                            <span>{selectedAgent.status}</span>
                        </div>
                    )}

                    <button
                        onClick={handleNewChat}
                        className="new-chat-btn"
                        title="Start New Chat"
                    >
                        <PlusCircle size={20} />
                        <span>New Chat</span>
                    </button>
                </div>

                {/* Messages Container */}
                <div className="messages-container">
                    {messages.length === 0 && !isTyping && (
                        <div className="chat-empty-state">
                            <Sparkles size={32} className="chat-empty-icon" />
                            <p className="chat-empty-text">
                                {selectedAgent
                                    ? `Start a conversation with ${selectedAgent.name}`
                                    : 'Select an agent above to begin chatting'}
                            </p>
                        </div>
                    )}
                    <AnimatePresence initial={false}>
                        {messages.map((message) => (
                            <MessageBubble
                                key={message.id}
                                message={message}
                            />
                        ))}
                    </AnimatePresence>

                    {/* Typing Indicator */}
                    {isTyping && <TypingIndicator agentName={selectedAgent?.name} />}

                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="input-container">
                    <textarea
                        ref={inputRef}
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder={
                            selectedAgent
                                ? `Message ${selectedAgent.name}...`
                                : 'Select an agent above to start chatting...'
                        }
                        className="message-input"
                        rows={1}
                    />

                    <motion.button
                        onClick={sendMessage}
                        disabled={!inputText.trim()}
                        className="send-button"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        <Send size={20} />
                    </motion.button>
                </div>
            </div>
        </>
    );
}

// ============================================================================
// Message Bubble Component
// ============================================================================

interface MessageBubbleProps {
    message: Message;
}

function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.sender === 'user';
    const [feedback, setFeedback] = useState<'thumbs_up' | 'thumbs_down' | null>(message.feedback || null);

    const handleFeedback = async (type: 'thumbs_up' | 'thumbs_down') => {
        // Toggle if clicking same button
        if (feedback === type) {
            setFeedback(null);
            return;
        }

        setFeedback(type);

        // Submit feedback to backend
        try {
            await fetch(apiPath('/v1/rlhf/feedback'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: 'session-' + Date.now(),
                    message_id: message.id,
                    agent_id: message.agent_id || 'unknown',
                    feedback_type: type,
                    user_query: '', // Would need to track previous user message
                    agent_response: message.content,
                    rating: type === 'thumbs_up' ? 1.0 : 0.0,
                }),
            });
        } catch (error) {
            console.error('Failed to submit feedback:', error);
        }
    };

    return (
        <motion.div
            className={`message-wrapper ${isUser ? 'user' : 'agent'}`}
            data-role={isUser ? 'USER' : 'DCID'}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
        >
            {/* Avatar */}
            {!isUser && (
                <div
                    className="message-avatar"
                    style={{
                        background: `linear-gradient(135deg, ${message.agent_name ? getAgentColor(message.agent_id || '') : '#667eea'} 0%, #764ba2 100%)`
                    }}
                >
                    <Bot size={20} />
                </div>
            )}

            <div className={`message-bubble ${isUser ? 'user' : 'agent'}`}>
                {/* Agent Name */}
                {!isUser && message.agent_name && (
                    <div className="agent-name">{message.agent_name}</div>
                )}

                {/* Content */}
                <div className="message-content">
                    {isUser ? (
                        <p>{message.content}</p>
                    ) : (
                        <ReactMarkdown
                            components={{
                                code({ inline, className, children, ...rest }: React.ComponentPropsWithoutRef<'code'> & { inline?: boolean }) {
                                    const match = /language-(\w+)/.exec(className || '');
                                    return !inline && match ? (
                                        <SyntaxHighlighter
                                            style={vscDarkPlus}
                                            language={match[1]}
                                            PreTag="div"
                                            {...rest}
                                        >
                                            {String(children).replace(/\n$/, '')}
                                        </SyntaxHighlighter>
                                    ) : (
                                        <code className={className} {...rest}>
                                            {children}
                                        </code>
                                    );
                                }
                            }}
                        >
                            {message.content}
                        </ReactMarkdown>
                    )}
                </div>

                {/* Metadata */}
                <div className="message-meta">
                    <span className="timestamp">
                        {message.timestamp.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit'
                        })}
                    </span>

                    {isUser && (
                        <span className="status-icon">
                            {message.status === 'sending' && <Clock size={14} />}
                            {message.status === 'sent' && <Check size={14} />}
                            {message.status === 'delivered' && <CheckCheck size={14} />}
                        </span>
                    )}
                </div>

                {/* Feedback Buttons (only for agent messages) */}
                {!isUser && (
                    <div className="message-feedback">
                        <motion.button
                            onClick={() => handleFeedback('thumbs_up')}
                            className={`feedback-btn ${feedback === 'thumbs_up' ? 'active' : ''}`}
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            title="Helpful"
                        >
                            <ThumbsUp size={14} />
                        </motion.button>
                        <motion.button
                            onClick={() => handleFeedback('thumbs_down')}
                            className={`feedback-btn ${feedback === 'thumbs_down' ? 'active' : ''}`}
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            title="Not helpful"
                        >
                            <ThumbsDown size={14} />
                        </motion.button>
                    </div>
                )}
            </div>

            {/* User Avatar - Hidden in Quantum UI */}
            {/* {isUser && (
                <div className="message-avatar user">
                    <UserIcon size={20} />
                </div>
            )} */}
        </motion.div>
    );
}

// ============================================================================
// Typing Indicator Component
// ============================================================================

function TypingIndicator({ agentName }: { agentName?: string }) {
    return (
        <motion.div
            className="typing-indicator"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
        >
            <div className="typing-avatar">
                <Bot size={16} />
            </div>

            <div className="typing-bubble">
                <span className="agent-typing">
                    {agentName || 'Agent'} is typing
                </span>
                <div className="typing-dots">
                    <motion.span
                        animate={{ y: [0, -8, 0] }}
                        transition={{ repeat: Infinity, duration: 0.6, delay: 0 }}
                    />
                    <motion.span
                        animate={{ y: [0, -8, 0] }}
                        transition={{ repeat: Infinity, duration: 0.6, delay: 0.2 }}
                    />
                    <motion.span
                        animate={{ y: [0, -8, 0] }}
                        transition={{ repeat: Infinity, duration: 0.6, delay: 0.4 }}
                    />
                </div>
            </div>
        </motion.div>
    );
}

// ============================================================================
// Utility Functions
// ============================================================================

function generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function getAgentColor(agentId: string): string {
    const colors = [
        '#667eea',
        '#764ba2',
        '#f093fb',
        '#4facfe',
        '#43e97b',
        '#fa709a',
        '#feca57',
        '#48dbfb'
    ];

    // Safety check for undefined/null agentId
    if (!agentId || typeof agentId !== 'string') {
        return colors[0]; // Return default color
    }

    // Hash agent ID to get consistent color
    const hash = agentId.split('').reduce((acc, char) => {
        return char.charCodeAt(0) + ((acc << 5) - acc);
    }, 0);

    return colors[Math.abs(hash) % colors.length];
}

function isUuidLike(value: string): boolean {
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}
