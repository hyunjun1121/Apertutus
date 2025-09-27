import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: "standalone",
  eslint: {
    // Docker 빌드 시 ESLint 에러를 무시
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Docker 빌드 시 TypeScript 에러를 무시
    ignoreBuildErrors: true,
  },
  experimental: {
    // outputFileTracingRoot은 더 이상 사용되지 않음
  },
};

export default nextConfig;
