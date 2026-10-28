import { StackSkeleton } from "@/components/skeletons";
import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div className="wrap flex flex-col gap-8 py-10 lg:grid lg:grid-cols-[320px_1fr]">
      <div className="space-y-3 lg:col-start-2">
        <Skeleton className="h-10 w-56" />
        <Skeleton className="h-4 w-72" />
        <div className="grid gap-3 sm:grid-cols-2">
          <StackSkeleton rows={4} />
        </div>
      </div>
      <div className="panel space-y-3 p-5 lg:col-start-1 lg:row-start-1">
        <Skeleton className="h-10 w-40" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-28 rounded-full" />
      </div>
    </div>
  );
}
