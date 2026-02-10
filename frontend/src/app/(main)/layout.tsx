import { Navigation } from "@/components/navigation";
import { ErrorBoundary } from "@/components/error-boundary";
import { MobileWarning } from "@/components/mobile-warning";

export default function MainLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex h-screen overflow-hidden">
            <Navigation />
            <main className="flex-1 overflow-auto">
                <ErrorBoundary>
                    {children}
                </ErrorBoundary>
            </main>
            <MobileWarning />
        </div>
    );
}
