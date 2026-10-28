"use client";

import { useI18n } from "@/lib/i18n";
import type { components } from "@/lib/api-types";

type Account = components["schemas"]["DemoAccount"];

export function LoginForm({ accounts, nextPath, failed }: { accounts: Account[]; nextPath?: string; failed?: boolean }) {
  const { t } = useI18n();
  return (
    <div className="wrap flex flex-col gap-8 py-10 lg:grid lg:grid-cols-[320px_1fr]">
      <div className="space-y-3 lg:col-start-2">
        <h2 className="serif text-3xl">{t.login.demoTitle}</h2>
        <p className="text-sm text-[#6b6258]">{t.login.demoIntro}</p>
        <div className="grid gap-3 sm:grid-cols-2">
          {accounts.map((account) => (
            <form key={account.email} action="/sign-in" method="post">
              <input type="hidden" name="email" value={account.email} />
              <input type="hidden" name="password" value={account.password} />
              {nextPath ? <input type="hidden" name="next" value={nextPath} /> : null}
              <button type="submit" className="panel w-full cursor-pointer p-4 text-left transition hover:border-[#24362c]">
                <p className="text-xs uppercase tracking-wide text-[#b8572a]">{account.role}</p>
                <p className="text-lg">{account.name}</p>
                <p className="text-sm">{account.email}</p>
                <p className="kh text-sm text-[#6b6258]">{account.blurb_kh}</p>
                <p className="mt-2 text-sm">{account.try_this}</p>
                <p className="mt-3 text-sm font-medium text-[#24362c]">{t.login.signIn}</p>
              </button>
            </form>
          ))}
        </div>
      </div>
      <form className="panel space-y-3 p-5 lg:col-start-1 lg:row-start-1" action="/sign-in" method="post">
        <h1 className="serif text-4xl">{t.login.title}</h1>
        {failed ? <p className="text-sm text-[#9f2d3a]">{t.login.failed}</p> : null}
        {nextPath ? <input type="hidden" name="next" value={nextPath} /> : null}
        <input name="email" className="w-full rounded-xl border border-[#e2d8c8] px-3 py-2" defaultValue="maya@bazaar.local" autoComplete="username" />
        <input name="password" className="w-full rounded-xl border border-[#e2d8c8] px-3 py-2" type="password" defaultValue="demo" autoComplete="current-password" />
        <button className="cursor-pointer rounded-full bg-[#24362c] px-4 py-2 text-[#f6efe3]">{t.login.continue}</button>
        <p className="text-sm text-[#6b6258]">
          {t.login.newHere} <a href="/register">{t.login.createAccount}</a>
        </p>
      </form>
    </div>
  );
}
