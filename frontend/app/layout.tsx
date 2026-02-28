import type { Metadata } from "next";
import "./globals.css";
import AppShell from "@/components/AppShell";
import { UserProvider } from "@/lib/UserContext";
import { LanguageProvider } from "@/lib/LanguageContext";
import { ThemeProvider } from "@/lib/ThemeContext";
import Providers from "./providers";

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
      <body className="antialiased font-sans" style={{ fontFamily: "var(--font-sans, ui-sans-serif, system-ui, sans-serif, 'Segoe UI', Roboto, sans-serif)" }}>
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
