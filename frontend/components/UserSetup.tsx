"use client";

import { useState } from "react";
import { useUser } from "@/lib/UserContext";
import { useLanguage } from "@/lib/LanguageContext";
import Image from "next/image";

export default function UserSetup() {
    const { setUserName } = useUser();
    const { t, language, setLanguage } = useLanguage();
    const [name, setName] = useState("");
    const [selectedLanguage, setSelectedLanguage] = useState(language);
    const [riskTolerance, setRiskTolerance] = useState("moderate");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) return;

        setLoading(true);
        setError("");
        try {
            await setUserName(name.trim(), selectedLanguage, riskTolerance);
            setLanguage(selectedLanguage as any);
        } catch {
            setError(t("error_create"));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-[var(--bg-primary)]">
            <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-3xl p-10 w-full max-w-md animate-fade-in text-center shadow-sm">
                <div className="mx-auto mb-8 flex items-center justify-center">
                    <Image src="/logo.png" alt="BaniWise Logo" width={64} height={64} className="rounded-2xl shadow-sm" />
                </div>

                <h1 className="text-3xl font-bold mb-3 tracking-tight text-[var(--text-primary)]">
                    {t("welcome")}
                </h1>

                <div className="text-[var(--text-secondary)] text-base mb-10 leading-relaxed whitespace-pre-line">
                    {t("welcome_subtitle")}
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder={t("name_placeholder")}
                        autoFocus
                        className="w-full px-5 py-4 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-all duration-200 text-lg text-center"
                    />

                    <div className="space-y-4 text-left">
                        <div>
                            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1 ml-1">{t("pref_language")}</label>
                            <select
                                value={selectedLanguage}
                                onChange={(e) => setSelectedLanguage(e.target.value as any)}
                                className="w-full px-5 py-3.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-all cursor-pointer appearance-none"
                            >
                                <option value="ro">{t("pref_lang_ro")}</option>
                                <option value="en">{t("pref_lang_en")}</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1 ml-1">{t("pref_risk")}</label>
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

                    {error && (
                        <p className="text-[var(--danger)] text-sm animate-fade-in">{error}</p>
                    )}

                    <button
                        type="submit"
                        disabled={!name.trim() || loading}
                        className="w-full py-4 rounded-xl bg-[var(--accent)] text-[var(--accent-fg)] font-medium text-lg shadow-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                    >
                        {loading ? (
                            <span className="flex items-center justify-center gap-2">
                                <span className="w-2 h-2 bg-current rounded-full animate-bounce" />
                                <span className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                                <span className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                            </span>
                        ) : (
                            t("start_button")
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}
