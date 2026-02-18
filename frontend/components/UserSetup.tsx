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
        <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
            {/* Abstract background blobs */}
            <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[120px] pointer-events-none" />

            <div className="relative glass-card p-10 w-full max-w-md animate-fade-in text-center border border-white/10 shadow-2xl">
                <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl mx-auto mb-8 flex items-center justify-center text-3xl shadow-lg shadow-indigo-500/20">
                    🏦
                </div>

                <h1 className="text-4xl font-bold mb-3 tracking-tight bg-gradient-to-r from-white via-indigo-100 to-indigo-200 bg-clip-text text-transparent">
                    {t("welcome")}
                </h1>

                <div className="text-[var(--text-muted)] text-base mb-10 leading-relaxed font-light whitespace-pre-line">
                    {t("welcome_subtitle")}
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="group relative">
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder={t("name_placeholder")}
                            autoFocus
                            className="w-full px-5 py-4 rounded-xl bg-[var(--bg-input)] border border-white/5 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:bg-[var(--bg-input)] transition-all duration-300 text-lg text-center"
                        />
                    </div>

                    {error && (
                        <p className="text-[var(--danger)] text-sm animate-fade-in">{error}</p>
                    )}

                    <button
                        type="submit"
                        disabled={!name.trim() || loading}
                        className="w-full py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-lg shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/40 transform hover:-translate-y-0.5 transition-all duration-300"
                    >
                        {loading ? (
                            <span className="flex items-center justify-center gap-2">
                                <span className="w-2 h-2 bg-white rounded-full animate-bounce" />
                                <span className="w-2 h-2 bg-white rounded-full animate-bounce delay-100" />
                                <span className="w-2 h-2 bg-white rounded-full animate-bounce delay-200" />
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
