import { PlanVisualizer } from "@/components/conductor/PlanVisualizer";

export default function ConductorPage() {
  return (
    <div className="h-full min-h-full p-3 sm:p-4 md:p-6">
      <div className="mx-auto h-full w-full max-w-[1600px]">
        <PlanVisualizer />
      </div>
    </div>
  );
}
