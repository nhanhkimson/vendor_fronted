import createClient, { type Client } from "openapi-fetch";

import type { paths } from "./api-types";

const API_URL = process.env.API_URL || "http://127.0.0.1:8000";

function clientFetch(request: Request): Promise<Response> {
  const headers = new Headers(request.headers);
  headers.set("X-Bazaar-Client", "web");
  return fetch(new Request(request, { headers, credentials: "include" }));
}

export const browserApi: Client<paths> = createClient<paths>({
  baseUrl: "",
  fetch: clientFetch,
});

export const serverApi: Client<paths> = createClient<paths>({
  baseUrl: API_URL,
  fetch: (request) => fetch(new Request(request, { cache: "no-store" })),
});

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(status: number, detail: string, code?: string) {
    super(detail);
    this.status = status;
    this.code = code;
  }
}

export async function unwrap<T>(pending: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  const result = await pending;
  if (!result.response.ok) {
    const error = result.error as { detail?: unknown; code?: string } | undefined;
    const detail = typeof error?.detail === "string" ? error.detail : result.response.statusText || "Request failed";
    throw new ApiError(result.response.status, detail, error?.code);
  }
  return result.data as T;
}
