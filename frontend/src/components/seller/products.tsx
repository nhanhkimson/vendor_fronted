"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { Records } from "@/components/records";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

export function SellerProducts() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<ListingProduct | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("24.00");
  const [stock, setStock] = useState("5");
  const [saving, setSaving] = useState(false);

  function resetForm(product?: ListingProduct | null) {
    setEditing(product || null);
    setTitle(product?.title || "");
    setDescription(product?.description || "");
    setPrice(product ? (product.price_cents / 100).toFixed(2) : "24.00");
    setStock("5");
  }

  function openCreate() {
    resetForm(null);
    setOpen(true);
  }

  function openEdit(product: ListingProduct) {
    resetForm(product);
    setOpen(true);
  }

  async function save() {
    const cents = Math.round(Number.parseFloat(price) * 100);
    if (!title.trim() || !Number.isFinite(cents) || cents <= 0) {
      toast.error("Enter a title and a valid price");
      return;
    }
    setSaving(true);
    await run(async () => {
      if (editing) {
        await updateProduct(editing.id, {
          title: title.trim(),
          description: description.trim(),
          price_cents: cents,
        });
      } else {
        const sku = `SKU-${Date.now().toString(36).toUpperCase()}`;
        await createProduct({
          title: title.trim(),
          description: description.trim(),
          price_cents: cents,
          variants: [{ sku, size: "One size", color: "Natural", stock: Math.max(0, Number.parseInt(stock, 10) || 0) }],
        });
      }
      setOpen(false);
      await queryClient.invalidateQueries({ queryKey: ["seller-products"] });
      await queryClient.invalidateQueries({ queryKey: ["summary", "seller"] });
    }, editing ? "Product updated" : "Draft product created");
    setSaving(false);
  }

  return (
    <Records
      title="Products"
      hint="Create drafts, set prices, then submit for staff review. Published title/price/description edits go back to review."
      queryKey={["seller-products"]}
      load={() => listSellerProducts()}
      actions={
        <>
          <Button onClick={openCreate}>New product</Button>
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetContent className="sm:max-w-md">
              <SheetHeader>
                <SheetTitle>{editing ? "Edit product" : "New product"}</SheetTitle>
                <SheetDescription>
                  {editing
                    ? "Saving material changes on a live listing may send it back to pending review."
                    : "Starts as a draft. Submit it when you are ready for staff approval."}
                </SheetDescription>
              </SheetHeader>
              <div className="mt-6 space-y-4 px-4">
                <div className="space-y-2">
                  <Label htmlFor="title">Title</Label>
                  <Input id="title" value={title} onChange={(event) => setTitle(event.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="price">Price (USD)</Label>
                  <Input id="price" inputMode="decimal" value={price} onChange={(event) => setPrice(event.target.value)} />
                </div>
                {!editing ? (
                  <div className="space-y-2">
                    <Label htmlFor="stock">Starting stock</Label>
                    <Input id="stock" inputMode="numeric" value={stock} onChange={(event) => setStock(event.target.value)} />
                  </div>
                ) : null}
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea id="description" value={description} onChange={(event) => setDescription(event.target.value)} rows={4} />
                </div>
              </div>
              <SheetFooter className="mt-6">
                <Button onClick={() => void save()} disabled={saving}>
                  {saving ? "Saving…" : editing ? "Save changes" : "Create draft"}
                </Button>
              </SheetFooter>
            </SheetContent>
          </Sheet>
        </>
      }
      columns={[
        { key: "title", label: "Title" },
        { key: "price", label: "Price", render: (row) => money(row.price_cents) },
        { key: "stock", label: "Available", render: (row) => String(row.available) },
        {
          key: "listing_status",
          label: "Listing",
          render: (row) => <Badge variant={statusVariant(row.listing_status)}>{titleCase(row.listing_status)}</Badge>,
        },
      ]}
      render={(row) => (
        <div className="flex flex-wrap justify-end gap-2">
          <Button size="sm" variant="outline" onClick={() => openEdit(row)}>
            Edit
          </Button>
          {row.listing_status === "draft" || row.listing_status === "rejected" ? (
            <Button
              size="sm"
              onClick={() =>
                void run(
                  () =>
                    submitListing(row.id).then(() => {
                      void queryClient.invalidateQueries({ queryKey: ["seller-products"] });
                      void queryClient.invalidateQueries({ queryKey: ["summary", "seller"] });
                    }),
                  "Submitted for review",
                )
              }
            >
              Submit
            </Button>
          ) : null}
        </div>
      )}
    />
  );
}
