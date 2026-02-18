"use client";

import { useState } from "react";
import { useUser } from "@/lib/UserContext";
import { useLanguage } from "@/lib/LanguageContext";

export default function UserSetup() {
    const { setUserName } = useUser();
    const { t } = useLanguage();
    const [name, setName] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) return;

        setLoading(true);
        setError("");
        try {
            await setUserName(name.trim());
        } catch {
            setError(t("error_create"));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-[var(--bg-primary)]">
            <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-3xl p-10 w-full max-w-md animate-fade-in text-center shadow-sm">
                <div className="w-14 h-14 bg-[var(--accent)] rounded-2xl mx-auto mb-8 flex items-center justify-center text-2xl shadow-sm text-[var(--accent-fg)]">
                    🏦
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
                        className="w-full px-5 py-4 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--border-light)] focus:ring-2 focus:ring-[var(--border)] transition-all duration-200 text-lg text-center"
                    />

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
