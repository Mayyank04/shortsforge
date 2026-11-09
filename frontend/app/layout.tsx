import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "ShortForge AI", description: "Create animated faceless Shorts locally." };
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body>{children}</body></html>;
}
