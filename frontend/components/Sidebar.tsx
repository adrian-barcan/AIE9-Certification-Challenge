"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUser } from "@/lib/UserContext";
import { useLanguage } from "@/lib/LanguageContext";
import { useTheme } from "@/lib/ThemeContext";

export default function Sidebar() {
    const pathname = usePathname();
    const { user, logout } = useUser();
    const { language, setLanguage, t } = useLanguage();
    const { theme, toggleTheme } = useTheme();

    const toggleLanguage = () => {
        setLanguage(language === "ro" ? "en" : "ro");
    };

    const navItems = [
        { href: "/chat", icon: "💬", label: t("nav_chat") },
        { href: "/goals", icon: "🎯", label: t("nav_goals") },
        { href: "/documents", icon: "📄", label: t("nav_documents") },
    ];

    return (
        <aside className="w-80 h-screen shrink-0 flex flex-col border-r border-[var(--border)] bg-[var(--bg-card)]">
            {/* Logo */}
            <div className="p-6 border-b border-[var(--border)]">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-[var(--accent)] rounded-xl flex items-center justify-center text-lg shadow-sm text-[var(--accent-fg)]">
                            🏦
                        </div>
                        <div>
                            <h1 className="text-sm font-semibold tracking-tight text-[var(--text-primary)]">
                                FinBot
                            </h1>
                            <p className="text-xs text-[var(--text-secondary)]">
                                {t("app_subtitle")}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                        {/* Language Toggle */}
                        <button
                            onClick={toggleLanguage}
                            className="px-2 py-1 rounded-lg text-xs font-bold text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-input)] transition-colors border border-[var(--border)]"
                            title="Switch Language"
                        >
                            {language.toUpperCase()}
                        </button>

                        {/* Theme Toggle */}
                        <button
                            onClick={toggleTheme}
                            className="p-1.5 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-input)] transition-colors border border-[var(--border)]"
                            title="Toggle theme"
                        >
                            {theme === "dark" ? (
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" /></svg>
                            ) : (
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 group ${isActive
                                    ? "bg-[var(--accent)] text-[var(--accent-fg)] shadow-sm"
                                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-input)]"
                                }`}
                        >
                            <span
                                className={`text-lg transition-transform duration-200 ${isActive ? "scale-110" : "group-hover:scale-110"
                                    }`}
                            >
                                {item.icon}
                            </span>
                            {item.label}
                        </Link>
                    );
                })}
            </nav>

            {/* User info */}
            {user && (
                <div className="p-4 mt-auto border-t border-[var(--border)]">
                    <div className="flex items-center gap-3 rounded-xl bg-[var(--bg-input)] p-3">
                        <div className="w-9 h-9 rounded-full bg-[var(--accent)] flex items-center justify-center text-xs font-bold text-[var(--accent-fg)]">
                            {user.name.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate text-[var(--text-primary)]">
                                {user.name}
                            </p>
                            <button
                                onClick={logout}
                                className="text-xs text-[var(--text-muted)] hover:text-[var(--danger)] transition-colors"
                            >
                                {t("logout")}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </aside>
    );
}
