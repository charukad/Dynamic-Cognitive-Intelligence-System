import { NotFound } from "@/components/error-boundary";

export default function NotFoundPage() {
    return (
        <NotFound
            title="Page Not Found"
            description="The page you're looking for doesn't exist or has been moved."
            actionLabel="Return to Dashboard"
            actionHref="/"
        />
    );
}
