import { Navigation } from "@/components/navigation";
import { ErrorBoundary } from "@/components/error-boundary";

export default function MainLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex flex-col h-screen overflow-hidden">
            <Navigation />
            <main className="flex-1 overflow-auto pt-14">
                <ErrorBoundary>
                    {children}
                </ErrorBoundary>
            </main>
        </div>
    );
}
