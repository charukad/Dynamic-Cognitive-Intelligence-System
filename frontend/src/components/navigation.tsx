import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
    HomeIcon,
    MessageSquareIcon,
    UsersIcon,
    BrainCircuitIcon,
    SettingsIcon,
    ActivityIcon,
} from "lucide-react";

const navItems = [
    {
        name: "Home",
        href: "/",
        icon: HomeIcon,
    },
    {
        name: "Chat",
        href: "/chat",
        icon: MessageSquareIcon,
    },
    {
        name: "Agents",
        href: "/agents",
        icon: UsersIcon,
    },
    {
        name: "Orbit",
        href: "/orbit",
        icon: ActivityIcon,
    },
    {
        name: "Neural Link",
        href: "/neural-link",
        icon: BrainCircuitIcon,
    },
    {
        name: "Settings",
        href: "/settings",
        icon: SettingsIcon,
    },
];

export function Navigation() {
    const pathname = usePathname();

    return (
        <nav className="fixed left-0 top-0 z-50 h-screen w-20 border-r border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex h-full flex-col items-center justify-between py-8">
                {/* Logo */}
                <Link href="/" className="group">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 transition-transform hover:scale-110">
                        <BrainCircuitIcon className="h-6 w-6 text-white" />
                    </div>
                </Link>

                {/* Navigation Items */}
                <div className="flex flex-col items-center gap-4">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href;
                        const Icon = item.icon;

                        return (
                            <Link key={item.href} href={item.href}>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className={cn(
                                        "relative h-12 w-12 rounded-xl transition-all",
                                        isActive
                                            ? "bg-primary/10 text-primary"
                                            : "text-muted-foreground hover:text-foreground hover:bg-accent"
                                    )}
                                    aria-label={item.name}
                                >
                                    <Icon className="h-5 w-5" />
                                    {isActive && (
                                        <div className="absolute left-0 top-1/2 h-8 w-1 -translate-y-1/2 rounded-r-full bg-primary" />
                                    )}
                                </Button>
                            </Link>
                        );
                    })}
                </div>

                {/* Status Indicator */}
                <div className="flex flex-col items-center gap-2">
                    <div className="relative">
                        <div className="h-3 w-3 rounded-full bg-green-500" />
                        <div className="absolute inset-0 h-3 w-3 animate-ping rounded-full bg-green-400 opacity-75" />
                    </div>
                    <span className="text-xs text-muted-foreground">Online</span>
                </div>
            </div>
        </nav>
    );
}
