import type { NextConfig } from "next";

const api = process.env.API_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Live catalogue and dashboards read the API on each request.
  cacheComponents: false,
  allowedDevOrigins: ["127.0.0.1", "localhost"],
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
