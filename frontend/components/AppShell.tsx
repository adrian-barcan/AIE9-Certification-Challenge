"use client";

import { ReactNode } from "react";
import { UserProvider, useUser } from "@/lib/UserContext";
import Sidebar from "@/components/Sidebar";
import UserSetup from "@/components/UserSetup";

function AppContent({ children }: { children: ReactNode }) {
    const { user, loading } = useUser();

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
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
        <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-auto">{children}</main>
        </div>
    );
}

export default function AppShell({ children }: { children: ReactNode }) {
    return (
        <UserProvider>
            <AppContent>{children}</AppContent>
        </UserProvider>
    );
}
