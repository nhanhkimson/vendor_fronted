"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { ApiError, browserApi, unwrap } from "@/lib/api";
import type { components } from "@/lib/api-types";
import { clearGuestCart, readGuestCart } from "@/lib/guest-cart";

type Account = components["schemas"]["DemoAccount"];

export function LoginForm({ accounts, nextPath }: { accounts: Account[]; nextPath?: string }) {
  const [email, setEmail] = useState("maya@bazaar.local");
  const [password, setPassword] = useState("demo");
  const router = useRouter();
  const queryClient = useQueryClient();

  async function signIn(nextEmail = email, nextPassword = password) {
    try {
      const me = await unwrap(browserApi.POST("/api/auth/login", { body: { email: nextEmail, password: nextPassword } }));
      const guest = readGuestCart();
      if (me.kind === "customer" && guest.length) {
        await unwrap(
          browserApi.POST("/api/cart/merge", {
            body: { items: guest.map((line) => ({ variant_id: line.variant_id, qty: line.qty })) },
          }),
        );
        clearGuestCart();
      }
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      router.push(nextPath || me.home);
      router.refresh();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Sign-in failed");
    }
  }

  return (
    <div className="wrap grid gap-8 py-10 lg:grid-cols-[320px_1fr]">
      <form
        className="panel space-y-3 p-5"
        onSubmit={(event) => {
          event.preventDefault();
          void signIn();
        }}
      >
        <h1 className="serif text-4xl">Sign in</h1>
        <input className="w-full rounded-xl border border-[#e2d8c8] px-3 py-2" value={email} onChange={(event) => setEmail(event.target.value)} />
        <input className="w-full rounded-xl border border-[#e2d8c8] px-3 py-2" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        <button className="rounded-full bg-[#24362c] px-4 py-2 text-[#f6efe3]">Continue</button>
        <p className="text-sm text-[#6b6258]">
          New here? <a href="/register">Create a customer account</a>
        </p>
      </form>
      <div className="space-y-3">
        <h2 className="serif text-3xl">Demo accounts</h2>
        <p className="text-sm text-[#6b6258]">Password for every account is demo. Click a card to sign in.</p>
        <div className="grid gap-3 md:grid-cols-2">
          {accounts.map((account) => (
            <button
              key={account.email}
              type="button"
              className="panel p-4 text-left"
              onClick={() => {
                setEmail(account.email);
                setPassword(account.password);
                void signIn(account.email, account.password);
              }}
            >
              <p className="text-xs uppercase tracking-wide text-[#b8572a]">{account.role}</p>
              <p className="text-lg">{account.name}</p>
              <p className="text-sm">{account.email}</p>
              <p className="kh text-sm text-[#6b6258]">{account.blurb_kh}</p>
              <p className="mt-2 text-sm">{account.try_this}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
