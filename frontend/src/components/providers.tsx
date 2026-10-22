"use client";

import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useContext, useState } from "react";
import { Toaster } from "sonner";

import { browserApi, unwrap } from "@/lib/api";
import type { components } from "@/lib/api-types";

export type Me = components["schemas"]["MeOut"];

const SessionContext = createContext<{ me: Me | null; loading: boolean; refresh: () => Promise<void> }>({
  me: null,
  loading: true,
  refresh: async () => {},
});

export function useSession() {
  return useContext(SessionContext);
}

function Session({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const result = await browserApi.GET("/api/auth/me");
      if (result.response.status === 401) return null;
      return unwrap(Promise.resolve(result));
    },
    retry: false,
  });
  return (
    <SessionContext.Provider
      value={{
        me: query.data ?? null,
        loading: query.isLoading,
        refresh: async () => {
          await queryClient.invalidateQueries({ queryKey: ["me"] });
        },
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient({ defaultOptions: { queries: { refetchOnWindowFocus: false } } }));
  return (
    <QueryClientProvider client={client}>
      <Session>{children}</Session>
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  );
}
