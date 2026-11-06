"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Field, FlowSteps } from "@/components/flow";
import { useSession } from "@/components/providers";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api";
import { resendOtp, startRegister, verifyEmail } from "@/lib/auth-api";

const STEPS = [{ label: "Account" }, { label: "Shop" }, { label: "Add products" }];

export default function SellPage() {
  const { me, loading, refresh } = useSession();
  const current = me?.kind === "vendor" ? 2 : me ? 1 : 0;

  return (
    <div className="wrap max-w-xl space-y-8 py-10">
      <div className="space-y-3">
        <h1 className="serif text-5xl leading-none">Open a shop</h1>
        <p className="max-w-lg text-sm text-muted-foreground">
          Verify your email, name the shop, add a photo buyers will see, then wait for staff to publish.
        </p>
        <FlowSteps steps={STEPS} current={current} />
      </div>
      {loading ? (
        <div className="panel h-64 animate-pulse" />
      ) : me?.kind === "vendor" ? (
        <AlreadySelling name={me.vendor?.name || "your shop"} />
      ) : me?.kind === "platform" ? (
        <div className="panel space-y-4 p-6">
          <p>Staff review shops in Admin. You do not open a shop on this account.</p>
          <Button asChild size="lg">
            <Link href="/admin">Open Admin</Link>
          </Button>
        </div>
      ) : me ? (
        <ShopForm onReady={refresh} />
      ) : (
        <AccountForm onVerified={refresh} />
      )}
    </div>
  );
}

function AlreadySelling({ name }: { name: string }) {
  return (
    <div className="panel space-y-5 p-6">
      <div>
        <h2 className="text-xl font-medium">You already have a shop</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          You are selling as <b>{name}</b>. Next, add a product with a photo and price.
        </p>
      </div>
      <div className="dash-actions">
        <Button asChild size="lg">
          <Link href="/seller/products">Add a product</Link>
        </Button>
        <Button asChild variant="outline" size="lg">
          <Link href="/seller">Seller dashboard</Link>
        </Button>
      </div>
    </div>
  );
}

