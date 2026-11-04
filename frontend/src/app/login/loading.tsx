import { StackSkeleton } from "@/components/skeletons";
import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div className="wrap grid gap-8 py-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
      <div className="panel space-y-5 p-6">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-40 w-full rounded-2xl" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-12 w-full rounded-full" />
      </div>
      <div className="space-y-5">
        <Skeleton className="h-9 w-56" />
        <Skeleton className="h-4 w-72" />
        <div className="grid gap-3 sm:grid-cols-2">
          <StackSkeleton rows={2} />
        </div>
        <div className="panel space-y-3 p-5">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-28 rounded-full" />
        </div>
      </div>
    </div>
  );
}
