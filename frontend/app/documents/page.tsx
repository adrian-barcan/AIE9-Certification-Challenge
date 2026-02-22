"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ingestDocuments, listDocuments } from "@/lib/api";
import { useLanguage } from "@/lib/LanguageContext";
import Image from "next/image";

export default function DocumentsPage() {
    const queryClient = useQueryClient();
    const { t } = useLanguage();
    const [result, setResult] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const { data: documents = [], isLoading: loading } = useQuery({
        queryKey: ["documents"],
        queryFn: listDocuments,
    });

    const ingestMutation = useMutation({
        mutationFn: ingestDocuments,
        onSuccess: () => {
            setResult(t("docs_success"));
            queryClient.invalidateQueries({ queryKey: ["documents"] });
        },
        onError: (e) => {
            setError(e instanceof Error ? e.message : t("docs_error"));
        },
    });

    const handleIngest = () => {
        setResult(null);
        setError(null);
        ingestMutation.mutate();
    };

    const isIngesting = ingestMutation.isPending;

    useEffect(() => {
        document.title = `${t("nav_documents")} | BaniWise`;
    }, [t]);

    return (
        <div className="p-6 max-w-2xl mx-auto">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t("docs_title")}</h1>
                <p className="text-sm text-[var(--text-secondary)] mt-1">
                    {t("docs_subtitle")}
                </p>
            </div>

            {/* Ingest button */}
            <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-6 mb-6 shadow-sm">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
                    <div className="p-3 bg-[var(--bg-input)] rounded-2xl border border-[var(--border)] shadow-sm shrink-0">
                        <Image src="/docs_icon.png" alt="Documente" width={48} height={48} className="rounded-xl drop-shadow-sm" />
                    </div>
                    <div className="flex-1">
                        <h3 className="font-bold text-base text-[var(--text-primary)]">{t("docs_ingest_button")}</h3>
                        <p className="text-sm font-medium text-[var(--text-secondary)] mt-1">
                            {t("docs_info")}
                        </p>
                    </div>
                    <button
                        onClick={handleIngest}
                        disabled={isIngesting}
                        className="w-full sm:w-auto px-6 py-3 rounded-full bg-[var(--accent)] text-[var(--accent-fg)] text-sm font-bold transition-transform hover:scale-105 disabled:hover:scale-100 disabled:opacity-50 shrink-0 shadow-md hover:shadow-lg"
                    >
                        {isIngesting ? (
                            <span className="flex items-center justify-center gap-2">
                                <span className="animate-spin text-lg">⏳</span> {t("docs_ingest_processing")}
                            </span>
                        ) : (
                            t("docs_ingest_button")
                        )}
                    </button>
                </div>

                {/* Result / Error */}
                {result && (
                    <div className="mt-4 p-3 rounded-xl bg-green-500/10 border border-green-500/20 text-sm text-green-600 dark:text-green-400 animate-fade-in">
                        {result}
                    </div>
                )}
                {error && (
                    <div className="mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-600 dark:text-red-400 animate-fade-in">
                        ⚠️ {error}
                    </div>
                )}
            </div>

            {/* Collection info */}
            <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-6 shadow-sm">
                <h3 className="font-bold text-base mb-4 text-[var(--text-primary)]">{t("docs_status_title")}</h3>
                {loading ? (
                    <p className="text-sm font-medium text-[var(--text-muted)] animate-pulse">
                        Loading...
                    </p>
                ) : documents.length > 0 ? (
                    <div className="space-y-3">
                        {documents.map((doc, i) => (
                            <div
                                key={i}
                                className="flex items-center justify-between p-4 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] hover:border-[var(--accent)]/30 transition-colors group shadow-sm"
                            >
                                <span className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--accent)] opacity-80 group-hover:opacity-100 transition-opacity"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" /><polyline points="14 2 14 8 20 8" /></svg>
                                    {doc.filename}
                                </span>
                                <span className="text-xs font-bold text-[var(--accent)] bg-[var(--accent)]/10 px-3 py-1.5 rounded-md border border-[var(--accent)]/20">
                                    {doc.chunk_count} {t("docs_count")}
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-sm text-[var(--text-muted)]">
                        {t("docs_upload_hint")}
                    </p>
                )}
            </div>
        </div>
    );
}
