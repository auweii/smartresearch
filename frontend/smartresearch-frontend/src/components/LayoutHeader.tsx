"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function LayoutHeader() {
  const pathname = usePathname();

  const nav = [
    { href: "/", label: "Upload" },
    { href: "/cluster", label: "Cluster" },
    { href: "/export", label: "Export" },
  ];

  return (
    <header className="topbar">
      <div className="brand">SmartResearch</div>
      <nav className="nav">
        {nav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`navitem ${pathname === item.href ? "active" : ""}`}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <style jsx>{`
        .topbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 20px;
          background: #2b2d31;
          color: #fff;
        }
        .brand {
          font-weight: 700;
          font-size: 18px;
        }
        .nav {
          display: flex;
          gap: 20px;
        }
        .navitem {
          opacity: 0.7;
          text-decoration: none;
          color: #fff;
          font-weight: 500;
        }
        .navitem.active {
          opacity: 1;
          border-bottom: 2px solid #c9b39a;
          padding-bottom: 2px;
        }
        .navitem:hover {
          opacity: 1;
        }
      `}</style>
    </header>
  );
}
