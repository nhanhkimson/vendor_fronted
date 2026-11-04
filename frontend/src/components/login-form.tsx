"use client";

import { useMemo, useState } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useI18n } from "@/lib/i18n";
import type { components } from "@/lib/api-types";

type Account = components["schemas"]["DemoAccount"];

const ROLE_ORDER = ["customer", "vendor", "admin", "support", "super_admin"] as const;

type RoleId = (typeof ROLE_ORDER)[number];

function isRoleId(value: string): value is RoleId {
  return ROLE_ORDER.includes(value as RoleId);
}

function accountRoleId(account: Account): RoleId | null {
  if (isRoleId(account.role_id)) return account.role_id;
  if (isRoleId(account.role)) return account.role;
  return null;
}

export function LoginForm({ accounts, nextPath, failed }: { accounts: Account[]; nextPath?: string; failed?: boolean }) {
  const { t } = useI18n();
  const roles = useMemo(() => {
    const present = new Set(
      accounts.map((account) => accountRoleId(account)).filter((id): id is RoleId => id !== null),
    );
    return ROLE_ORDER.filter((role) => present.has(role));
  }, [accounts]);

  const [role, setRole] = useState<RoleId>(() => roles[0] || "customer");
  const roleAccounts = useMemo(
    () => accounts.filter((account) => accountRoleId(account) === role),
    [accounts, role],
  );
  const [email, setEmail] = useState(() => roleAccounts[0]?.email || accounts[0]?.email || "");

  const selected = roleAccounts.find((account) => account.email === email) || roleAccounts[0] || null;
  const roleCopy = t.login.roles[role];
  const passwordHint = t.login.passwordHint.replace("{password}", selected?.password || "demo");

  function onRoleChange(nextRole: string) {
    if (!isRoleId(nextRole)) return;
    setRole(nextRole);
    const first = accounts.find((account) => accountRoleId(account) === nextRole);
    if (first) setEmail(first.email);
  }

  return (
    <div className="wrap grid gap-8 py-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)] lg:items-start">
      <Card>
        <CardHeader>
          <p className="text-xs uppercase tracking-[0.18em] text-primary">{t.login.eyebrow}</p>
          <CardTitle className="serif text-4xl leading-tight font-normal">{t.login.title}</CardTitle>
          <CardDescription className="text-sm leading-relaxed">{t.login.intro}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {failed ? (
            <Alert variant="destructive">
              <AlertTitle>{t.login.failed}</AlertTitle>
              <AlertDescription>Check the role and account, then try again.</AlertDescription>
            </Alert>
          ) : null}

          <div className="space-y-2">
            <Label htmlFor="role">{t.login.chooseRole}</Label>
            <Select value={role} onValueChange={onRoleChange}>
              <SelectTrigger id="role" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {roles.map((id) => (
                  <SelectItem key={id} value={id}>
                    {t.login.roles[id].label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Card size="sm" className="bg-muted ring-1 ring-border">
            <CardHeader>
              <p className="text-xs uppercase tracking-wide text-secondary">{t.login.canDo}</p>
              <CardTitle>{roleCopy.label}</CardTitle>
              <CardDescription>{roleCopy.summary}</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {roleCopy.capabilities.map((item) => (
                  <li key={item} className="flex gap-2 text-sm leading-snug text-foreground">
                    <span aria-hidden className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-secondary" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-muted-foreground">
                {t.login.landsAt}: {roleCopy.home}
              </p>
            </CardContent>
          </Card>

          <form className="space-y-4" action="/sign-in" method="post">
            {nextPath ? <input type="hidden" name="next" value={nextPath} /> : null}
            <input type="hidden" name="password" value={selected?.password || "demo"} />
            <input type="hidden" name="email" value={selected?.email || ""} />

            <div className="space-y-2">
              <Label htmlFor="account">{t.login.chooseAccount}</Label>
              <Select value={selected?.email || ""} onValueChange={setEmail} disabled={roleAccounts.length === 0}>
                <SelectTrigger id="account" className="w-full">
                  <SelectValue placeholder={t.login.noAccounts} />
                </SelectTrigger>
                <SelectContent>
                  {roleAccounts.map((account) => (
                    <SelectItem key={account.email} value={account.email}>
                      {account.name} · {account.email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selected ? (
              <Alert>
                <AlertTitle>{selected.name}</AlertTitle>
                <AlertDescription>
                  <p>{selected.try_this}</p>
                  <p className="mt-2 text-xs uppercase tracking-wide text-primary">{passwordHint}</p>
                </AlertDescription>
              </Alert>
            ) : null}

            <Button type="submit" className="w-full" disabled={!selected}>
              {selected ? t.login.signInAs.replace("{name}", selected.name) : t.login.signIn}
            </Button>
          </form>
        </CardContent>
      </Card>

      <section className="space-y-5">
        <div className="space-y-2">
          <h2 className="serif text-3xl text-foreground">{t.login.demoTitle}</h2>
          <p className="text-sm leading-relaxed text-muted-foreground">{t.login.demoIntro}</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {roleAccounts.map((account) => {
            const id = accountRoleId(account) || role;
            const isSelected = selected?.email === account.email;
            return (
              <form key={account.email} action="/sign-in" method="post">
                <input type="hidden" name="email" value={account.email} />
                <input type="hidden" name="password" value={account.password} />
                {nextPath ? <input type="hidden" name="next" value={nextPath} /> : null}
                <Button
                  type="submit"
                  variant="outline"
                  className={`h-auto w-full flex-col items-start gap-1 whitespace-normal p-4 text-left ${
                    isSelected ? "border-primary ring-1 ring-primary/20" : ""
                  }`}
                  onClick={() => setEmail(account.email)}
                >
                  <span className="text-xs uppercase tracking-wide text-primary">{t.login.roles[id].label}</span>
                  <span className="text-lg text-foreground">{account.name}</span>
                  <span className="text-sm text-muted-foreground">{account.email}</span>
                  <span className="mt-1 text-sm leading-snug text-foreground">{account.try_this}</span>
                  <span className="mt-2 text-sm font-medium text-primary">{t.login.signIn}</span>
                </Button>
              </form>
            );
          })}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{t.login.manualTitle}</CardTitle>
            <CardDescription>{t.login.manualIntro}</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-3" action="/sign-in" method="post">
              {nextPath ? <input type="hidden" name="next" value={nextPath} /> : null}
              <div className="space-y-2">
                <Label htmlFor="manual-email">{t.login.email}</Label>
                <Input
                  id="manual-email"
                  name="email"
                  type="email"
                  defaultValue={selected?.email || "maya@bazaar.local"}
                  autoComplete="username"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="manual-password">{t.login.password}</Label>
                <Input id="manual-password" name="password" type="password" defaultValue="demo" autoComplete="current-password" />
              </div>
              <Button type="submit" variant="secondary">
                {t.login.continue}
              </Button>
              <p className="text-sm text-muted-foreground">
                {t.login.newHere}{" "}
                <a className="underline decoration-border underline-offset-2 hover:text-foreground" href="/register">
                  {t.login.createAccount}
                </a>
              </p>
            </form>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
