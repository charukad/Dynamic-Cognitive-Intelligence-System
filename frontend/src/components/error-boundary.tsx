"use client";

import React from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface ErrorBoundaryProps {
    children: React.ReactNode;
    fallback?: React.ReactNode;
    onReset?: () => void;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends React.Component<
    ErrorBoundaryProps,
    ErrorBoundaryState
> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error("Error Boundary caught an error:", error, errorInfo);
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null });
        this.props.onReset?.();
    };

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className="flex min-h-screen items-center justify-center p-4">
                    <Card className="max-w-md p-8">
                        <div className="flex flex-col items-center gap-4 text-center">
                            <div className="rounded-full bg-destructive/10 p-4">
                                <AlertTriangle className="h-8 w-8 text-destructive" />
                            </div>

                            <div>
                                <h2 className="text-2xl font-bold">Something went wrong</h2>
                                <p className="mt-2 text-muted-foreground">
                                    {this.state.error?.message || "An unexpected error occurred"}
                                </p>
                            </div>

                            <Button
                                onClick={this.handleReset}
                                className="mt-4 gap-2"
                            >
                                <RefreshCcw className="h-4 w-4" />
                                Try Again
                            </Button>

                            {process.env.NODE_ENV === "development" && this.state.error && (
                                <details className="mt-4 w-full text-left">
                                    <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
                                        Error Details
                                    </summary>
                                    <pre className="mt-2 overflow-auto rounded-lg bg-muted p-4 text-xs">
                                        {this.state.error.stack}
                                    </pre>
                                </details>
                            )}
                        </div>
                    </Card>
                </div>
            );
        }

        return this.props.children;
    }
}

export function ErrorFallback({
    error,
    resetError
}: {
    error: Error;
    resetError: () => void;
}) {
    return (
        <div className="flex min-h-[400px] items-center justify-center p-4">
            <Card className="max-w-md p-6">
                <div className="flex flex-col items-center gap-4 text-center">
                    <div className="rounded-full bg-destructive/10 p-3">
                        <AlertTriangle className="h-6 w-6 text-destructive" />
                    </div>

                    <div>
                        <h3 className="text-lg font-semibold">Error Loading Component</h3>
                        <p className="mt-1 text-sm text-muted-foreground">
                            {error.message}
                        </p>
                    </div>

                    <Button onClick={resetError} size="sm" variant="outline">
                        <RefreshCcw className="mr-2 h-3 w-3" />
                        Retry
                    </Button>
                </div>
            </Card>
        </div>
    );
}

export function NotFound({
    title = "Not Found",
    description = "The page you're looking for doesn't exist.",
    actionLabel = "Go Home",
    actionHref = "/",
}: {
    title?: string;
    description?: string;
    actionLabel?: string;
    actionHref?: string;
}) {
    return (
        <div className="flex min-h-screen items-center justify-center p-4">
            <div className="text-center">
                <h1 className="text-9xl font-bold text-muted-foreground/20">404</h1>
                <h2 className="mt-4 text-3xl font-bold">{title}</h2>
                <p className="mt-2 text-muted-foreground">{description}</p>
                <Button asChild className="mt-6">
                    <a href={actionHref}>{actionLabel}</a>
                </Button>
            </div>
        </div>
    );
}

export function APIError({
    statusCode,
    message,
    onRetry,
}: {
    statusCode?: number;
    message: string;
    onRetry?: () => void;
}) {
    return (
        <div className="flex items-center justify-center p-8">
            <Card className="max-w-md p-6">
                <div className="flex flex-col items-center gap-4 text-center">
                    <div className="rounded-full bg-destructive/10 p-3">
                        <AlertTriangle className="h-6 w-6 text-destructive" />
                    </div>

                    <div>
                        {statusCode && (
                            <div className="text-sm font-mono text-muted-foreground">
                                Error {statusCode}
                            </div>
                        )}
                        <h3 className="mt-1 text-lg font-semibold">API Request Failed</h3>
                        <p className="mt-1 text-sm text-muted-foreground">{message}</p>
                    </div>

                    {onRetry && (
                        <Button onClick={onRetry} size="sm" variant="outline">
                            <RefreshCcw className="mr-2 h-3 w-3" />
                            Retry Request
                        </Button>
                    )}
                </div>
            </Card>
        </div>
    );
}
