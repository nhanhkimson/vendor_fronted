"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { Records } from "@/components/records";
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
  const [rejecting, setRejecting] = useState<ListingProduct | null>(null);
  const [reason, setReason] = useState("Needs clearer photos or product details before going live.");

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["pending-listings"] });
    await queryClient.invalidateQueries({ queryKey: ["summary", "admin"] });
  }

  return (
    <>
      <Records
        title="Listings to moderate"
        hint="Maker-checker queue. Approve to publish on the website, or reject with a reason the seller can fix."
        queryKey={["pending-listings"]}
        load={() => listPendingListings()}
        columns={[
          { key: "title", label: "Title" },
          { key: "vendor_name", label: "Shop" },
          { key: "price", label: "Price", render: (row) => money(row.price_cents) },
          {
            key: "listing_status",
            label: "Status",
            render: (row) => <Badge variant="secondary">{titleCase(row.listing_status)}</Badge>,
          },
        ]}
        render={(row) => (
          <div className="flex flex-wrap justify-end gap-2">
            <Button
              size="sm"
              onClick={() =>
                void run(
                  () => approveListing(row.id).then(() => refresh()),
                  "Listing published",
                )
              }
            >
              Approve
            </Button>
            <Button size="sm" variant="outline" onClick={() => setRejecting(row)}>
              Reject
            </Button>
          </div>
        )}
      />

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
                  () => rejectListing(rejecting.id, reason.trim() || "Needs more detail").then(() => refresh()),
                  "Listing rejected",
                ).then(() => setRejecting(null));
              }}
            >
              Reject listing
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