function AccountForm({ onVerified }: { onVerified: () => Promise<void> }) {
  const [step, setStep] = useState<"details" | "otp">("details");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [devCode, setDevCode] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submitDetails(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const started = await startRegister({ name, email, password, city: "Phnom Penh" });
      setDevCode(started.dev_code || null);
      setStep("otp");
      toast.success("Verification code sent");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Could not start registration");
    } finally {
      setBusy(false);
    }
  }

  async function submitCode(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await verifyEmail({ email, code: code.trim() });
      await onVerified();
      toast.success("Email verified — name your shop next");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "That code did not work");
    } finally {
      setBusy(false);
    }
  }

  if (step === "otp") {
    return (
      <form className="panel space-y-5 p-6" onSubmit={(event) => void submitCode(event)}>
        <div>
          <h2 className="text-xl font-medium">Verify your email</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Sent to <span className="text-foreground">{email}</span>. Then you can name the shop.
          </p>
        </div>
        {devCode ? (
          <div className="rounded-2xl bg-secondary/10 px-4 py-3 text-sm text-secondary">
            Demo inbox: code <span className="font-semibold tracking-widest">{devCode}</span>
          </div>
        ) : null}
        <Field id="otp" label="6-digit code">
          <Input
            id="otp"
            required
            inputMode="numeric"
            autoComplete="one-time-code"
            value={code}
            onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
            className="tracking-[0.35em]"
            placeholder="000000"
          />
        </Field>
        <Button type="submit" disabled={busy || code.length < 6} size="lg" className="w-full">
          {busy ? "Verifying…" : "Verify and continue"}
        </Button>
        <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
          <button
            type="button"
            className="text-muted-foreground underline-offset-4 hover:underline"
            onClick={() =>
              void resendOtp(email)
                .then((started) => {
                  setDevCode(started.dev_code || null);
                  toast.success("New code sent");
                })
                .catch((error: unknown) => toast.error(error instanceof ApiError ? error.message : "Could not resend"))
            }
          >
            Resend code
          </button>
          <button type="button" className="text-muted-foreground underline-offset-4 hover:underline" onClick={() => setStep("details")}>
            Edit details
          </button>
        </div>
      </form>
    );
  }

  return (
    <form className="panel space-y-5 p-6" onSubmit={(event) => void submitDetails(event)}>
      <div>
        <h2 className="text-xl font-medium">Create your seller account</h2>
        <p className="mt-1 text-sm text-muted-foreground">We email a code first. After that, name the shop on this page.</p>
      </div>
      <Field id="name" label="Your name">
        <Input id="name" required minLength={2} value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" />
      </Field>
      <Field id="email" label="Email">
        <Input id="email" required type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" />
      </Field>
      <Field id="password" label="Password" hint="At least 8 characters.">
        <Input
          id="password"
          required
          minLength={8}
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="new-password"
        />
      </Field>
      <Button type="submit" disabled={busy} size="lg" className="w-full">
        {busy ? "Sending code…" : "Send verification code"}
      </Button>
      <p className="text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login?next=/sell" className="underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}

function ShopForm({ onReady }: { onReady: () => Promise<void> }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [city, setCity] = useState("Phnom Penh");
  const [headline, setHeadline] = useState("");
  const [about, setAbout] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!photo) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(photo);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [photo]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!photo) {
      toast.error("Add a shop photo buyers will see on your storefront");
      return;
    }
    setBusy(true);
    const body = new FormData();
    body.set("name", name.trim());
    body.set("country", "KH");
    body.set("city", city.trim());
    body.set("headline", headline.trim());
    body.set("about", about.trim());
    body.set("shop_image", photo);
    try {
      const response = await fetch("/api/vendor-applications", {
        method: "POST",
        body,
        credentials: "include",
        headers: { "X-Bazaar-Client": "web" },
      });
      const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
      if (!response.ok) throw new ApiError(response.status, payload?.detail || "Could not register the shop");
      toast.success("Shop created. Add your first product.");
      await onReady();
      router.push("/seller/products");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Could not register the shop");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="panel space-y-5 p-6" onSubmit={(event) => void submit(event)}>
      <div>
        <h2 className="text-xl font-medium">Name your shop</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Buyers see the name and photo on your storefront. Staff verify the shop before it goes live.
        </p>
      </div>

      <Field id="shop-photo" label="Shop photo" hint="JPEG, PNG or WebP. Up to 5 MB. Shown as your storefront banner.">
        <Input
          id="shop-photo"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          required
          onChange={(event) => setPhoto(event.target.files?.[0] || null)}
        />
      </Field>
      {preview ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={preview} alt="" className="h-48 w-full rounded-2xl object-cover" />
      ) : (
        <div className="flex h-48 items-center justify-center rounded-2xl bg-muted text-sm text-muted-foreground">
          Photo preview
        </div>
      )}

      <Field id="shop-name" label="Shop name">
        <Input
          id="shop-name"
          required
          minLength={2}
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Jess Home Textiles"
        />
      </Field>
      <Field id="shop-city" label="City">
        <Input id="shop-city" required value={city} onChange={(event) => setCity(event.target.value)} />
      </Field>
      <Field id="shop-headline" label="One-line pitch" hint="Optional. Shown under your shop name.">
        <Input
          id="shop-headline"
          value={headline}
          onChange={(event) => setHeadline(event.target.value)}
          placeholder="Linen for the home"
        />
      </Field>
      <Field id="shop-about" label="About" hint="Optional. Tell buyers what you make.">
        <Textarea id="shop-about" value={about} onChange={(event) => setAbout(event.target.value)} rows={3} />
      </Field>
      <Button type="submit" disabled={busy} size="lg" className="w-full">
        {busy ? "Creating shop…" : "Create shop"}
      </Button>
    </form>
  );
}
