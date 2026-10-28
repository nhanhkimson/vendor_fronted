import os from "os";
import type { NextConfig } from "next";

const api = process.env.API_URL || "http://127.0.0.1:8000";

function devOrigins() {
  const hosts = new Set(["127.0.0.1", "localhost"]);
  for (const entries of Object.values(os.networkInterfaces())) {
    for (const entry of entries ?? []) {
      const family = entry.family as string | number;
      if ((family === "IPv4" || family === 4) && !entry.internal) hosts.add(entry.address);
    }
  }
  return [...hosts];
}

const nextConfig: NextConfig = {
  // Live catalogue and dashboards read the API on each request.
  cacheComponents: false,
  allowedDevOrigins: devOrigins(),
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${api}/api/:path*` },
      { source: "/media/:path*", destination: `${api}/media/:path*` },
    ];
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
