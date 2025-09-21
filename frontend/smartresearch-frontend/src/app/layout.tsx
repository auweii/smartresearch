import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "SmartResearch",
  description: "Upload and cluster research PDFs",
};

function Header() {
  return (
    <div className="topbar">
      <div className="topbar-inner">
        <div className="brand">SmartResearch</div>
        <nav className="nav">
          <Link href="/">Upload</Link>
          <Link href="/cluster">Cluster</Link>
          <Link href="/export">Export</Link>
        </nav>
      </div>
    </div>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main className="page">{children}</main>
      </body>
    </html>
  );
}
