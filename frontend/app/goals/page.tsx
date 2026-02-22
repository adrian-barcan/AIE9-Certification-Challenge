"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useUser } from "@/lib/UserContext";
import { useLanguage } from "@/lib/LanguageContext";
import Image from "next/image";
import {
    listGoals,
    createGoal,
    deleteGoal,
    contributeToGoal,
    Goal,
    GoalCreate,
} from "@/lib/api";

const ICON_CATEGORIES = [
    { icon: "🎯", key: "cat_general" },
    { icon: "🚗", key: "cat_auto" },
    { icon: "🏖️", key: "cat_vacation" },
    { icon: "🏠", key: "cat_home" },
    { icon: "🛡️", key: "cat_emergency" },
    { icon: "💰", key: "cat_savings" },
    { icon: "📚", key: "cat_education" },
    { icon: "✈️", key: "cat_flights" },
    { icon: "💻", key: "cat_tech" },
    { icon: "🎓", key: "cat_graduation" },
    { icon: "💡", key: "cat_others" },
];

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
        currency: "RON",
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
                currency: "RON",
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

    useEffect(() => {
        document.title = `${t("nav_goals")} | BaniWise`;
    }, [t]);

    const handleCreate = (e: React.FormEvent) => {
        e.preventDefault();
        if (!user || !formData.name || !formData.target_amount) return;
        createMutation.mutate(formData);
    };

    const handleDelete = (goalId: string) => {
        if (window.confirm(t("goals_delete_confirm"))) {
            deleteMutation.mutate(goalId);
        }
    };

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

    // Group totals by currency
    const totalsByCurrency = goals.reduce((acc, goal) => {
        const cur = goal.currency || "RON";
        if (!acc[cur]) acc[cur] = { target: 0, saved: 0, monthly: 0 };
        acc[cur].target += goal.target_amount;
        acc[cur].saved += goal.saved_amount;
        acc[cur].monthly += goal.monthly_contribution;
        return acc;
    }, {} as Record<string, { target: number; saved: number; monthly: number }>);

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
                    className="px-4 py-2.5 rounded-full bg-[var(--accent)] text-[var(--accent-fg)] text-sm font-medium transition-default hover:opacity-90 shadow-sm"
                >
                    {showForm ? t("modal_cancel") : t("goals_create_new")}
                </button>
            </div>

            {/* Metrics Dashboard */}
            {goals.length > 0 && !showForm && (
                <div className="flex flex-col gap-4 mb-8">
                    {Object.entries(totalsByCurrency).map(([currency, totals]) => (
                        <div key={currency} className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-fade-in relative">
                            {Object.keys(totalsByCurrency).length > 1 && (
                                <div className="absolute -top-3 left-4 bg-[var(--accent)] text-[var(--accent-fg)] text-[10px] uppercase font-bold px-2 py-0.5 rounded-full shadow-sm z-10">
                                    {currency} {t("nav_goals")}
                                </div>
                            )}
                            <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-4 flex flex-col justify-center">
                                <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider font-semibold mb-1">{t("goals_summary_saved")}</span>
                                <span className="text-2xl font-bold text-[var(--text-primary)]">{totals.saved.toLocaleString("ro-RO")} <span className="text-sm text-[var(--text-secondary)] font-medium">{currency}</span></span>
                            </div>
                            <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-4 flex flex-col justify-center">
                                <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider font-semibold mb-1">{t("goals_summary_target")}</span>
                                <span className="text-2xl font-bold text-[var(--text-primary)]">{totals.target.toLocaleString("ro-RO")} <span className="text-sm text-[var(--text-secondary)] font-medium">{currency}</span></span>
                            </div>
                            <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-4 flex flex-col justify-center">
                                <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider font-semibold mb-1">{t("goals_summary_monthly")}</span>
                                <span className="text-2xl font-bold text-[var(--accent)]">{totals.monthly.toLocaleString("ro-RO")} <span className="text-sm font-medium">{currency}/mo</span></span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Create form */}
            {showForm && (
                <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-6 mb-6 animate-fade-in shadow-sm">
                    <h3 className="font-semibold mb-4 text-[var(--text-primary)]">{t("modal_title")}</h3>
                    <form onSubmit={handleCreate} className="space-y-4">
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                            <div className="lg:col-span-2">
                                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                                    {t("modal_name")}
                                </label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) =>
                                        setFormData({ ...formData, name: e.target.value })
                                    }
                                    placeholder={t("modal_name_placeholder")}
                                    className="w-full px-4 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-all font-medium"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                                    {t("modal_currency") || "Currency"}
                                </label>
                                <select
                                    value={formData.currency || "RON"}
                                    onChange={(e) =>
                                        setFormData({ ...formData, currency: e.target.value })
                                    }
                                    className="w-full px-4 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-all font-medium"
                                >
                                    <option value="RON">RON</option>
                                    <option value="EUR">EUR</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                                    {t("modal_target")}
                                </label>
                                <div className="relative">
                                    <input
                                        type="number"
                                        value={formData.target_amount || ""}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                target_amount: parseFloat(e.target.value) || 0,
                                            })
                                        }
                                        placeholder={t("modal_target_placeholder")}
                                        min="1"
                                        className="w-full pl-4 pr-12 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-all font-medium"
                                        required
                                    />
                                    <div className="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none">
                                        <span className="text-[10px] font-bold text-[var(--text-muted)]">{formData.currency || "RON"}</span>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                                    {t("modal_monthly")}
                                </label>
                                <div className="relative">
                                    <input
                                        type="number"
                                        value={formData.monthly_contribution || ""}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                monthly_contribution: parseFloat(e.target.value) || 0,
                                            })
                                        }
                                        placeholder={t("modal_monthly_placeholder")}
                                        min="0"
                                        className="w-full pl-4 pr-12 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-all font-medium"
                                    />
                                    <div className="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none">
                                        <span className="text-[10px] font-bold text-[var(--text-muted)]">{formData.currency || "RON"}</span>
                                    </div>
                                </div>
                                {formData.target_amount > 0 && formData.monthly_contribution > 0 && (
                                    <p className="mt-2 text-xs text-emerald-600 dark:text-emerald-400 font-medium animate-fade-in">
                                        ✨ {t("goals_form_eta")} {Math.ceil(formData.target_amount / formData.monthly_contribution)} {t("goals_months")}!
                                    </p>
                                )}
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                                    {t("modal_priority")}
                                </label>
                                <select
                                    value={formData.priority}
                                    onChange={(e) =>
                                        setFormData({ ...formData, priority: e.target.value })
                                    }
                                    className="w-full px-4 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-all font-medium"
                                >
                                    <option value="low">{t("priority_low")}</option>
                                    <option value="medium">{t("priority_medium")}</option>
                                    <option value="high">{t("priority_high")}</option>
                                </select>
                            </div>
                        </div>

                        {/* Icon picker */}
                        <div className="pt-2">
                            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">
                                {t("modal_icon")}
                            </label>
                            <div className="flex gap-2.5 flex-wrap">
                                {ICON_CATEGORIES.map(({ icon, key }) => (
                                    <button
                                        key={icon}
                                        type="button"
                                        title={t(key as any)}
                                        onClick={() => setFormData({ ...formData, icon })}
                                        className={`w-11 h-11 rounded-xl text-xl flex items-center justify-center transition-all cursor-pointer transform hover:scale-105 ${formData.icon === icon
                                            ? "bg-[var(--accent)] text-[var(--accent-fg)] ring-2 ring-offset-2 ring-offset-[var(--bg-card)] ring-[var(--accent)] scale-110 shadow-md"
                                            : "bg-[var(--bg-input)] border border-[var(--border)] hover:border-[var(--border-light)] hover:bg-[var(--bg-hover)]"
                                            }`}
                                    >
                                        {icon}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="pt-4 flex justify-end">
                            <button
                                type="submit"
                                className="px-6 py-2.5 rounded-full bg-[var(--accent)] text-[var(--accent-fg)] text-sm font-semibold transition-transform hover:scale-105 shadow-md hover:shadow-lg"
                            >
                                {t("modal_create")}
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Goals grid */}
            {goals.length === 0 && !showForm ? (
                <div className="text-center py-20 animate-fade-in flex flex-col items-center">
                    <div className="mb-6">
                        <Image src="/goals_icon.png" alt="Obiective" width={96} height={96} className="rounded-3xl shadow-lg drop-shadow-sm opacity-90" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2 text-[var(--text-primary)]">{t("goals_no_goals")}</h3>
                    <p className="text-sm text-[var(--text-secondary)] mb-8 max-w-sm">
                        {t("goals_subtitle")}
                    </p>
                    <button
                        onClick={() => setShowForm(true)}
                        className="px-6 py-3 rounded-full bg-[var(--accent)] text-[var(--accent-fg)] text-sm font-semibold transition-transform hover:scale-105 shadow-md flex items-center gap-2"
                    >
                        <span>+</span> {t("goals_create_first")}
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    {goals.map((goal) => {
                        const isCompleted = goal.progress_percent >= 100;
                        const monthsLeft = Math.ceil(goal.remaining_amount / goal.monthly_contribution);
                        const isFinite = monthsLeft > 0 && goal.monthly_contribution > 0;
                        const currency = goal.currency || "RON";

                        let etaDateObj = new Date();
                        if (isFinite) {
                            etaDateObj.setMonth(etaDateObj.getMonth() + monthsLeft);
                        }
                        const etaString = isFinite ? etaDateObj.toLocaleDateString(undefined, { month: 'long', year: 'numeric' }) : null;

                        return (
                            <div
                                key={goal.id}
                                className={`bg-[var(--bg-card)] border-y border-r border-l-4 rounded-2xl p-5 animate-fade-in hover:shadow-md transition-all flex flex-col justify-between ${isCompleted
                                        ? "border-l-emerald-500 border-y-[var(--border)] border-r-[var(--border)]"
                                        : goal.priority === "high"
                                            ? "border-l-red-500 border-y-[var(--border)] border-r-[var(--border)]"
                                            : goal.priority === "medium"
                                                ? "border-l-amber-500 border-y-[var(--border)] border-r-[var(--border)]"
                                                : "border-l-blue-500 border-y-[var(--border)] border-r-[var(--border)]"
                                    }`}
                            >
                                {/* Header */}
                                <div>
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="flex items-center gap-4">
                                            <div
                                                className="w-12 h-12 rounded-2xl bg-[var(--bg-input)] flex items-center justify-center text-2xl shadow-sm border border-[var(--border)] relative"
                                                title={t(ICON_CATEGORIES.find(c => c.icon === goal.icon)?.key as any || "cat_general")}
                                            >
                                                {goal.icon}
                                                <div className="absolute -bottom-1 -right-1 bg-[var(--accent)] text-[var(--accent-fg)] text-[8px] font-bold px-1.5 py-0.5 rounded-md">
                                                    {currency}
                                                </div>
                                            </div>
                                            <div>
                                                <h3 className="font-bold text-[var(--text-primary)] leading-tight">{goal.name}</h3>
                                                <div className="flex items-center gap-2 mt-1.5">
                                                    {isCompleted && (
                                                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400">
                                                            {t("goals_completed")} 🎉
                                                        </span>
                                                    )}
                                                    {!isCompleted && (
                                                        <span
                                                            className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md ${goal.priority === "high"
                                                                ? "bg-red-500/10 text-red-600 dark:bg-red-500/20 dark:text-red-400"
                                                                : goal.priority === "medium"
                                                                    ? "bg-amber-500/10 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400"
                                                                    : "bg-blue-500/10 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400"
                                                                }`}
                                                        >
                                                            {t(`priority_${goal.priority}` as any)}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => handleDelete(goal.id)}
                                            className="text-[var(--text-muted)] hover:text-red-500 p-2 -mr-2 -mt-2 rounded-full transition-colors flex-shrink-0"
                                            title={t("goals_delete")}
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
                                        </button>
                                    </div>

                                    {/* Progress */}
                                    <div className="mb-5">
                                        <div className="flex justify-between items-end mb-2">
                                            <div className="flex flex-col">
                                                <span className="text-[10px] text-[var(--text-muted)] font-semibold uppercase tracking-wider mb-0.5">{t("goals_summary_saved")}</span>
                                                <span className="text-sm font-bold text-[var(--text-primary)]">
                                                    {goal.saved_amount.toLocaleString("ro-RO")} <span className="text-[10px] font-medium text-[var(--text-muted)]">{currency}</span>
                                                </span>
                                            </div>
                                            <div className="flex flex-col items-end">
                                                <span className="text-[10px] text-[var(--text-muted)] font-semibold uppercase tracking-wider mb-0.5">{t("goals_summary_target")}</span>
                                                <span className="text-sm font-bold text-[var(--text-secondary)]">
                                                    {goal.target_amount.toLocaleString("ro-RO")} <span className="text-[10px] font-medium text-[var(--text-muted)]">{currency}</span>
                                                </span>
                                            </div>
                                        </div>
                                        <div className="h-2 bg-[var(--bg-input)] rounded-full overflow-hidden mb-2">
                                            <div
                                                className={`h-full rounded-full transition-all duration-1000 ease-out ${isCompleted ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' : 'bg-gradient-to-r from-blue-500 to-indigo-500'}`}
                                                style={{
                                                    width: `${Math.min(goal.progress_percent, 100)}%`,
                                                }}
                                            />
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className={`text-xs font-bold ${isCompleted ? 'text-emerald-500' : 'text-[var(--accent)]'}`}>
                                                {goal.progress_percent.toFixed(0)}%
                                            </span>
                                            {!isCompleted && isFinite && (
                                                <span className="text-[11px] font-medium text-[var(--text-secondary)] bg-[var(--bg-input)] px-2 py-0.5 rounded-full">
                                                    🎯 {t("goals_on_track")} <span className="font-semibold">{etaString}</span>
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Info text */}
                                    {!isCompleted && goal.monthly_contribution > 0 && (
                                        <p className="text-[11px] text-[var(--text-muted)] mb-4 font-medium flex items-center gap-1.5">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2" /><line x1="16" x2="16" y1="2" y2="6" /><line x1="8" x2="8" y1="2" y2="6" /><line x1="3" x2="21" y1="10" y2="10" /></svg>
                                            {goal.monthly_contribution.toLocaleString("ro-RO")} {currency} {t("goals_monthly")}
                                        </p>
                                    )}
                                </div>

                                {/* Actions / Quick contribute */}
                                {!isCompleted && (
                                    <div className="mt-auto">
                                        {contributeId === goal.id ? (
                                            <div className="flex gap-2 animate-fade-in">
                                                <div className="relative flex-1">
                                                    <input
                                                        type="number"
                                                        value={contributeAmount}
                                                        onChange={(e) => setContributeAmount(e.target.value)}
                                                        placeholder={t("goals_custom_placeholder")}
                                                        min="1"
                                                        autoFocus
                                                        className="w-full pl-3 pr-10 py-2 rounded-xl bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 transition-all font-medium"
                                                        onKeyDown={(e) => {
                                                            if (e.key === 'Enter') handleContribute(goal.id);
                                                        }}
                                                    />
                                                    <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                                                        <span className="text-[10px] font-bold text-[var(--text-muted)]">{currency}</span>
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => handleContribute(goal.id)}
                                                    className="px-4 py-2 rounded-xl bg-[var(--accent)] hover:opacity-90 text-[var(--accent-fg)] text-xs font-bold transition-transform hover:scale-105 shadow-sm"
                                                >
                                                    {t("goals_add_funds")}
                                                </button>
                                                <button
                                                    onClick={() => {
                                                        setContributeId(null);
                                                        setContributeAmount("");
                                                    }}
                                                    className="px-3 py-2 rounded-xl bg-[var(--bg-input)] hover:bg-[var(--border)] text-sm transition-colors text-[var(--text-primary)] font-bold"
                                                >
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
                                                </button>
                                            </div>
                                        ) : (
                                            <div className="grid grid-cols-3 gap-2">
                                                <button
                                                    onClick={() => quickContribute(goal.id, 100)}
                                                    className="py-2 rounded-xl bg-[var(--bg-card)] hover:bg-[var(--bg-hover)] text-xs transition-colors text-[var(--text-primary)] border border-[var(--border)] font-semibold shadow-sm"
                                                >
                                                    +100
                                                </button>
                                                <button
                                                    onClick={() => quickContribute(goal.id, 500)}
                                                    className="py-2 rounded-xl bg-[var(--bg-card)] hover:bg-[var(--bg-hover)] text-xs transition-colors text-[var(--text-primary)] border border-[var(--border)] font-semibold shadow-sm"
                                                >
                                                    +500
                                                </button>
                                                <button
                                                    onClick={() => setContributeId(goal.id)}
                                                    className="py-2 rounded-xl bg-[var(--accent)]/10 hover:bg-[var(--accent)]/20 text-xs transition-colors text-[var(--accent)] border border-[var(--accent)]/20 font-bold"
                                                >
                                                    {t("goals_custom")}
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
