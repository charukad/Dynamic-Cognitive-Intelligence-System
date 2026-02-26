import { ChatInterface } from "@/components/chat/ChatInterface";

export default function ChatPage() {
  return (
    <div className="h-[calc(100vh-3.5rem)] p-4 md:p-6">
      <div className="h-full overflow-hidden rounded-xl border border-white/10 bg-black/40">
        <ChatInterface />
      </div>
    </div>
  );
}
