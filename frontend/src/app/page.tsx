import { HomeView } from "@/components/storefront";
import { serverApi, unwrap } from "@/lib/api";

export default async function HomePage() {
  const home = await unwrap(serverApi.GET("/api/store/home"));
  return <HomeView home={home} />;
}
