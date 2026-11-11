"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { components } from "@/lib/api-types";

type Account = components["schemas"]["DemoAccount"];

const ROLES: {
  id: string;
  title: string;
  lands: string;
  does: string;
  roles: string[];
  email: string;
}[] = [
  {
    id: "customer",
    title: "Customer",
    lands: "Shop and cart",
    does: "Browse listings, pay, track a parcel.",
    roles: ["customer"],
    email: "theo@mail.local",
  },
  {
    id: "seller",
    title: "Seller",
    lands: "Seller dashboard",
    does: "Add products, set discounts, ship orders.",
    roles: ["vendor"],
    email: "jess@annescraftworks.local",
  },
  {
    id: "staff",
    title: "Staff",
    lands: "Staff console",
    does: "Verify shops and publish products.",
    roles: ["admin", "support"],
    email: "ava@bazaar.local",
  },
  {
    id: "owner",
    title: "Owner",
    lands: "Owner console",
    does: "Growth, revenue, and permissions.",
    roles: ["super_admin"],
    email: "daniel@bazaar.local",
  },
];

function roleId(account: Account) {
  return account.role_id || account.role;
}

function AutoEnter({
  account,
  nextPath,
  label,
  hint,
}: {
  account: Account;
  nextPath?: string;
  label: string;
  hint: string;
}) {
  return (
    <form action="/sign-in" method="post" className="contents">
      <input type="hidden" name="email" value={account.email} />
      <input type="hidden" name="password" value={account.password} />
      {nextPath ? <input type="hidden" name="next" value={nextPath} /> : null}
      <button
        type="submit"
        className="panel group flex w-full items-center justify-between gap-4 p-5 text-left transition hover:border-primary"
      >
        <span>
          <span className="text-[11px] uppercase tracking-[0.16em] text-secondary">{label}</span>
          <span className="mt-1 block serif text-3xl leading-none">{account.name}</span>
          <span className="mt-2 block text-sm text-muted-foreground">{hint}</span>
        </span>
        <span className="shrink-0 rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground group-hover:bg-secondary">
          Enter
        </span>
      </button>
    </form>
  );
}

export function LoginForm({ accounts, nextPath, failed }: { accounts: Account[]; nextPath?: string; failed?: boolean }) {
  const [manual, setManual] = useState(false);

  return (
    <div className="wrap max-w-2xl space-y-8 py-10">
      <div className="space-y-2">
        <h1 className="serif text-5xl">Sign in</h1>
        <p className="text-muted-foreground">
          One click. Password is already set to <span className="font-medium text-foreground">demo</span>.
          {nextPath ? " You will return to checkout after." : ""}
        </p>
        {failed ? (
          <p className="text-sm text-destructive">
            That sign-in did not work. Try another role, or{" "}
            <Link href={`/register${nextPath ? `?next=${encodeURIComponent(nextPath)}` : ""}`} className="underline">
              create an account
            </Link>
            . Unverified emails are sent to the OTP step automatically.
          </p>
        ) : null}
      </div>

      <div className="space-y-3">
        {ROLES.map((role) => {
          const account =
            accounts.find((item) => item.email === role.email) ||
            accounts.find((item) => role.roles.includes(roleId(item)));
          if (!account) return null;
          return (
            <AutoEnter
              key={role.id}
              account={account}
              nextPath={nextPath}
              label={`${role.title} · ${role.lands}`}
              hint={role.does}
            />
          );
        })}
      </div>

      <div className="space-y-3">
        <button
          type="button"
          className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
          onClick={() => setManual((open) => !open)}
        >
          {manual ? "Hide email form" : "Use another email"}
        </button>
        {manual ? (
          <form className="panel space-y-4 p-5" action="/sign-in" method="post">
            {nextPath ? <input type="hidden" name="next" value={nextPath} /> : null}
            <div className="space-y-2">
              <Label htmlFor="manual-email">Email</Label>
              <Input id="manual-email" name="email" type="email" autoComplete="username" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="manual-password">Password</Label>
              <Input id="manual-password" name="password" type="password" defaultValue="demo" autoComplete="current-password" />
            </div>
            <Button type="submit" className="w-full">
              Continue
            </Button>
          </form>
        ) : null}
        <p className="text-sm text-muted-foreground">
          New customer?{" "}
          <Link className="underline" href={`/register${nextPath ? `?next=${encodeURIComponent(nextPath)}` : ""}`}>
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
