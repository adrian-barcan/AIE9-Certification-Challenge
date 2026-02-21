"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ingestDocuments, listDocuments } from "@/lib/api";
import { useLanguage } from "@/lib/LanguageContext";

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
                <div className="flex items-center gap-4">
                    <div className="text-3xl">📄</div>
                    <div className="flex-1">
                        <h3 className="font-medium text-sm text-[var(--text-primary)]">{t("docs_ingest_button")}</h3>
                        <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                            {t("docs_info")}
                        </p>
                    </div>
                    <button
                        onClick={handleIngest}
                        disabled={isIngesting}
                        className="px-5 py-2.5 rounded-full bg-[var(--accent)] text-[var(--accent-fg)] text-sm font-medium transition-default hover:opacity-90 disabled:opacity-50 shrink-0"
                    >
                        {isIngesting ? (
                            <span className="flex items-center gap-2">
                                <span className="animate-spin">⏳</span> {t("docs_ingest_processing")}
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
                <h3 className="font-medium text-sm mb-3 text-[var(--text-primary)]">{t("docs_status_title")}</h3>
                {loading ? (
                    <p className="text-sm text-[var(--text-muted)] animate-pulse">
                        Loading...
                    </p>
                ) : documents.length > 0 ? (
                    <div className="space-y-3">
                        {documents.map((doc, i) => (
                            <div
                                key={i}
                                className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border)]"
                            >
                                <span className="text-sm text-[var(--text-primary)]">{doc.filename}</span>
                                <span className="text-xs text-[var(--text-secondary)] bg-[var(--bg-secondary)] px-2.5 py-1 rounded-full border border-[var(--border)]">
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
