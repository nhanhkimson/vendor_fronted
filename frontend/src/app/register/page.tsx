"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { ApiError, browserApi, unwrap } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
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
      toast.error(error instanceof ApiError ? error.message : "Could not create the account");
    }
  }

  return (
    <form className="wrap max-w-md space-y-3 py-10" onSubmit={(event) => void submit(event)}>
      <h1 className="serif text-5xl">Create an account</h1>
      <input required minLength={2} placeholder="Name" className="w-full rounded-xl border border-[#e2d8c8] px-3 py-2" value={name} onChange={(event) => setName(event.target.value)} />
      <input required type="email" placeholder="Email" className="w-full rounded-xl border border-[#e2d8c8] px-3 py-2" value={email} onChange={(event) => setEmail(event.target.value)} />
      <input required minLength={8} type="password" placeholder="Password" className="w-full rounded-xl border border-[#e2d8c8] px-3 py-2" value={password} onChange={(event) => setPassword(event.target.value)} />
      <input placeholder="City" className="w-full rounded-xl border border-[#e2d8c8] px-3 py-2" value={city} onChange={(event) => setCity(event.target.value)} />
      <button className="rounded-full bg-[#b8572a] px-4 py-2 text-white">Register</button>
    </form>
  );
}
