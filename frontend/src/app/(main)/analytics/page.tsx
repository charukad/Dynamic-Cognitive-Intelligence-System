import { PerformanceDashboard } from "@/components/analytics/PerformanceDashboard";

export default function AnalyticsPage() {
  return (
    <div className="h-full min-h-full p-3 sm:p-4 md:p-6">
      <div className="mx-auto h-full w-full max-w-[1600px]">
        <PerformanceDashboard />
      </div>
    </div>
  );
}
