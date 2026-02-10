"use client";

import { useEffect } from "react";
import { useIsMobile } from "@/hooks/use-responsive";
import { AlertTriangle } from "lucide-react";

export function MobileWarning() {
    const isMobile = useIsMobile();

    useEffect(() => {
        if (isMobile) {
            console.warn(
                "DCIS is optimized for desktop viewing. Some features may be limited on mobile devices."
            );
        }
    }, [isMobile]);

    if (!isMobile) return null;

    return (
        <div className="fixed inset-x-0 bottom-0 z-50 bg-yellow-500/90 p-4 text-center text-sm font-medium text-yellow-950 backdrop-blur-sm">
            <div className="flex items-center justify-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                <p>This app is optimized for desktop viewing (1920x1080+)</p>
            </div>
        </div>
    );
}
