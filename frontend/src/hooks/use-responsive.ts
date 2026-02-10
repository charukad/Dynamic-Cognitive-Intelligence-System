/**
 * Responsive design utilities and hooks
 */

import { useEffect, useState } from "react";

// Breakpoints matching Tailwind CSS
export const breakpoints = {
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
    "2xl": 1536,
} as const;

export type Breakpoint = keyof typeof breakpoints;

/**
 * Hook to detect current screen size breakpoint
 */
export function useBreakpoint() {
    const [breakpoint, setBreakpoint] = useState<Breakpoint>("2xl");

    useEffect(() => {
        const updateBreakpoint = () => {
            const width = window.innerWidth;

            if (width < breakpoints.sm) {
                setBreakpoint("sm");
            } else if (width < breakpoints.md) {
                setBreakpoint("md");
            } else if (width < breakpoints.lg) {
                setBreakpoint("lg");
            } else if (width < breakpoints.xl) {
                setBreakpoint("xl");
            } else {
                setBreakpoint("2xl");
            }
        };

        updateBreakpoint();
        window.addEventListener("resize", updateBreakpoint);

        return () => window.removeEventListener("resize", updateBreakpoint);
    }, []);

    return breakpoint;
}

/**
 * Hook to check if viewport is mobile
 */
export function useIsMobile() {
    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth < breakpoints.md);
        };

        checkMobile();
        window.addEventListener("resize", checkMobile);

        return () => window.removeEventListener("resize", checkMobile);
    }, []);

    return isMobile;
}

/**
 * Hook to check if viewport is tablet
 */
export function useIsTablet() {
    const [isTablet, setIsTablet] = useState(false);

    useEffect(() => {
        const checkTablet = () => {
            const width = window.innerWidth;
            setIsTablet(width >= breakpoints.md && width < breakpoints.lg);
        };

        checkTablet();
        window.addEventListener("resize", checkTablet);

        return () => window.removeEventListener("resize", checkTablet);
    }, []);

    return isTablet;
}

/**
 * Hook to get current viewport dimensions
 */
export function useViewport() {
    const [viewport, setViewport] = useState({
        width: typeof window !== "undefined" ? window.innerWidth : 0,
        height: typeof window !== "undefined" ? window.innerHeight : 0,
    });

    useEffect(() => {
        const updateViewport = () => {
            setViewport({
                width: window.innerWidth,
                height: window.innerHeight,
            });
        };

        updateViewport();
        window.addEventListener("resize", updateViewport);

        return () => window.removeEventListener("resize", updateViewport);
    }, []);

    return viewport;
}

/**
 * Hook for media queries
 */
export function useMediaQuery(query: string) {
    const [matches, setMatches] = useState(() => {
        // Server-side safe initialization
        if (typeof window === 'undefined') return false;
        return window.matchMedia(query).matches;
    });

    useEffect(() => {
        const mediaQuery = window.matchMedia(query);

        const handler = (event: MediaQueryListEvent) => {
            setMatches(event.matches);
        };

        mediaQuery.addEventListener("change", handler);

        return () => mediaQuery.removeEventListener("change", handler);
    }, [query]);

    return matches;
}

/**
 * Check if device prefers reduced motion
 */
export function usePrefersReducedMotion() {
    return useMediaQuery("(prefers-reduced-motion: reduce)");
}

/**
 * Check if device prefers dark mode
 */
export function usePrefersDarkMode() {
    return useMediaQuery("(prefers-color-scheme: dark)");
}

/**
 * Responsive class helper
 */
export function cn(...classes: (string | undefined | null | false)[]) {
    return classes.filter(Boolean).join(" ");
}
