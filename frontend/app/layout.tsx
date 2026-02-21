import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import AppShell from "@/components/AppShell";
import { UserProvider } from "@/lib/UserContext";
import { LanguageProvider } from "@/lib/LanguageContext";
import { ThemeProvider } from "@/lib/ThemeContext";
import Providers from "./providers";

const inter = Inter({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "BaniWise — Asistent Financiar Personal",
  description: "Aplicația ta de bugetare și sfaturi financiare inteligente.",
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
          <Providers>
            <UserProvider>
              <LanguageProvider>
                <AppShell>{children}</AppShell>
              </LanguageProvider>
            </UserProvider>
          </Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}
