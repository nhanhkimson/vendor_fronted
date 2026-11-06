import { ApiError } from "@/lib/api";

export type RegisterStarted = {
  email: string;
  detail: string;
  expires_in_seconds: number;
  challenge_id: string;
  dev_code?: string | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("X-Bazaar-Client", "web");
  if (init?.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const response = await fetch(path, { ...init, headers, credentials: "include" });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof payload?.detail === "string" ? payload.detail : response.statusText || "Request failed";
    throw new ApiError(response.status, detail, payload?.code);
  }
  return payload as T;
}

export function startRegister(body: { name: string; email: string; password: string; city?: string }) {
  return request<RegisterStarted>("/api/auth/register", { method: "POST", body: JSON.stringify(body) });
}

export function verifyEmail(body: { email: string; code: string }) {
  return request<unknown>("/api/auth/verify-email", { method: "POST", body: JSON.stringify(body) });
}

export function resendOtp(email: string) {
  return request<RegisterStarted>("/api/auth/resend-otp", { method: "POST", body: JSON.stringify({ email }) });
}
