"use client"

import * as React from "react"
import { Send, Bot, User } from "lucide-react"
import { useChatStore } from "@/store/chatStore"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

// TODO: Implement WebSocket streaming when real-time backend is configured
// import { useSocketListener } from "@/lib/socket/use-socket"

interface ChatTokenData {
    id: string;
    token: string;
    agentId?: string;
}

export function ChatInterface() {
    const { messages, addMessage } = useChatStore()
    const [inputValue, setInputValue] = React.useState("")
    const scrollRef = React.useRef<HTMLDivElement>(null)

    // TODO: Enable when WebSocket backend is ready
    // Listen for streaming tokens
    // useSocketListener('chat:token', (data: ChatTokenData) => {
    //     console.log("Token:", data);
    //     // In a real implementation: appendToken(data.id, data.token)
    // }, 'chat');

    const handleSendMessage = async (e?: React.FormEvent) => {
        e?.preventDefault()
        const messageText = inputValue; // Capture before clearing
        console.log('📤 Sending message:', messageText)
        if (!messageText.trim()) return

        // Add User Message
        const userMsg = {
            sender: "Commander",
            role: "user" as const,
            content: messageText
        }
        addMessage(userMsg)
        console.log('✅ User message added to store')
        setInputValue("")


        try {
            // Call Real Backend
            const response = await fetch("http://localhost:8008/api/v1/chat/completions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    messages: [
                        ...messages.map(m => ({ role: m.role, content: m.content })),
                        { role: "user", content: inputValue }
                    ],
                    stream: false
                })
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errorData.detail || `Error ${response.status}`);
            }

            const data = await response.json()
            console.log('✅ Backend Response:', data)
            console.log('✅ Extracted content:', data.content)

            // Update Agent Message
            // Backend returns {role: "assistant", content: "..."}
            addMessage({
                sender: "Logician",
                role: "agent", // Changed from "assistant" to match ChatMessage type
                content: data.content || data // Fallback if structure changes
            })
            console.log('✅ Agent message added to store')

        } catch (error) {
            console.error("Chat Error:", error)
            addMessage({
                sender: "System",
                role: "system",
                content: `Error: ${error instanceof Error ? error.message : "Comms Failure"}`
            })
        }
    }

    // Auto-scroll to bottom
    React.useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" })
        }
    }, [messages])

    return (
        <GlassPanel className="w-full h-full flex flex-col p-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between mb-4 border-b border-white/10 pb-4">
                <div className="flex items-center gap-2">
                    <Bot className="w-6 h-6 text-cyan-400" />
                    <h2 className="text-xl font-mono text-cyan-100 uppercase tracking-widest">Neural Link</h2>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    <span className="text-xs text-green-400 font-mono uppercase">Online</span>
                </div>
            </div>

            {/* Messages Area */}
            <ScrollArea className="flex-1 pr-4">
                <div className="space-y-4">
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                        >
                            <Avatar className={`w-8 h-8 border ${msg.role === 'user' ? 'border-white/20' : 'border-cyan-500/50'}`}>
                                {msg.role === 'user' ? (
                                    <AvatarFallback className="bg-white/10"><User className="w-4 h-4" /></AvatarFallback>
                                ) : (
                                    <AvatarFallback className="bg-cyan-500/20 text-cyan-400">AI</AvatarFallback>
                                )}
                            </Avatar>

                            <div className={`max-w-[70%] p-3 rounded-lg text-sm ${msg.role === 'user'
                                ? 'bg-white/10 text-white rounded-tr-none'
                                : 'bg-cyan-950/40 border border-cyan-500/20 text-cyan-100 rounded-tl-none'
                                }`}>
                                <div className="font-mono text-xs opacity-50 mb-1 flex justify-between gap-4">
                                    <span>{msg.sender}</span>
                                    <span>{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                </div>
                                <p className="leading-relaxed">{msg.content}</p>
                            </div>
                        </div>
                    ))}

                    {/* Scroll Anchor */}
                    <div ref={scrollRef} />
                </div>
            </ScrollArea>

            {/* Input Area */}
            <form onSubmit={handleSendMessage} className="mt-4 flex gap-2">
                <div className="relative flex-1">
                    <Input
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Transmit command..."
                        className="bg-black/20 border-white/10 text-white placeholder:text-white/30 focus-visible:ring-cyan-500/50"
                    />
                    {/* Corner decorations for input */}
                    <div className="absolute bottom-0 right-0 w-2 h-2 border-r border-b border-cyan-500/50 rounded-br-none pointer-events-none" />
                </div>
                <Button
                    type="submit"
                    size="icon"
                    className="bg-cyan-600 hover:bg-cyan-500 text-white border border-cyan-400/30"
                >
                    <Send className="w-4 h-4" />
                </Button>
            </form>
        </GlassPanel>
    )
}
