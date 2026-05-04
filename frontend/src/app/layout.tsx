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

export const metadata: Metadata = {
  title: "Book2Podcast - 书本变播客",
  description: "将书本转化为双人对谈播客，随时随地在手机上收听",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Book2Podcast",
  },
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-CN"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <link rel="apple-touch-icon" href="/icon-192.png" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
      </head>
      <body className="min-h-full flex flex-col bg-zinc-50 dark:bg-zinc-950">
        <header className="sticky top-0 z-50 bg-white/80 dark:bg-zinc-900/80 backdrop-blur border-b border-zinc-200 dark:border-zinc-800">
          <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
            <a href="/" className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
              书本播客
            </a>
          </div>
        </header>
        <main className="flex-1 max-w-2xl mx-auto w-full px-4 pb-24">
          {children}
        </main>
      </body>
    </html>
  );
}
