import { Skeleton } from "@/components/ui/skeleton";

function Frame({ children, label = "Loading" }: { children: React.ReactNode; label?: string }) {
  return (
    <div role="status" aria-live="polite" aria-busy="true">
      <span className="sr-only">{label}</span>
      {children}
    </div>
  );
}

export function HomeSkeleton() {
  return (
    <Frame label="Loading the shop">
      <div className="wrap space-y-12 py-8">
        <div className="grid gap-8 md:grid-cols-2">
          <div className="space-y-4">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-16 w-full max-w-md" />
            <Skeleton className="h-4 w-full max-w-sm" />
            <div className="flex gap-3">
              <Skeleton className="h-9 w-24 rounded-full" />
              <Skeleton className="h-9 w-24 rounded-full" />
              <Skeleton className="h-9 w-28 rounded-full" />
            </div>
          </div>
          <Skeleton className="h-48" />
        </div>
        <ProductGridSkeleton />
      </div>
    </Frame>
  );
}

export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid-cards">
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="panel overflow-hidden">
          <Skeleton className="h-40 rounded-none" />
          <div className="space-y-2 p-4">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-3 w-16" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function CatalogueSkeleton() {
  return (
    <Frame label="Loading the catalogue">
      <div className="wrap space-y-6 py-8">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-4 w-32" />
        <ProductGridSkeleton />
      </div>
    </Frame>
  );
}

export function ShopListSkeleton() {
  return (
    <Frame label="Loading shops">
      <div className="wrap space-y-6 py-8">
        <Skeleton className="h-12 w-40" />
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }, (_, index) => (
            <Skeleton key={index} className="h-32" />
          ))}
        </div>
      </div>
    </Frame>
  );
}

export function ProductSkeleton() {
  return (
    <Frame label="Loading this piece">
      <div className="wrap grid gap-8 py-8 md:grid-cols-2">
        <Skeleton className="min-h-80" />
        <div className="space-y-4">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-14 w-56" />
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-10 w-32 rounded-full" />
        </div>
      </div>
    </Frame>
  );
}

export function ReviewListSkeleton() {
  return (
    <Frame label="Loading reviews">
      <div className="wrap space-y-4 py-8">
        <Skeleton className="h-12 w-48" />
        {Array.from({ length: 4 }, (_, index) => (
          <Skeleton key={index} className="h-24" />
        ))}
      </div>
    </Frame>
  );
}

export function WorkspaceSkeleton() {
  return (
    <Frame label="Loading your workspace">
      <div className="wrap grid gap-8 py-8 md:grid-cols-[220px_1fr]">
        <div className="space-y-3">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-8 w-36" />
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-8 w-full rounded-full" />
          ))}
        </div>
        <div className="space-y-4">
          <Skeleton className="h-12 w-56" />
          <div className="grid gap-3 sm:grid-cols-3">
            {Array.from({ length: 6 }, (_, index) => (
              <Skeleton key={index} className="h-24" />
            ))}
          </div>
        </div>
      </div>
    </Frame>
  );
}

export function TableSkeleton({ columns = 4, rows = 6 }: { columns?: number; rows?: number }) {
  return (
    <Frame label="Loading the list">
      <div className="panel space-y-4 p-4">
        {Array.from({ length: rows }, (_, row) => (
          <div key={row} className="flex gap-4">
            {Array.from({ length: columns }, (_, column) => (
              <Skeleton key={column} className="h-4 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </Frame>
  );
}

export function StackSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <Frame>
      <div className="space-y-3">
        {Array.from({ length: rows }, (_, index) => (
          <Skeleton key={index} className="h-20 w-full" />
        ))}
      </div>
    </Frame>
  );
}

export function CartSkeleton() {
  return (
    <Frame label="Loading your cart">
      <div className="wrap space-y-4 py-8">
        <Skeleton className="h-12 w-32" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-10 w-36 rounded-full" />
      </div>
    </Frame>
  );
}

export function CheckoutSkeleton() {
  return (
    <Frame label="Loading checkout">
      <div className="wrap max-w-xl space-y-4 py-8">
        <Skeleton className="h-12 w-48" />
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-12" />
        <Skeleton className="h-12" />
        <Skeleton className="h-12" />
        <Skeleton className="h-10 w-28 rounded-full" />
      </div>
    </Frame>
  );
}
