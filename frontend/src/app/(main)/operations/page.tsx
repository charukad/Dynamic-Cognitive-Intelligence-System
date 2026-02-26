import { OperationsDashboard } from "@/components/operations/OperationsDashboard";

export default function OperationsPage() {
  return (
    <div className="h-full min-h-full p-3 sm:p-4 md:p-6">
      <div className="mx-auto h-full w-full max-w-[1600px]">
        <OperationsDashboard />
      </div>
    </div>
  );
}
