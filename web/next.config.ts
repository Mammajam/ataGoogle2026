import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone is Docker/Cloud Run only. Vercel (and local `pnpm build`) must
  // use the default Next.js output so the platform can bundle functions.
  output: process.env.DOCKER_BUILD === "1" ? "standalone" : undefined,
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;
