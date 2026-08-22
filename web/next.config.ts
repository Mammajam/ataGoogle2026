import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output is for Linux Cloud Run. Windows + pnpm cannot create
  // the required symlinks (EPERM) unless Developer Mode is on.
  output: process.env.DOCKER_BUILD === "1" || process.platform !== "win32" ? "standalone" : undefined,
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;
