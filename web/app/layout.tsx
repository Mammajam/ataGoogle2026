import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GreenChain — GHG close",
  description:
    "A Collaborative Partner that drafts a GHG inventory from mixed evidence, then asks only at material gaps.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
