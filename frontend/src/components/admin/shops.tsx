"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
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
import { Textarea } from "@/components/ui/textarea";
import { ApiError, browserApi, unwrap } from "@/lib/api";
import type { components } from "@/lib/api-types";
import { cityLabel, docLabel, shopBlurb, shopLabel, tierLabel } from "@/lib/labels";
import { titleCase } from "@/lib/format";

type Vendor = components["schemas"]["VendorOut"];
type Filter = "review" | "active" | "other";

async function run(work: () => Promise<unknown>, ok: string) {
  try {
    await work();
    toast.success(ok);
  } catch (error) {
    toast.error(error instanceof ApiError ? error.message : "That did not work");
  }
}

async function postVendor(path: string, body?: Record<string, string>) {
  const response = await fetch(path, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-Bazaar-Client": "web",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, typeof payload?.detail === "string" ? payload.detail : response.statusText, payload?.code);
  }
  return payload as Vendor;
}

export function ShopQueue() {
  const queryClient = useQueryClient();
  const vendors = useQuery({ queryKey: ["vendors"], queryFn: () => unwrap(browserApi.GET("/api/vendors")) });
  const [filter, setFilter] = useState<Filter>("review");
  const [reasonFor, setReasonFor] = useState<{ id: string; action: "reject" | "suspend"; name: string } | null>(null);
  const [reason, setReason] = useState("Documents do not match a real shop.");

  const rows = vendors.data || [];
  const grouped = useMemo(() => {
    const review = rows.filter((shop) => shop.status === "under_review" || shop.status === "draft");
    const active = rows.filter((shop) => shop.status === "active");
    const other = rows.filter((shop) => !review.includes(shop) && !active.includes(shop));
    return { review, active, other };
  }, [rows]);
  const shown = grouped[filter];

  function refresh() {
    return Promise.all([
      queryClient.invalidateQueries({ queryKey: ["vendors"] }),
      queryClient.invalidateQueries({ queryKey: ["summary", "admin"] }),
    ]);
  }

  return (
    <div className="space-y-6">
      <div className="max-w-2xl space-y-2">
        <h1 className="serif text-4xl">Shops</h1>
        <p className="text-sm text-muted-foreground">
          Three steps: accept into review, mark documents real, then verify. Buyers only see Live shops.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {(
          [
            ["review", "Needs review", grouped.review.length],
            ["active", "Live", grouped.active.length],
            ["other", "Paused", grouped.other.length],
          ] as const
        ).map(([id, label, count]) => (
          <button
            key={id}
            type="button"
            onClick={() => setFilter(id)}
            className={`rounded-full px-4 py-2 text-sm transition ${
              filter === id ? "bg-primary text-primary-foreground" : "bg-card ring-1 ring-border hover:ring-primary"
            }`}
          >
            {label}
            <span className="ml-2 opacity-70">{count}</span>
          </button>
        ))}
      </div>

      {vendors.isLoading ? <StackSkeleton rows={4} /> : null}
      {!vendors.isLoading && !shown.length ? (
        <div className="panel p-8 text-center text-sm text-muted-foreground">Nothing in this list.</div>
      ) : null}

      <div className="grid gap-5">
        {shown.map((shop) => (
          <ShopRow key={shop.id} shop={shop} onRefresh={refresh} onReason={setReasonFor} />
        ))}
      </div>

      <Dialog open={Boolean(reasonFor)} onOpenChange={(open) => !open && setReasonFor(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{reasonFor?.action === "suspend" ? "Suspend shop" : "Reject shop"}</DialogTitle>
            <DialogDescription>
              {reasonFor ? `${reasonFor.name} will not appear to buyers until this is resolved.` : null}
            </DialogDescription>
          </DialogHeader>
          <Textarea value={reason} onChange={(event) => setReason(event.target.value)} rows={4} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setReasonFor(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (!reasonFor) return;
                const note = { reason: reason.trim() || "Not a real shop" };
                const params = { path: { vendor_id: reasonFor.id } };
                void run(
                  () =>
                    (reasonFor.action === "suspend"
                      ? unwrap(browserApi.POST("/api/vendors/{vendor_id}/suspend", { params, body: note }))
                      : unwrap(browserApi.POST("/api/vendors/{vendor_id}/reject", { params, body: note }))
                    ).then(() => refresh()),
                  reasonFor.action === "suspend" ? "Shop suspended" : "Application rejected",
                ).then(() => setReasonFor(null));
              }}
            >
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function ShopRow({
  shop,
  onRefresh,
  onReason,
}: {
  shop: Vendor;
  onRefresh: () => Promise<unknown>;
  onReason: (value: { id: string; action: "reject" | "suspend"; name: string }) => void;
}) {
  const name = shopLabel(shop.id, shop.name);
  const blurb = shopBlurb(shop.id, shop.headline || "");
  const docs = shop.documents || [];
  const verifiedDocs = docs.filter((doc) => doc.status === "verified").length;
  const readyDocs = docs.filter((doc) => doc.status === "submitted" || doc.status === "verified" || doc.has_file);
  const missingDocs = docs.filter((doc) => doc.status === "missing" || doc.status === "rejected" || !doc.has_file);
  const allDocsVerified = docs.length > 0 && verifiedDocs === docs.length;
  const docsReady = docs.length > 0 && missingDocs.length === 0;
  const isDraft = shop.status === "draft" || shop.status === "rejected";
  const inReview = shop.status === "under_review";
  const step = isDraft ? 1 : inReview && !allDocsVerified ? 2 : inReview ? 3 : 0;

  return (
    <article className="panel overflow-hidden">
      <div className="grid gap-0 lg:grid-cols-[240px_1fr]">
        <div className="relative min-h-48 bg-muted lg:min-h-full">
          {shop.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={shop.image_url} alt="" className="absolute inset-0 h-full w-full object-cover" />
          ) : (
            <div className="flex h-full min-h-48 items-center justify-center px-4 text-center text-sm text-muted-foreground">
              {cityLabel(shop.city)}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-5 p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0 space-y-1">
              <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                {cityLabel(shop.city)} · {tierLabel(shop.tier_id, shop.tier_name)}
              </p>
              <h2 className="serif text-3xl leading-none">{name}</h2>
              {blurb ? <p className="max-w-xl text-sm text-muted-foreground">{blurb}</p> : null}
            </div>
            <Badge variant={shop.status === "active" ? "secondary" : inReview ? "outline" : "destructive"}>
              {titleCase(shop.status)}
            </Badge>
          </div>

          {(isDraft || inReview) && (
            <ol className="grid gap-2 sm:grid-cols-3">
              {[
                { n: 1, label: "Accept review", done: !isDraft },
                { n: 2, label: "Mark documents", done: !isDraft && allDocsVerified },
                { n: 3, label: "Verify & go live", done: shop.status === "active" },
              ].map((item) => (
                <li
                  key={item.n}
                  className={`rounded-xl px-3 py-2 text-xs ${
                    step === item.n ? "bg-secondary/15 text-secondary" : item.done ? "bg-muted text-muted-foreground" : "bg-muted/50 text-muted-foreground"
                  }`}
                >
                  <span className="font-medium">
                    {item.done ? "✓ " : `${item.n}. `}
                    {item.label}
                  </span>
                </li>
              ))}
            </ol>
          )}

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Documents</p>
              {docs.length ? (
                <p className="text-xs text-muted-foreground">
                  {verifiedDocs}/{docs.length} verified
                </p>
              ) : null}
            </div>
            {docs.length ? (
              <ul className="flex flex-wrap gap-2">
                {docs.map((doc) => {
                  const canMark = (doc.status === "submitted" || Boolean(doc.has_file)) && doc.status !== "verified";
                  return (
                    <li
                      key={doc.id}
                      className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs ring-1 ${
                        doc.status === "verified"
                          ? "bg-secondary/15 ring-secondary/30"
                          : doc.status === "missing"
                            ? "bg-destructive/10 ring-destructive/20"
                            : "bg-muted ring-transparent"
                      }`}
                    >
                      <span>
                        {docLabel(doc.kind, doc.name)} · {titleCase(doc.status)}
                      </span>
                      {canMark ? (
                        <button
                          type="button"
                          className="font-medium text-secondary underline-offset-2 hover:underline"
                          onClick={() =>
                            void run(
                              () =>
                                unwrap(
                                  browserApi.POST("/api/vendors/{vendor_id}/documents/{doc_id}/review", {
                                    params: { path: { vendor_id: shop.id, doc_id: doc.id } },
                                    body: { decision: "verified" },
                                  }),
                                ).then(() => onRefresh()),
                              "Document marked real",
                            )
                          }
                        >
                          Mark real
                        </button>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No documents yet.</p>
            )}
            {!docsReady && (isDraft || inReview) ? (
              <p className="text-xs text-muted-foreground">
                {readyDocs.length}/{docs.length || 0} ready. Missing uploads block review — attach samples to continue.
              </p>
            ) : null}
          </div>

          <div className="mt-auto flex flex-wrap gap-2 border-t border-border pt-4">
            {!docsReady && (isDraft || inReview) ? (
              <Button
                variant="outline"
                onClick={() =>
                  void run(
                    () => postVendor(`/api/vendors/${shop.id}/documents/sample`).then(() => onRefresh()),
                    "Sample documents attached",
                  )
                }
              >
                Attach sample documents
              </Button>
            ) : null}

            {isDraft ? (
              <Button
                onClick={() =>
                  void run(
                    () => postVendor(`/api/vendors/${shop.id}/accept`).then(() => onRefresh()),
                    "Shop is in review — mark documents next",
                  )
                }
                disabled={!docsReady}
              >
                1. Accept into review
              </Button>
            ) : null}

            {inReview ? (
              <Button
                onClick={() =>
                  void run(
                    () =>
                      unwrap(browserApi.POST("/api/vendors/{vendor_id}/verify", { params: { path: { vendor_id: shop.id } } })).then(() =>
                        onRefresh(),
                      ),
                    `${name} is live`,
                  )
                }
                disabled={!allDocsVerified}
              >
                {allDocsVerified ? "3. Verify shop" : "2. Mark all documents first"}
              </Button>
            ) : null}

            {inReview ? (
              <Button size="default" variant="outline" onClick={() => onReason({ id: shop.id, action: "reject", name })}>
                Reject
              </Button>
            ) : null}

            {shop.status === "active" && shop.allowed_actions.includes("suspend") ? (
              <Button variant="outline" onClick={() => onReason({ id: shop.id, action: "suspend", name })}>
                Suspend
              </Button>
            ) : null}

            {shop.status === "suspended" ? (
              <Button
                onClick={() =>
                  void run(
                    () =>
                      unwrap(
                        browserApi.POST("/api/vendors/{vendor_id}/reinstate", {
                          params: { path: { vendor_id: shop.id } },
                          body: { reason: "Reinstated after review" },
                        }),
                      ).then(() => onRefresh()),
                    "Shop reinstated",
                  )
                }
              >
                Reinstate
              </Button>
            ) : null}
          </div>
        </div>
      </div>
    </article>
  );
}
