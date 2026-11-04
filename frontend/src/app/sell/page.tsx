"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { useSession } from "@/components/providers";
import { ApiError } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function SellPage() {
  const { me } = useSession();
  const { t } = useI18n();
  const router = useRouter();
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [headline, setHeadline] = useState("");
  const [about, setAbout] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const body = new FormData();
    body.set("name", name);
    body.set("country", "US");
    body.set("city", city);
    body.set("headline", headline);
    body.set("about", about);
    try {
      const response = await fetch("/api/vendor-applications", {
        method: "POST",
        body,
        credentials: "include",
        headers: { "X-Bazaar-Client": "web" },
      });
      const payload = (await response.json()) as { detail?: string; home?: string };
      if (!response.ok) throw new ApiError(response.status, payload.detail || t.sell.failed);
      toast.success(t.sell.success);
      router.push("/seller");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : t.sell.failed);
    }
  }

  return (
    <div className="wrap max-w-xl space-y-4 py-10">
      <h1 className="serif text-5xl">{t.sell.title}</h1>
      <p className="text-muted-foreground">{t.sell.intro}</p>
      {!me ? <p>{t.sell.signInFirst}</p> : null}
      <form className="space-y-3" onSubmit={(event) => void submit(event)}>
        <input required placeholder={t.sell.shopName} className="w-full rounded-xl border border-border bg-background px-3 py-2 text-foreground" value={name} onChange={(event) => setName(event.target.value)} />
        <input placeholder={t.sell.city} className="w-full rounded-xl border border-border bg-background px-3 py-2 text-foreground" value={city} onChange={(event) => setCity(event.target.value)} />
        <input placeholder={t.sell.headline} className="w-full rounded-xl border border-border bg-background px-3 py-2 text-foreground" value={headline} onChange={(event) => setHeadline(event.target.value)} />
        <textarea placeholder={t.sell.about} className="w-full rounded-xl border border-border bg-background px-3 py-2 text-foreground" value={about} onChange={(event) => setAbout(event.target.value)} />
        <button className="rounded-full bg-primary px-4 py-2 text-primary-foreground" disabled={!me}>
          {t.sell.open}
        </button>
      </form>
      <p className="text-sm text-muted-foreground">{t.sell.staffNote}</p>
    </div>
  );
}
