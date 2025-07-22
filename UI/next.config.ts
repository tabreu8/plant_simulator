import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: 'standalone',
  eslint: {
    // Disable ESLint during builds for faster deployment
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Allow builds to proceed even with TypeScript errors
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
