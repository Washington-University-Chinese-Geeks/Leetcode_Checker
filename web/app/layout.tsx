import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "WUCG LeetCode Dashboard",
  description:
    "Daily-updated LeetCode progress dashboard for WUCG members. Collected by GitHub Actions, served from GitHub Pages.",
};

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <Link href="/" className="brand">
            WUCG LeetCode
          </Link>
          <nav>
            <Link href="/">Roster</Link>
          </nav>
        </header>
        <main className="site-main">{children}</main>
        <footer className="site-footer">
          <span>
            Static dashboard built with Next.js. Data collected daily via GitHub
            Actions.
          </span>
          {basePath && <span> · Base path: {basePath}</span>}
        </footer>
      </body>
    </html>
  );
}
