import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

import { Sidebar } from "@/components/layout/Sidebar";

export const metadata: Metadata = {
  title: "Real Estate ML Dashboard",
  description: "Predicting and understanding real estate prices in France",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="fr"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <Sidebar />
        <main className="flex-1 ml-64 min-h-screen">
          <div className="mx-auto max-w-7xl p-8">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
