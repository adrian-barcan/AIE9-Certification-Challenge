import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import AppShell from "@/components/AppShell";
import { UserProvider } from "@/lib/UserContext";
import { LanguageProvider } from "@/lib/LanguageContext";
import { ThemeProvider } from "@/lib/ThemeContext";

const inter = Inter({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FinBot — Asistent Financiar Personal",
  description:
    "Agent financiar AI pentru investitori din România. RAG pe documente reglementare, obiective financiare, și date live de piață.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ro" className="dark">
      <body className={`${inter.variable} antialiased`}>
        <ThemeProvider>
          <UserProvider>
            <LanguageProvider>
              <AppShell>{children}</AppShell>
            </LanguageProvider>
          </UserProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
