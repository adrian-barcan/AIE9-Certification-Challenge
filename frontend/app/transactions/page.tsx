"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
    ingestTransactions,
    listTransactionSources,
    listTransactions,
    deleteTransactionSource,
    type TransactionSourceResponse,
    type TransactionResponse,
} from "@/lib/api";
import { useUser } from "@/lib/UserContext";
import { useLanguage } from "@/lib/LanguageContext";

export default function TransactionsPage() {
    const { user } = useUser();
    const queryClient = useQueryClient();
    const { t } = useLanguage();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [bankLabel, setBankLabel] = useState("");
    const [result, setResult] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);

    const { data: sources = [], isLoading: loadingSources } = useQuery({
        queryKey: ["transaction-sources", user?.id],
        queryFn: () => listTransactionSources(user!.id),
        enabled: !!user?.id,
    });

    const { data: transactions = [], isLoading: loadingTx } = useQuery({
        queryKey: ["transactions", user?.id, selectedSourceId],
        queryFn: () =>
            listTransactions(user!.id, {
                source_id: selectedSourceId || undefined,
                limit: 200,
            }),
        enabled: !!user?.id,
    });

    const ingestMutation = useMutation({
        mutationFn: ({ file, label }: { file: File; label: string }) =>
            ingestTransactions(user!.id, file, label || undefined),
        onSuccess: (data) => {
            const by = data.categorization_source === "ollama"
                ? " (Mistral/Ollama)"
                : " (rules – Ollama unavailable)";
            setResult(
                `${t("tx_import_success")}: ${data.transactions_imported} ${t("tx_transactions").toLowerCase()} (${data.bank_label})${by}`
            );
            setError(null);
            setBankLabel("");
            if (fileInputRef.current) fileInputRef.current.value = "";
            queryClient.invalidateQueries({ queryKey: ["transaction-sources", user?.id] });
            queryClient.invalidateQueries({ queryKey: ["transactions", user?.id] });
        },
        onError: (e) => {
            setError(e instanceof Error ? e.message : t("tx_import_error"));
            setResult(null);
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (sourceId: string) =>
            deleteTransactionSource(sourceId, user!.id),
        onSuccess: () => {
            if (selectedSourceId) setSelectedSourceId(null);
            queryClient.invalidateQueries({ queryKey: ["transaction-sources", user?.id] });
            queryClient.invalidateQueries({ queryKey: ["transactions", user?.id] });
        },
    });

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setResult(null);
        setError(null);
        ingestMutation.mutate({ file, label: bankLabel });
    };

    useEffect(() => {
        document.title = `${t("tx_title")} | BaniWise`;
    }, [t]);

    if (!user) {
        return (
            <div className="p-6 max-w-2xl mx-auto">
                <p className="text-[var(--text-muted)]">{t("goals_loading")}</p>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-[var(--text-primary)]">
                    {t("tx_title")}
                </h1>
                <p className="text-sm text-[var(--text-secondary)] mt-1">
                    {t("tx_subtitle")}
                </p>
            </div>

            {/* Upload */}
            <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-6 mb-6 shadow-sm">
                <div className="flex flex-col gap-4">
                    <div className="flex flex-wrap items-end gap-3">
                        <label className="flex flex-col gap-1">
                            <span className="text-sm font-medium text-[var(--text-primary)]">
                                {t("tx_upload")}
                            </span>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".csv"
                                onChange={handleFileChange}
                                disabled={ingestMutation.isPending}
                                className="text-sm text-[var(--text-primary)] file:mr-3 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-[var(--accent)] file:text-[var(--accent-fg)] file:font-bold"
                            />
                        </label>
                        <label className="flex flex-col gap-1">
                            <span className="text-sm font-medium text-[var(--text-secondary)]">
                                {t("tx_bank_label")}
                            </span>
                            <input
                                type="text"
                                value={bankLabel}
                                onChange={(e) => setBankLabel(e.target.value)}
                                placeholder="Ex: BRD Current"
                                className="px-3 py-2 rounded-xl border border-[var(--border)] bg-[var(--bg-input)] text-sm text-[var(--text-primary)] w-40"
                            />
                        </label>
                    </div>
                    {ingestMutation.isPending && (
                        <p className="text-sm text-[var(--text-secondary)] flex items-center gap-2">
                            <span className="animate-spin">⏳</span> {t("tx_upload_processing")}
                        </p>
                    )}
                    {result && (
                        <div className="p-3 rounded-xl bg-green-500/10 border border-green-500/20 text-sm text-green-600 dark:text-green-400">
                            {result}
                        </div>
                    )}
                    {error && (
                        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-600 dark:text-red-400">
                            ⚠️ {error}
                        </div>
                    )}
                </div>
            </div>

            {/* CTA to Chat */}
            <div className="mb-6">
                <Link
                    href="/chat?q=Unde%20pot%20economisi?"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--accent)] text-[var(--accent-fg)] text-sm font-bold hover:opacity-90 transition-opacity"
                >
                    💡 {t("tx_ask_savings")}
                </Link>
            </div>

            {/* Sources */}
            <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-6 shadow-sm mb-6">
                <h3 className="font-bold text-base mb-4 text-[var(--text-primary)]">
                    {t("tx_sources")}
                </h3>
                {loadingSources ? (
                    <p className="text-sm text-[var(--text-muted)] animate-pulse">Loading...</p>
                ) : sources.length === 0 ? (
                    <p className="text-sm text-[var(--text-muted)]">{t("tx_no_sources")}</p>
                ) : (
                    <ul className="space-y-2">
                        {sources.map((src: TransactionSourceResponse) => (
                            <li
                                key={src.id}
                                className={`flex items-center justify-between p-3 rounded-xl border transition-colors ${
                                    selectedSourceId === src.id
                                        ? "border-[var(--accent)] bg-[var(--accent)]/5"
                                        : "border-[var(--border)] bg-[var(--bg-input)] hover:border-[var(--accent)]/30"
                                }`}
                            >
                                <button
                                    type="button"
                                    onClick={() =>
                                        setSelectedSourceId(
                                            selectedSourceId === src.id ? null : src.id
                                        )
                                    }
                                    className="flex-1 text-left"
                                >
                                    <span className="font-medium text-[var(--text-primary)]">
                                        {src.bank_label || "Import"}
                                    </span>
                                    <span className="ml-2 text-sm text-[var(--text-secondary)]">
                                        {src.transaction_count ?? 0} {t("tx_transactions").toLowerCase()} ·{" "}
                                        {new Date(src.imported_at).toLocaleDateString()}
                                    </span>
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        if (confirm(t("goals_delete_confirm")))
                                            deleteMutation.mutate(src.id);
                                    }}
                                    className="text-xs text-[var(--text-muted)] hover:text-red-500 px-2"
                                >
                                    {t("tx_delete_source")}
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {/* Transaction list */}
            <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-6 shadow-sm">
                <h3 className="font-bold text-base mb-4 text-[var(--text-primary)]">
                    {t("tx_transactions")}
                    {selectedSourceId ? " (filtered)" : ""}
                </h3>
                {loadingTx ? (
                    <p className="text-sm text-[var(--text-muted)] animate-pulse">Loading...</p>
                ) : transactions.length === 0 ? (
                    <p className="text-sm text-[var(--text-muted)]">
                        {selectedSourceId
                            ? "No transactions in this source."
                            : "Upload a CSV to see anonymized transactions here."}
                    </p>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-[var(--border)]">
                                    <th className="text-left py-2 font-medium text-[var(--text-secondary)]">
                                        {t("tx_date")}
                                    </th>
                                    <th className="text-right py-2 font-medium text-[var(--text-secondary)]">
                                        {t("tx_amount")}
                                    </th>
                                    <th className="text-left py-2 font-medium text-[var(--text-secondary)]">
                                        {t("tx_category")}
                                    </th>
                                    <th className="text-center py-2 font-medium text-[var(--text-secondary)]">
                                        {t("tx_recurring")}
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {transactions.map((tx: TransactionResponse) => (
                                    <tr
                                        key={tx.id}
                                        className="border-b border-[var(--border)]/50 hover:bg-[var(--bg-input)]/50"
                                    >
                                        <td className="py-2 text-[var(--text-primary)]">
                                            {new Date(tx.date).toLocaleDateString()}
                                        </td>
                                        <td
                                            className={`py-2 text-right font-medium ${
                                                tx.amount < 0
                                                    ? "text-red-500 dark:text-red-400"
                                                    : "text-green-600 dark:text-green-400"
                                            }`}
                                        >
                                            {tx.amount >= 0 ? "+" : ""}
                                            {tx.amount.toFixed(2)} {tx.currency}
                                        </td>
                                        <td className="py-2 text-[var(--text-primary)]">
                                            {tx.category}
                                        </td>
                                        <td className="py-2 text-center">
                                            {tx.is_recurring ? "✓" : "—"}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
