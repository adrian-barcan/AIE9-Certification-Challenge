"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useUser } from "@/lib/UserContext";
import { useLanguage } from "@/lib/LanguageContext";
import {
    listGoals,
    createGoal,
    deleteGoal,
    contributeToGoal,
    Goal,
    GoalCreate,
} from "@/lib/api";

const ICONS = ["🎯", "🚗", "🏖️", "🏠", "🛡️", "💰", "📚", "✈️", "💻", "🎓"];

export default function GoalsPage() {
    const { user } = useUser();
    const queryClient = useQueryClient();
    const { t } = useLanguage();

    const [showForm, setShowForm] = useState(false);
    const [contributeId, setContributeId] = useState<string | null>(null);
    const [contributeAmount, setContributeAmount] = useState("");

    const [formData, setFormData] = useState<GoalCreate>({
        name: "",
        icon: "🎯",
        target_amount: 0,
        monthly_contribution: 0,
        priority: "medium",
    });

    const { data: goals = [], isLoading: loading } = useQuery({
        queryKey: ["goals", user?.id],
        queryFn: () => listGoals(user!.id),
        enabled: !!user?.id,
    });

    const createMutation = useMutation({
        mutationFn: (data: GoalCreate) => createGoal(user!.id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["goals", user?.id] });
            setShowForm(false);
            setFormData({
                name: "",
                icon: "🎯",
                target_amount: 0,
                monthly_contribution: 0,
                priority: "medium",
            });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: deleteGoal,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["goals", user?.id] }),
    });

    const contributeMutation = useMutation({
        mutationFn: ({ id, amount }: { id: string; amount: number }) => contributeToGoal(id, amount),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["goals", user?.id] });
            setContributeId(null);
            setContributeAmount("");
        },
    });

    const handleCreate = (e: React.FormEvent) => {
        e.preventDefault();
        if (!user || !formData.name || !formData.target_amount) return;
        createMutation.mutate(formData);
    };

    const handleDelete = (goalId: string) => deleteMutation.mutate(goalId);

    const handleContribute = (goalId: string) => {
        const amount = parseFloat(contributeAmount);
        if (!amount || amount <= 0) return;
        contributeMutation.mutate({ id: goalId, amount });
    };

    const quickContribute = (goalId: string, amount: number) => {
        contributeMutation.mutate({ id: goalId, amount });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <p className="text-[var(--text-muted)] animate-pulse">
                    {t("goals_loading")}
                </p>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-4xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t("goals_title")}</h1>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">
                        {t("goals_subtitle")}
                    </p>
                </div>
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="px-4 py-2.5 rounded-full bg-[var(--accent)] text-[var(--accent-fg)] text-sm font-medium transition-default hover:opacity-90"
                >
                    {showForm ? t("modal_cancel") : t("goals_create_new")}
                </button>
            </div>

            {/* Create form */}
            {showForm && (
                <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-6 mb-6 animate-fade-in">
                    <h3 className="font-semibold mb-4 text-[var(--text-primary)]">{t("modal_title")}</h3>
                    <form onSubmit={handleCreate} className="space-y-4">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs text-[var(--text-secondary)] mb-1.5">
                                    {t("modal_name")}
                                </label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) =>
                                        setFormData({ ...formData, name: e.target.value })
                                    }
                                    placeholder="Ex: Mașină nouă"
                                    className="w-full px-3 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--border-light)] transition-default"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-xs text-[var(--text-secondary)] mb-1.5">
                                    {t("modal_target")}
                                </label>
                                <input
                                    type="number"
                                    value={formData.target_amount || ""}
                                    onChange={(e) =>
                                        setFormData({
                                            ...formData,
                                            target_amount: parseFloat(e.target.value) || 0,
                                        })
                                    }
                                    placeholder="50000"
                                    min="1"
                                    className="w-full px-3 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--border-light)] transition-default"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-xs text-[var(--text-secondary)] mb-1.5">
                                    {t("modal_monthly")}
                                </label>
                                <input
                                    type="number"
                                    value={formData.monthly_contribution || ""}
                                    onChange={(e) =>
                                        setFormData({
                                            ...formData,
                                            monthly_contribution: parseFloat(e.target.value) || 0,
                                        })
                                    }
                                    placeholder="2000"
                                    min="0"
                                    className="w-full px-3 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--border-light)] transition-default"
                                />
                            </div>
                            <div>
                                <label className="block text-xs text-[var(--text-secondary)] mb-1.5">
                                    {t("modal_priority")}
                                </label>
                                <select
                                    value={formData.priority}
                                    onChange={(e) =>
                                        setFormData({ ...formData, priority: e.target.value })
                                    }
                                    className="w-full px-3 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--border-light)] transition-default"
                                >
                                    <option value="low">Scăzută</option>
                                    <option value="medium">Medie</option>
                                    <option value="high">Ridicată</option>
                                </select>
                            </div>
                        </div>

                        {/* Icon picker */}
                        <div>
                            <label className="block text-xs text-[var(--text-secondary)] mb-1.5">
                                {t("modal_icon")}
                            </label>
                            <div className="flex gap-2 flex-wrap">
                                {ICONS.map((icon) => (
                                    <button
                                        key={icon}
                                        type="button"
                                        onClick={() => setFormData({ ...formData, icon })}
                                        className={`w-10 h-10 rounded-xl text-lg flex items-center justify-center transition-default border ${formData.icon === icon
                                            ? "bg-[var(--accent)] text-[var(--accent-fg)] border-[var(--accent)]"
                                            : "bg-[var(--bg-input)] border-[var(--border)] hover:border-[var(--border-light)]"
                                            }`}
                                    >
                                        {icon}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <button
                            type="submit"
                            className="px-5 py-2.5 rounded-full bg-[var(--accent)] text-[var(--accent-fg)] text-sm font-medium transition-default hover:opacity-90"
                        >
                            {t("modal_create")}
                        </button>
                    </form>
                </div>
            )}

            {/* Goals grid */}
            {goals.length === 0 ? (
                <div className="text-center py-16 animate-fade-in">
                    <div className="text-5xl mb-4">🎯</div>
                    <h3 className="text-lg font-medium mb-2 text-[var(--text-primary)]">{t("goals_no_goals")}</h3>
                    <p className="text-sm text-[var(--text-secondary)]">
                        {t("goals_subtitle")}
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {goals.map((goal) => (
                        <div
                            key={goal.id}
                            className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-5 animate-fade-in hover:border-[var(--border-light)] transition-default shadow-sm"
                        >
                            {/* Header */}
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-3">
                                    <span className="text-2xl">{goal.icon}</span>
                                    <div>
                                        <h3 className="font-semibold text-sm text-[var(--text-primary)]">{goal.name}</h3>
                                        <span
                                            className={`text-xs px-2 py-0.5 rounded-full ${goal.priority === "high"
                                                ? "bg-red-500/10 text-red-500 dark:bg-red-500/20 dark:text-red-400"
                                                : goal.priority === "medium"
                                                    ? "bg-yellow-500/10 text-yellow-600 dark:bg-yellow-500/20 dark:text-yellow-400"
                                                    : "bg-green-500/10 text-green-600 dark:bg-green-500/20 dark:text-green-400"
                                                }`}
                                        >
                                            {goal.priority === "high"
                                                ? "Ridicată"
                                                : goal.priority === "medium"
                                                    ? "Medie"
                                                    : "Scăzută"}
                                        </span>
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleDelete(goal.id)}
                                    className="text-[var(--text-muted)] hover:text-[var(--danger)] text-sm transition-default"
                                    title={t("goals_delete")}
                                >
                                    ✕
                                </button>
                            </div>

                            {/* Progress */}
                            <div className="mb-3">
                                <div className="flex justify-between text-xs mb-1.5">
                                    <span className="text-[var(--text-secondary)]">
                                        {goal.saved_amount.toLocaleString("ro-RO")} RON
                                    </span>
                                    <span className="text-[var(--text-secondary)]">
                                        {goal.target_amount.toLocaleString("ro-RO")} RON
                                    </span>
                                </div>
                                <div className="h-2.5 bg-[var(--bg-input)] rounded-full overflow-hidden">
                                    <div
                                        className="h-full rounded-full bg-[var(--accent)] animate-progress"
                                        style={{
                                            width: `${Math.min(goal.progress_percent, 100)}%`,
                                        }}
                                    />
                                </div>
                                <div className="flex justify-between mt-1.5">
                                    <span className="text-xs font-medium text-[var(--text-primary)]">
                                        {goal.progress_percent.toFixed(0)}%
                                    </span>
                                    <span className="text-xs text-[var(--text-muted)]">
                                        {t("goals_remaining_months")}:{" "}
                                        {goal.remaining_amount.toLocaleString("ro-RO")} RON
                                    </span>
                                </div>
                            </div>

                            {/* Monthly contribution info */}
                            {goal.monthly_contribution > 0 && (
                                <p className="text-xs text-[var(--text-muted)] mb-3">
                                    📅 {goal.monthly_contribution.toLocaleString("ro-RO")} RON /{" "}
                                    {t("goals_monthly")}
                                    {goal.remaining_amount > 0 &&
                                        goal.monthly_contribution > 0 && (
                                            <>
                                                {" "}
                                                · ~
                                                {Math.ceil(
                                                    goal.remaining_amount / goal.monthly_contribution
                                                )}{" "}
                                                {t("goals_remaining_months")}
                                            </>
                                        )}
                                </p>
                            )}

                            {/* Quick contribute */}
                            {contributeId === goal.id ? (
                                <div className="flex gap-2 animate-fade-in">
                                    <input
                                        type="number"
                                        value={contributeAmount}
                                        onChange={(e) => setContributeAmount(e.target.value)}
                                        placeholder="Sumă"
                                        min="1"
                                        autoFocus
                                        className="flex-1 px-3 py-2 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--border-light)] transition-default"
                                    />
                                    <button
                                        onClick={() => handleContribute(goal.id)}
                                        className="px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition-default"
                                    >
                                        {t("goals_add_funds")}
                                    </button>
                                    <button
                                        onClick={() => {
                                            setContributeId(null);
                                            setContributeAmount("");
                                        }}
                                        className="px-3 py-2 rounded-xl bg-[var(--bg-input)] hover:bg-[var(--border)] text-sm transition-default text-[var(--text-primary)]"
                                    >
                                        ✕
                                    </button>
                                </div>
                            ) : (
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => quickContribute(goal.id, 100)}
                                        className="flex-1 py-2 rounded-xl bg-[var(--bg-input)] hover:bg-[var(--border)] text-xs transition-default text-[var(--text-primary)] border border-[var(--border)]"
                                    >
                                        +100 RON
                                    </button>
                                    <button
                                        onClick={() => quickContribute(goal.id, 500)}
                                        className="flex-1 py-2 rounded-xl bg-[var(--bg-input)] hover:bg-[var(--border)] text-xs transition-default text-[var(--text-primary)] border border-[var(--border)]"
                                    >
                                        +500 RON
                                    </button>
                                    <button
                                        onClick={() => setContributeId(goal.id)}
                                        className="flex-1 py-2 rounded-xl bg-[var(--bg-input)] hover:bg-[var(--border)] text-xs transition-default text-[var(--text-primary)] border border-[var(--border)]"
                                    >
                                        {t("goals_custom")}
                                    </button>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
