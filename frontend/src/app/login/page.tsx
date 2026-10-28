import { LoginForm } from "@/components/login-form";
import { serverApi, unwrap } from "@/lib/api";

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ next?: string; error?: string }> }) {
  const accounts = await unwrap(serverApi.GET("/api/auth/demo-accounts"));
  const params = await searchParams;
  return <LoginForm accounts={accounts} nextPath={params.next} failed={params.error === "1"} />;
}
