"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { ApiError, browserApi, unwrap } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function RegisterPage() {
  const router = useRouter();
  const { t } = useI18n();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [city, setCity] = useState("Phnom Penh");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    try {
      await unwrap(browserApi.POST("/api/auth/register", { body: { name, email, password, city } }));
      router.push("/account");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : t.register.failed);
    }
  }

  return (
    <form className="wrap max-w-md space-y-3 py-10" onSubmit={(event) => void submit(event)}>
      <h1 className="serif text-5xl">{t.register.title}</h1>
      <input required minLength={2} placeholder={t.register.name} className="w-full rounded-xl border border-[#e2d8c8] px-3 py-2" value={name} onChange={(event) => setName(event.target.value)} />
      <input required type="email" placeholder={t.register.email} className="w-full rounded-xl border border-[#e2d8c8] px-3 py-2" value={email} onChange={(event) => setEmail(event.target.value)} />
      <input required minLength={8} type="password" placeholder={t.register.password} className="w-full rounded-xl border border-[#e2d8c8] px-3 py-2" value={password} onChange={(event) => setPassword(event.target.value)} />
      <input placeholder={t.register.city} className="w-full rounded-xl border border-[#e2d8c8] px-3 py-2" value={city} onChange={(event) => setCity(event.target.value)} />
      <button className="rounded-full bg-[#b8572a] px-4 py-2 text-white">{t.register.submit}</button>
    </form>
  );
}