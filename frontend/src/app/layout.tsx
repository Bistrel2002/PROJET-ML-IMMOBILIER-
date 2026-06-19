import type { Metadata } from "next";
import "./globals.css";
import { Inter } from "next/font/google";
import { Sidebar } from "@/components/layout/Sidebar";

// P7: Use next/font for optimal font loading (no render-blocking link tag)
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

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
    <html lang="fr" className={`h-full antialiased dark ${inter.variable}`}>
      <body className="min-h-full flex flex-col bg-background text-foreground font-sans">
        <Sidebar />
        {/* B13: responsive margin — no left margin on mobile, ml-64 on lg+ */}
        <main className="flex-1 lg:ml-64 min-h-screen">
          <div className="mx-auto max-w-7xl p-4 pt-16 lg:p-8 lg:pt-8">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
