import type { Metadata } from "next";
import { Open_Sans } from "next/font/google";
import "./globals.css";

const openSans = Open_Sans({
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "GreenChain — GHG close",
  description:
    "A Collaborative Partner that drafts a GHG inventory from mixed evidence, then asks only at material gaps.",
  openGraph: {
    title: "GreenChain — GHG close",
    description:
      "A Collaborative Partner that drafts a GHG inventory from mixed evidence, then asks only at material gaps.",
    images: ["/og.png"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={openSans.className}>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
