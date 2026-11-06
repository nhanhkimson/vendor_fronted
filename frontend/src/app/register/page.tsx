"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { toast } from "sonner";

import { Field, FlowSteps } from "@/components/flow";
import { useSession } from "@/components/providers";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api";
import { resendOtp, startRegister, verifyEmail } from "@/lib/auth-api";

function RegisterForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { refresh } = useSession();
  const next = params.get("next") || "/";
  const selling = next.startsWith("/sell");
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
      toast.success("Check your email for the code");
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
      await refresh();
      toast.success("Email verified — you are signed in");
      router.push(selling ? "/sell" : next);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "That code did not work");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="wrap max-w-lg space-y-6 py-10">
      <FlowSteps
        steps={[{ label: "Details" }, { label: "Verify email" }, { label: selling ? "Open shop" : "Shop" }]}
        current={step === "details" ? 0 : 1}
      />

      {step === "details" ? (
        <form className="panel space-y-5 p-6" onSubmit={(event) => void submitDetails(event)}>
          <div>
            <h1 className="serif text-4xl">Create an account</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              We email a 6-digit code to verify you. After that you can buy and track orders.
            </p>
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
          <Button type="submit" disabled={busy} className="w-full">
            {busy ? "Sending code…" : "Send verification code"}
          </Button>
          <p className="text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href={`/login?next=${encodeURIComponent(selling ? "/sell" : next)}`} className="underline">
              Sign in
            </Link>
          </p>
        </form>
      ) : (
        <form className="panel space-y-5 p-6" onSubmit={(event) => void submitCode(event)}>
          <div>
            <h1 className="serif text-4xl">Enter your code</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Sent to <span className="text-foreground">{email}</span>. Codes expire in 15 minutes.
            </p>
          </div>
          {devCode ? (
            <div className="rounded-2xl bg-secondary/10 px-4 py-3 text-sm text-secondary">
              Demo inbox: your code is <span className="font-semibold tracking-widest">{devCode}</span>
            </div>
          ) : null}
          <Field id="code" label="6-digit code">
            <Input
              id="code"
              required
              inputMode="numeric"
              autoComplete="one-time-code"
              value={code}
              onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
              className="tracking-[0.35em]"
              placeholder="000000"
            />
          </Field>
          <Button type="submit" disabled={busy || code.length < 6} className="w-full">
            {busy ? "Verifying…" : "Verify and continue"}
          </Button>
          <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
            <button
              type="button"
              className="text-muted-foreground underline-offset-4 hover:underline"
              onClick={() => {
                void resendOtp(email)
                  .then((started) => {
                    setDevCode(started.dev_code || null);
                    toast.success("New code sent");
                  })
                  .catch((error: unknown) => toast.error(error instanceof ApiError ? error.message : "Could not resend"));
              }}
            >
              Resend code
            </button>
            <button type="button" className="text-muted-foreground underline-offset-4 hover:underline" onClick={() => setStep("details")}>
              Edit details
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense>
      <RegisterForm />
    </Suspense>
  );
}
