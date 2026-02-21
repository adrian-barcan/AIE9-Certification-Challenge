"use client";

import { ReactNode, useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { UserProvider, useUser } from "@/lib/UserContext";
import Sidebar from "@/components/Sidebar";
import UserSetup from "@/components/UserSetup";
import Image from "next/image";

function AppContent({ children }: { children: ReactNode }) {
    const { user, loading } = useUser();
    const pathname = usePathname();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    useEffect(() => {
        setIsMobileMenuOpen(false);
    }, [pathname]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
                <div className="text-[var(--text-muted)] animate-pulse text-lg">
                    Se încarcă...
                </div>
            </div>
        );
    }

    if (!user) {
        return <UserSetup />;
    }

    return (
        <div className="flex h-[100dvh] overflow-hidden bg-[var(--bg-primary)] text-[var(--text-primary)] flex-col md:flex-row">
            {/* Mobile Header - only visible on small screens */}
            <header className="md:hidden flex items-center justify-between p-4 border-b border-[var(--border)] bg-[var(--bg-card)] shrink-0 z-40">
                <div className="flex items-center gap-2 font-semibold">
                    <Image src="/logo.png" alt="BaniWise Logo" width={32} height={32} className="rounded-lg shadow-sm" />
                    <span className="tracking-tight text-[var(--text-primary)]">BaniWise</span>
                </div>
                <button
                    onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                    className="p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border)] rounded-lg bg-[var(--bg-input)] transition-colors"
                >
                    {isMobileMenuOpen ? (
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                    ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" /></svg>
                    )}
                </button>
            </header>

            {/* Mobile Sidebar Backdrop */}
            {isMobileMenuOpen && (
                <div
                    className="md:hidden fixed inset-0 bg-black/50 z-40 transition-opacity"
                    onClick={() => setIsMobileMenuOpen(false)}
                />
            )}

            {/* Sidebar Container */}
            <div className={`fixed inset-y-0 left-0 z-50 transform md:relative md:translate-x-0 transition-transform duration-300 ease-in-out ${isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"}`}>
                <Sidebar />
            </div>

            <main className="flex-1 overflow-auto">{children}</main>
        </div>
    );
}

export default function AppShell({ children }: { children: ReactNode }) {
    return (
        <AppContent>{children}</AppContent>
    );
}
