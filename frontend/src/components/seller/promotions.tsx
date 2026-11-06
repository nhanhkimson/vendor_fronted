"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { Field } from "@/components/flow";
import { StackSkeleton } from "@/components/skeletons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError, browserApi, unwrap } from "@/lib/api";
import { money, when } from "@/lib/format";

async function run(work: () => Promise<unknown>, ok: string) {
  try {
    await work();
    toast.success(ok);
  } catch (error) {
    toast.error(error instanceof ApiError ? error.message : "That did not work");
  }
}

export function SellerPromotions() {
  const queryClient = useQueryClient();
  const coupons = useQuery({
    queryKey: ["coupons", "seller"],
    queryFn: () => unwrap(browserApi.GET("/api/seller/coupons")),
  });
  const [code, setCode] = useState("");
  const [percent, setPercent] = useState("10");
  const [minSpend, setMinSpend] = useState("20");

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["coupons", "seller"] });
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="serif text-4xl">Discounts</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          After a product is live, create a shop coupon here. Buyers type the code at checkout. The discount comes out of your shop, not the platform.
        </p>
      </div>

      <form
        className="panel grid gap-4 p-5 sm:grid-cols-2"
        onSubmit={(event) => {
          event.preventDefault();
          const off = Number.parseInt(percent, 10);
          const min = Math.round(Number.parseFloat(minSpend) * 100);
          if (!code.trim() || !Number.isFinite(off) || off < 1 || off > 90) {
            toast.error("Use a code and a percent between 1 and 90");
            return;
          }
          const now = new Date();
          const end = new Date(now.getTime() + 60 * 24 * 3600 * 1000);
          void run(
            () =>
              unwrap(
                browserApi.POST("/api/seller/coupons", {
                  body: {
                    code: code.trim().toUpperCase(),
                    funded_by: "vendor",
                    discount_type: "percent",
                    percent_off: off,
                    min_subtotal_cents: Number.isFinite(min) ? Math.max(0, min) : 0,
                    starts_at: now.toISOString(),
                    ends_at: end.toISOString(),
                    per_customer_limit: 1,
                    is_flash: false,
                    note: `${off}% off this shop`,
                  },
                }),
              ).then(() => refresh()),
            "Discount is live",
          );
        }}
      >
        <Field id="code" label="Code buyers type">
          <Input id="code" value={code} onChange={(event) => setCode(event.target.value.toUpperCase())} placeholder="SHOP10" />
        </Field>
        <Field id="percent" label="Percent off">
          <Input id="percent" inputMode="numeric" value={percent} onChange={(event) => setPercent(event.target.value)} />
        </Field>
        <Field id="min" label="Minimum spend (USD)" hint="Optional. 0 means any order from your shop.">
          <Input id="min" inputMode="decimal" value={minSpend} onChange={(event) => setMinSpend(event.target.value)} />
        </Field>
        <div className="flex items-end">
          <Button type="submit" className="w-full">
            Create discount
          </Button>
        </div>
      </form>

      {coupons.isLoading ? <StackSkeleton rows={3} /> : null}
      {!coupons.isLoading && !coupons.data?.length ? (
        <p className="text-sm text-muted-foreground">No discounts yet. Create one when you want to run a sale.</p>
      ) : null}
      {coupons.data?.map((coupon) => (
        <article key={coupon.code} className="panel flex flex-wrap items-center justify-between gap-3 p-4">
          <div>
            <p className="font-medium">
              {coupon.code}{" "}
              <Badge variant={coupon.active ? "secondary" : "outline"}>{coupon.active ? "On" : "Paused"}</Badge>
            </p>
            <p className="text-sm text-muted-foreground">
              {coupon.summary} · used {coupon.used_count}
              {coupon.min_subtotal_cents ? ` · min ${money(coupon.min_subtotal_cents)}` : ""} · until {when(coupon.ends_at)}
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() =>
              void run(
                () =>
                  unwrap(
                    browserApi.PATCH("/api/seller/coupons/{code}", {
                      params: { path: { code: coupon.code } },
                      body: { active: !coupon.active },
                    }),
                  ).then(() => refresh()),
                coupon.active ? "Discount paused" : "Discount on again",
              )
            }
          >
            {coupon.active ? "Pause" : "Resume"}
          </Button>
        </article>
      ))}
    </div>
  );
}
