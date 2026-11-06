"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Field } from "@/components/flow";
import { StackSkeleton } from "@/components/skeletons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api";
import { money, titleCase } from "@/lib/format";
import {
  createProduct,
  listSellerProducts,
  submitListing,
  updateProduct,
  uploadProductImage,
  type ListingProduct,
} from "@/lib/listing-api";

async function run(work: () => Promise<unknown>, ok: string) {
  try {
    await work();
    toast.success(ok);
  } catch (error) {
    toast.error(error instanceof ApiError ? error.message : "That did not work");
  }
}

function statusVariant(status: string): "default" | "secondary" | "outline" | "destructive" {
  if (status === "published") return "default";
  if (status === "pending_review") return "secondary";
  if (status === "rejected") return "destructive";
  return "outline";
}

function statusLabel(status: string) {
  if (status === "pending_review") return "In review";
  if (status === "published") return "Live";
  return titleCase(status);
}

type Filter = "all" | "draft" | "pending_review" | "published" | "rejected";

export function SellerProducts() {
  const queryClient = useQueryClient();
  const products = useQuery({ queryKey: ["seller-products"], queryFn: () => listSellerProducts() });
  const [filter, setFilter] = useState<Filter>("all");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<ListingProduct | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("24.00");
  const [stock, setStock] = useState("5");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const rows = products.data || [];
  const counts = useMemo(() => {
    const next = { all: rows.length, draft: 0, pending_review: 0, published: 0, rejected: 0 };
    for (const row of rows) {
      if (row.listing_status in next) next[row.listing_status as keyof typeof next] += 1;
    }
    return next;
  }, [rows]);
  const shown = filter === "all" ? rows : rows.filter((row) => row.listing_status === filter);

  function resetForm(product?: ListingProduct | null) {
    setEditing(product || null);
    setTitle(product?.title || "");
    setDescription(product?.description || "");
    setPrice(product ? (product.price_cents / 100).toFixed(2) : "24.00");
    setStock("5");
    setFile(null);
    setPreview(product?.image_url || null);
  }

  function openCreate() {
    resetForm(null);
    setOpen(true);
  }

  function openEdit(product: ListingProduct) {
    resetForm(product);
    setOpen(true);
  }

  function onFile(next: File | null) {
    setFile(next);
    setPreview(next ? URL.createObjectURL(next) : editing?.image_url || null);
  }

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["seller-products"] });
    await queryClient.invalidateQueries({ queryKey: ["summary", "seller"] });
  }

  async function save(submit: boolean) {
    const cents = Math.round(Number.parseFloat(price) * 100);
    if (!title.trim() || title.trim().length < 3 || !Number.isFinite(cents) || cents <= 0) {
      toast.error("Enter a title and a valid price");
      return;
    }
    if (!description.trim()) {
      toast.error("Add a short description buyers will read");
      return;
    }
    if (submit && !file && !editing?.image_url) {
      toast.error("Add a product photo before sending for review");
      return;
    }
    setSaving(true);
    await run(async () => {
      let product = editing;
      if (editing) {
        product = await updateProduct(editing.id, {
          title: title.trim(),
          description: description.trim(),
          price_cents: cents,
        });
      } else {
        const sku = `SKU-${Date.now().toString(36).toUpperCase()}`;
        product = await createProduct({
          title: title.trim(),
          description: description.trim(),
          price_cents: cents,
          variants: [{ sku, size: "One size", color: "Natural", stock: Math.max(0, Number.parseInt(stock, 10) || 0) }],
        });
      }
      if (file && product) {
        product = await uploadProductImage(product.id, file);
      }
      if (submit && product && (product.listing_status === "draft" || product.listing_status === "rejected")) {
        await submitListing(product.id);
      }
      setOpen(false);
      await refresh();
    }, submit ? "Sent for review" : editing ? "Product updated" : "Draft saved");
    setSaving(false);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="max-w-xl space-y-1">
          <p className="text-[11px] uppercase tracking-[0.16em] text-secondary">Catalogue</p>
          <h1 className="serif text-4xl">Products</h1>
          <p className="text-sm text-muted-foreground">
            Photo, description, and price first. Staff publish. Discounts live in your Discounts menu.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link href="/seller">Overview</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/seller/promotions">Discounts</Link>
          </Button>
          <Button onClick={openCreate}>New product</Button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {(
          [
            ["all", "All"],
            ["draft", "Drafts"],
            ["pending_review", "In review"],
            ["published", "Live"],
            ["rejected", "Rejected"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setFilter(id)}
            className={`rounded-full px-4 py-2 text-sm transition ${
              filter === id ? "bg-primary text-primary-foreground" : "bg-card ring-1 ring-border hover:ring-primary"
            }`}
          >
            {label}
            <span className="ml-2 opacity-70">{counts[id]}</span>
          </button>
        ))}
      </div>

      {products.isLoading ? <StackSkeleton rows={4} /> : null}
      {!products.isLoading && !shown.length ? (
        <div className="panel space-y-3 p-10 text-center">
          <p className="serif text-3xl">No products here</p>
          <p className="text-sm text-muted-foreground">Add a listing with a photo, description, and price.</p>
          <Button onClick={openCreate}>New product</Button>
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {shown.map((row) => (
          <article key={row.id} className="panel overflow-hidden">
            <div className="relative aspect-[4/3] bg-muted">
              {row.image_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={row.image_url} alt="" className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">No photo</div>
              )}
              <Badge className="absolute left-3 top-3" variant={statusVariant(row.listing_status)}>
                {statusLabel(row.listing_status)}
              </Badge>
            </div>
            <div className="space-y-3 p-4">
              <div>
                <h2 className="line-clamp-2 font-medium leading-snug">{row.title}</h2>
                {row.listing_reason && row.listing_status === "rejected" ? (
                  <p className="mt-1 text-xs text-destructive">{row.listing_reason}</p>
                ) : row.description ? (
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{row.description}</p>
                ) : null}
              </div>
              <div className="flex items-end justify-between gap-3">
                <span className="price price-md">{money(row.price_cents)}</span>
                <span className="text-sm text-muted-foreground">{row.available} in stock</span>
              </div>
              <div className="dash-actions border-t border-border pt-3">
                <Button variant="outline" onClick={() => openEdit(row)}>
                  Edit
                </Button>
                {row.listing_status === "draft" || row.listing_status === "rejected" ? (
                  <Button
                    onClick={() => {
                      if (!row.image_url) {
                        toast.error("Add a product photo first");
                        openEdit(row);
                        return;
                      }
                      void run(() => submitListing(row.id).then(() => refresh()), "Submitted for review");
                    }}
                  >
                    Send for review
                  </Button>
                ) : null}
                {row.listing_status === "published" ? (
                  <Button variant="outline" asChild>
                    <Link href="/seller/promotions">Discount</Link>
                  </Button>
                ) : null}
              </div>
            </div>
          </article>
        ))}
      </div>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent className="sm:max-w-md">
          <SheetHeader>
            <SheetTitle>{editing ? "Edit product" : "New product"}</SheetTitle>
            <SheetDescription>Buyers see the photo, title, description, and price. Staff approve the first publish.</SheetDescription>
          </SheetHeader>
          <div className="mt-6 space-y-4 px-4">
            <Field id="photo" label="Photo" hint="JPEG, PNG or WebP. Up to 5 MB.">
              <Input id="photo" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => onFile(event.target.files?.[0] || null)} />
            </Field>
            {preview ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={preview} alt="" className="h-40 w-full rounded-xl object-cover" />
            ) : (
              <div className="flex h-40 items-center justify-center rounded-xl bg-muted text-sm text-muted-foreground">No photo yet</div>
            )}
            <Field id="title" label="Title">
              <Input id="title" value={title} onChange={(event) => setTitle(event.target.value)} required minLength={3} />
            </Field>
            <Field id="price" label="Price (USD)">
              <Input id="price" inputMode="decimal" value={price} onChange={(event) => setPrice(event.target.value)} />
            </Field>
            {!editing ? (
              <Field id="stock" label="Starting stock">
                <Input id="stock" inputMode="numeric" value={stock} onChange={(event) => setStock(event.target.value)} />
              </Field>
            ) : null}
            <Field id="description" label="Description" hint="What is it, size, and what it is made of.">
              <Textarea id="description" value={description} onChange={(event) => setDescription(event.target.value)} rows={4} />
            </Field>
          </div>
          <SheetFooter className="mt-6 flex-col gap-2 sm:flex-col">
            <Button onClick={() => void save(false)} disabled={saving} className="w-full">
              {saving ? "Saving…" : "Save"}
            </Button>
            {!editing || editing.listing_status === "draft" || editing.listing_status === "rejected" ? (
              <Button variant="outline" onClick={() => void save(true)} disabled={saving} className="w-full">
                Save and send for review
              </Button>
            ) : null}
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
  );
}
