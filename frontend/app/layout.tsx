import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "ShortForge AI — Cinematic Shorts Production Studio",
  description: "Automated Minecraft and Geography 3D Animated Shorts Production Platform."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="app-header">
          <Link href="/dashboard" className="nav-brand">
            <span>⚡ SHORTFORGE AI</span>
            <span className="nav-brand-badge">STUDIO</span>
          </Link>
          <nav className="nav-links">
            <Link href="/dashboard" className="nav-link">Dashboard</Link>
            <Link href="/minecraft" className="nav-link">Minecraft</Link>
            <Link href="/minecraft/create" className="nav-link">Create Story</Link>
            <Link href="/minecraft/characters" className="nav-link">Characters</Link>
            <Link href="/" className="nav-link">Geography</Link>
            <Link href="/renders" className="nav-link">Render Queue</Link>
            <Link href="/projects" className="nav-link">Projects</Link>
            <Link href="/settings" className="nav-link">Settings</Link>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
