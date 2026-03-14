"use client";

import { useState } from "react";
import { useUser } from "@/lib/UserContext";
import { useLanguage } from "@/lib/LanguageContext";
import type { Language } from "@/lib/translations";
import Image from "next/image";

export default function UserSetup() {
    const { register, login } = useUser();
    const { t, language, setLanguage } = useLanguage();
    const [mode, setMode] = useState<"login" | "register">("login");
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [selectedLanguage, setSelectedLanguage] = useState(language);
    const [riskTolerance, setRiskTolerance] = useState("moderate");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (mode === "register" && !name.trim()) return;
        if (!email.trim() || !password.trim()) return;

        setLoading(true);
        setError("");
        try {
            if (mode === "register") {
                await register(name.trim(), email.trim(), password, selectedLanguage, riskTolerance);
                setLanguage(selectedLanguage);
            } else {
                await login(email.trim(), password);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : t("error_create"));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-[var(--bg-primary)]">
            <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-3xl p-6 sm:p-10 w-full max-w-md animate-fade-in text-center shadow-sm">
                <div className="mx-auto mb-8 flex items-center justify-center">
                    <Image src="/logo.png" alt="BaniWise Logo" width={64} height={64} className="rounded-2xl shadow-sm" />
                </div>

                <h1 className="text-3xl sm:text-4xl font-bold mb-3 tracking-tight text-[var(--text-primary)]">
                    {t("welcome")}
                </h1>

                <div className="text-[var(--text-secondary)] text-base sm:text-lg mb-10 leading-relaxed whitespace-pre-line">
                    {t("welcome_subtitle")}
                </div>

                <div className="flex gap-2 mb-5 p-1 rounded-xl bg-[var(--bg-input)] border border-[var(--border)]">
                    <button
                        type="button"
                        onClick={() => setMode("login")}
                        className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${mode === "login"
                                ? "bg-[var(--accent)] text-[var(--accent-fg)]"
                                : "text-[var(--text-secondary)]"
                            }`}
                    >
                        {t("auth_login")}
                    </button>
                    <button
                        type="button"
                        onClick={() => setMode("register")}
                        className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${mode === "register"
                                ? "bg-[var(--accent)] text-[var(--accent-fg)]"
                                : "text-[var(--text-secondary)]"
                            }`}
                    >
                        {t("auth_register")}
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    {mode === "register" && (
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder={t("name_placeholder")}
                            autoFocus
                            className="w-full px-5 py-4 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-all duration-200 text-base sm:text-lg text-center"
                        />
                    )}

                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder={t("auth_email")}
                        className="w-full px-5 py-4 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-all duration-200 text-base sm:text-lg text-center"
                    />

                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder={t("auth_password")}
                        className="w-full px-5 py-4 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-all duration-200 text-base sm:text-lg text-center"
                    />

                    {mode === "register" && (
                        <div className="space-y-4 text-left">
                        <div>
                            <label className="block text-sm sm:text-base font-medium text-[var(--text-secondary)] mb-1 ml-1">{t("pref_language")}</label>
                            <select
                                value={selectedLanguage}
                                onChange={(e) => setSelectedLanguage(e.target.value as Language)}
                                className="w-full px-5 py-3.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-all cursor-pointer appearance-none"
                            >
                                <option value="ro">{t("pref_lang_ro")}</option>
                                <option value="en">{t("pref_lang_en")}</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm sm:text-base font-medium text-[var(--text-secondary)] mb-1 ml-1">{t("pref_risk")}</label>
                            <select
                                value={riskTolerance}
                                onChange={(e) => setRiskTolerance(e.target.value)}
                                className="w-full px-5 py-3.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-all cursor-pointer appearance-none"
                            >
                                <option value="conservative">{t("pref_risk_conservative")}</option>
                                <option value="moderate">{t("pref_risk_moderate")}</option>
                                <option value="aggressive">{t("pref_risk_aggressive")}</option>
                            </select>
                        </div>
                        </div>
                    )}

                    {error && (
                        <p className="text-[var(--danger)] text-sm sm:text-base animate-fade-in">{error}</p>
                    )}

                    <button
                        type="submit"
                        disabled={(mode === "register" ? !name.trim() : false) || !email.trim() || !password.trim() || loading}
                        className="w-full py-4 rounded-xl bg-[var(--accent)] text-[var(--accent-fg)] font-medium text-base sm:text-lg shadow-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                    >
                        {loading ? (
                            <span className="flex items-center justify-center gap-2">
                                <span className="w-2 h-2 bg-current rounded-full animate-bounce" />
                                <span className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                                <span className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                            </span>
                        ) : (
                            mode === "register" ? t("auth_register_cta") : t("auth_login_cta")
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}
