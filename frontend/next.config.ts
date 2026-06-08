import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/auth/:path*",
        destination: "http://api:8000/auth/:path*",
      },
      {
        source: "/api/:path*",
        destination: "http://api:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
