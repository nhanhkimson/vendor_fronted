"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { StackSkeleton } from "@/components/skeletons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api";
import { money, titleCase } from "@/lib/format";
import { shopLabel } from "@/lib/labels";
import { approveListing, listPendingListings, rejectListing, type ListingProduct } from "@/lib/listing-api";

async function run(work: () => Promise<unknown>, ok: string) {
  try {
    await work();
    toast.success(ok);
  } catch (error) {
    toast.error(error instanceof ApiError ? error.message : "That did not work");
  }
}

export function ListingQueue() {
  const queryClient = useQueryClient();
  const listings = useQuery({ queryKey: ["pending-listings"], queryFn: () => listPendingListings() });
  const [rejecting, setRejecting] = useState<ListingProduct | null>(null);
  const [reason, setReason] = useState("Needs clearer photos or product details before going live.");

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["pending-listings"] });
    await queryClient.invalidateQueries({ queryKey: ["summary", "admin"] });
  }

  const rows = listings.data || [];

  return (
    <div className="space-y-6">
      <div className="max-w-2xl space-y-2">
        <h1 className="serif text-4xl">Publish</h1>
        <p className="text-sm text-muted-foreground">
          One job: preview what shops submitted, then publish or send back with a reason.
        </p>
      </div>

      {listings.isLoading ? <StackSkeleton rows={4} /> : null}
      {!listings.isLoading && !rows.length ? (
        <div className="panel space-y-2 p-10 text-center">
          <p className="serif text-3xl">Queue clear</p>
          <p className="text-sm text-muted-foreground">Nothing waiting for review. New seller submissions land here.</p>
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        {rows.map((row) => (
          <article key={row.id} className="panel overflow-hidden">
            <div className="grid gap-0 sm:grid-cols-[160px_1fr]">
              <div className="relative min-h-40 bg-muted sm:min-h-full">
                {row.image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={row.image_url} alt="" className="absolute inset-0 h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full min-h-40 items-center justify-center px-3 text-center text-sm text-muted-foreground">
                    No photo
                  </div>
                )}
              </div>
              <div className="flex flex-col gap-4 p-5">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0 space-y-1">
                    <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                      {shopLabel(row.vendor_id || "", row.vendor_name || "Shop")}
                    </p>
                    <h2 className="serif text-2xl leading-none">{row.title}</h2>
                    <p className="price price-md mt-2">{money(row.price_cents)}</p>
                  </div>
                  <Badge variant="secondary">
                    {row.listing_status === "pending_review" ? "In review" : titleCase(row.listing_status)}
                  </Badge>
                </div>
                {row.description ? <p className="line-clamp-3 text-sm text-muted-foreground">{row.description}</p> : null}
                <p className="text-sm text-muted-foreground">{row.available} in stock</p>
                <div className="dash-actions mt-auto border-t border-border pt-4">
                  <Button
                    size="lg"
                    onClick={() => void run(() => approveListing(row.id).then(() => refresh()), "Listing published")}
                  >
                    Publish
                  </Button>
                  <Button size="lg" variant="outline" onClick={() => setRejecting(row)}>
                    Reject
                  </Button>
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>

      <Dialog open={Boolean(rejecting)} onOpenChange={(next) => !next && setRejecting(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject listing</DialogTitle>
            <DialogDescription>
              {rejecting ? `${rejecting.title} stays off the website until the seller resubmits.` : null}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="reason">Reason</Label>
            <Textarea id="reason" value={reason} onChange={(event) => setReason(event.target.value)} rows={4} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRejecting(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (!rejecting) return;
                void run(
                  () => rejectListing(rejecting.id, reason.trim() || "Needs clearer details").then(() => refresh()),
                  "Listing rejected",
                ).then(() => setRejecting(null));
              }}
            >
              Reject
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
