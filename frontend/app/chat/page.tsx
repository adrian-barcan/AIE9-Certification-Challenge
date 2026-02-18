"use client";

import { useState, useRef, useEffect } from "react";
import { useUser } from "@/lib/UserContext";
import { useLanguage } from "@/lib/LanguageContext";
import { sendMessageStream } from "@/lib/api";

interface Message {
    role: "user" | "assistant";
    content: string;
}

export default function ChatPage() {
    const { user } = useUser();
    const { t } = useLanguage();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isStreaming, setIsStreaming] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const starterQuestions = [
        t("q_tezaur"),
        t("q_fidelis"),
        t("q_goals"),
        t("q_invest"),
    ];

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            const scrollHeight = textareaRef.current.scrollHeight;
            const maxHeight = 12 * 24; // 12 lines
            if (scrollHeight <= maxHeight) {
                textareaRef.current.style.height = `${Math.max(24, scrollHeight)}px`;
                textareaRef.current.style.overflowY = "hidden";
            } else {
                textareaRef.current.style.height = `${maxHeight}px`;
                textareaRef.current.style.overflowY = "auto";
            }
        }
    }, [input]);

    const sendMessage = async (text: string) => {
        if (!text.trim() || !user || isStreaming) return;

        const userMsg: Message = { role: "user", content: text.trim() };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsStreaming(true);

        setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

        try {
            await sendMessageStream(
                text.trim(),
                user.id,
                "default",
                (token) => {
                    setMessages((prev) => {
                        const updated = [...prev];
                        const last = updated[updated.length - 1];
                        if (last.role === "assistant") {
                            updated[updated.length - 1] = {
                                ...last,
                                content: last.content + token,
                            };
                        }
                        return updated;
                    });
                }
            );
        } catch {
            setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last.role === "assistant" && !last.content) {
                    updated[updated.length - 1] = {
                        ...last,
                        content: t("chat_error_connect"),
                    };
                }
                return updated;
            });
        } finally {
            setIsStreaming(false);
            textareaRef.current?.focus();
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        sendMessage(input);
    };

    const handleStarterClick = (question: string) => {
        sendMessage(question);
    };

    const hasContent = input.trim().length > 0;
    const userInitial = user?.name?.charAt(0).toUpperCase() || "U";

    return (
        <div className="flex flex-col h-full relative">
            {/* Messages area */}
            <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full animate-fade-in max-w-2xl mx-auto text-center">
                        <div className="w-16 h-16 bg-[var(--accent)] rounded-2xl flex items-center justify-center text-3xl shadow-sm text-[var(--accent-fg)] mb-8">
                            💬
                        </div>
                        <h2 className="text-2xl font-semibold mb-3 tracking-tight text-[var(--text-primary)]">
                            {t("chat_greeting")}{user ? `, ${user.name}` : ""}!
                        </h2>
                        <div className="text-[var(--text-secondary)] text-base mb-12 leading-relaxed whitespace-pre-line">
                            {t("chat_intro")}
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
                            {starterQuestions.map((q) => (
                                <button
                                    key={q}
                                    onClick={() => handleStarterClick(q)}
                                    className="p-5 text-sm text-left rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-light)] hover:shadow-sm transition-all duration-200 group h-full flex flex-col"
                                >
                                    <span className="block mb-2 text-xl group-hover:scale-110 transition-transform duration-200 w-fit">
                                        ⚡
                                    </span>
                                    {q}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="max-w-3xl mx-auto space-y-5 pb-32">
                        {messages.map((msg, i) => (
                            <div
                                key={i}
                                className={`animate-fade-in flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"
                                    }`}
                            >
                                {/* Assistant avatar */}
                                {msg.role === "assistant" && (
                                    <div className="mt-0.5 shrink-0 w-7 h-7 rounded-full bg-[var(--accent)] flex items-center justify-center text-[10px] font-bold text-[var(--accent-fg)]">
                                        AI
                                    </div>
                                )}
                                <div
                                    className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm ${msg.role === "user"
                                        ? "bg-[var(--accent)] text-[var(--accent-fg)]"
                                        : "bg-[var(--bg-card)] text-[var(--text-primary)] border border-[var(--border)]"
                                        }`}
                                >
                                    {msg.role === "assistant" && !msg.content && isStreaming ? (
                                        <div className="flex gap-1.5 py-1 px-1">
                                            <div className="w-2 h-2 rounded-full bg-current opacity-40 typing-dot" />
                                            <div
                                                className="w-2 h-2 rounded-full bg-current opacity-40 typing-dot"
                                                style={{ animationDelay: "0.2s" }}
                                            />
                                            <div
                                                className="w-2 h-2 rounded-full bg-current opacity-40 typing-dot"
                                                style={{ animationDelay: "0.4s" }}
                                            />
                                        </div>
                                    ) : (
                                        <div className="whitespace-pre-wrap">{msg.content}</div>
                                    )}
                                </div>
                                {/* User avatar */}
                                {msg.role === "user" && (
                                    <div className="mt-0.5 shrink-0 w-7 h-7 rounded-full bg-[var(--accent)] flex items-center justify-center text-[10px] font-bold text-[var(--accent-fg)]">
                                        {userInitial}
                                    </div>
                                )}
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* Composer — floating at bottom */}
            <div className="absolute bottom-0 left-0 right-0 p-4 pointer-events-none">
                <div className="max-w-3xl mx-auto pointer-events-auto">
                    <div className="flex flex-col rounded-3xl border border-[var(--border)] bg-[var(--bg-card)] shadow-sm">
                        {/* Textarea */}
                        <div className="flex-1 px-4 pt-4 pb-2">
                            <textarea
                                ref={textareaRef}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder={t("chat_input_placeholder")}
                                disabled={isStreaming}
                                rows={1}
                                className="w-full resize-none bg-transparent text-sm outline-none placeholder:text-[var(--text-muted)] min-h-[24px] leading-6 text-[var(--text-primary)]"
                                onKeyDown={(e) => {
                                    if (e.key === "Enter" && !e.shiftKey) {
                                        e.preventDefault();
                                        sendMessage(input);
                                    }
                                }}
                            />
                        </div>

                        {/* Bottom toolbar */}
                        <div className="flex items-center justify-end px-3 pb-3">
                            <button
                                onClick={() => sendMessage(input)}
                                disabled={!hasContent || isStreaming}
                                className={`inline-flex shrink-0 items-center justify-center rounded-full p-2.5 transition-colors ${hasContent
                                    ? "bg-[var(--accent)] text-[var(--accent-fg)] hover:opacity-90"
                                    : "bg-[var(--bg-input)] text-[var(--text-muted)] cursor-not-allowed"
                                    }`}
                            >
                                {isStreaming ? (
                                    <span className="block w-5 h-5 border-2 border-current/30 border-t-current rounded-full animate-spin" />
                                ) : (
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        viewBox="0 0 24 24"
                                        fill="currentColor"
                                        className="w-5 h-5"
                                    >
                                        <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
                                    </svg>
                                )}
                            </button>
                        </div>
                    </div>

                    <p className="text-center text-[11px] text-[var(--text-muted)] mt-2">
                        {t("chat_disclaimer")}
                    </p>
                </div>
            </div>
        </div>
    );
}
