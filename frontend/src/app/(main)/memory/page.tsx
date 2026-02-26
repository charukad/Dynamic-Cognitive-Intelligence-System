import { MemoryInspector } from "@/components/memory/MemoryInspector";

export default function MemoryPage() {
  return (
    <div className="h-full min-h-full p-3 sm:p-4 md:p-6">
      <div className="mx-auto h-full w-full max-w-[1600px]">
        <MemoryInspector />
      </div>
    </div>
  );
}
