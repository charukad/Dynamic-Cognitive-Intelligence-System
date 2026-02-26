import { EvolutionDashboard } from "@/components/evolution/EvolutionDashboard";

export default function EvolutionPage() {
  return (
    <div className="h-full min-h-full p-3 sm:p-4 md:p-6">
      <div className="mx-auto h-full w-full max-w-[1600px]">
        <EvolutionDashboard />
      </div>
    </div>
  );
}
