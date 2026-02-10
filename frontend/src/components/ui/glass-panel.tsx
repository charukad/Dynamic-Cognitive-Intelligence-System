import { cn } from "@/lib/utils"

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode
    variant?: "default" | "thin" | "ghost"
}

export function GlassPanel({
    children,
    className,
    variant = "default",
    ...props
}: GlassPanelProps) {
    return (
        <div
            className={cn(
                "relative overflow-hidden rounded-xl border border-white/10 backdrop-blur-md shadow-xl transition-all duration-300",
                variant === "default" && "bg-black/40 hover:bg-black/50 hover:border-white/20 hover:shadow-cyan-500/10",
                variant === "thin" && "bg-black/20 border-white/5",
                variant === "ghost" && "bg-transparent border-transparent hover:bg-white/5",
                className
            )}
            {...props}
        >
            {/* Sci-fi corner accents */}
            <div className="absolute top-0 left-0 w-2 h-2 border-l border-t border-white/30 rounded-tl-sm pointer-events-none" />
            <div className="absolute top-0 right-0 w-2 h-2 border-r border-t border-white/30 rounded-tr-sm pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-2 h-2 border-l border-b border-white/30 rounded-bl-sm pointer-events-none" />
            <div className="absolute bottom-0 right-0 w-2 h-2 border-r border-b border-white/30 rounded-br-sm pointer-events-none" />

            {children}
        </div>
    )
}
