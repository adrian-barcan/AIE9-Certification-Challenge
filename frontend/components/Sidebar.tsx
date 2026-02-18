"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUser } from "@/lib/UserContext";
import { useLanguage } from "@/lib/LanguageContext";

export default function Sidebar() {
    const pathname = usePathname();
    const { user, logout } = useUser();
    const { language, setLanguage, t } = useLanguage();

    const toggleLanguage = () => {
        setLanguage(language === "ro" ? "en" : "ro");
    };

    const navItems = [
        { href: "/chat", icon: "💬", label: t("nav_chat") },
        { href: "/goals", icon: "🎯", label: t("nav_goals") },
        { href: "/documents", icon: "📄", label: t("nav_documents") },
    ];

    return (
        <aside className="w-80 h-screen p-4 flex flex-col shrink-0">
            <div className="flex-1 flex flex-col glass-card overflow-hidden border border-white/5">
                {/* Logo */}
                <div className="p-6 border-b border-white/5 flex justify-between items-start">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center text-xl shadow-lg shadow-indigo-500/20">
                            🏦
                        </div>
                        <div>
                            <h1 className="text-lg font-bold tracking-tight text-white">
                                FinBot
                            </h1>
                            <p className="text-xs text-[var(--text-secondary)] font-medium">
                                {t("app_subtitle")}
                            </p>
                        </div>
                    </div>

                    {/* Language Toggle */}
                    <button
                        onClick={toggleLanguage}
                        className="px-2 py-1 rounded-md bg-white/5 hover:bg-white/10 text-xs font-bold text-[var(--text-secondary)] hover:text-white transition-colors border border-white/5"
                        title="Switch Language"
                    >
                        {language.toUpperCase()}
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`flex items-center gap-3 px-4 py-3.5 rounded-xl text-sm font-medium transition-all duration-200 group ${isActive
                                        ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/20 translate-x-1"
                                        : "text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/5"
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
                    <div className="p-4 mt-auto border-t border-white/5 bg-black/20">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-600 flex items-center justify-center text-sm font-medium border border-white/10 text-white">
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
            </div>
        </aside>
    );
}
