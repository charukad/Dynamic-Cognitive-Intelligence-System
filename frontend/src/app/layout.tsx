import type { Metadata } from "next";
import { Geist, Geist_Mono, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Providers from "@/components/providers";
import { SwarmCanvas } from "@/components/orbit/Canvas";
import { Toaster } from "sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "DCIS | Neural Command",
  description: "Distributed Collective Intelligence System Interface",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className={`${geistSans.variable} ${geistMono.variable} ${jetbrainsMono.variable} antialiased bg-[#000000] text-foreground overflow-hidden`}
      >
        <Providers>
          <div className="flex h-screen w-screen bg-black">
            {/* Optional: Add a subtle ambient background if requested later, but keeping it simple black for now */}
            {children}
          </div>
          <Toaster richColors position="top-right" />
        </Providers>
      </body>
    </html>
  );
}

