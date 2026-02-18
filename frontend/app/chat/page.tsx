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
    const inputRef = useRef<HTMLInputElement>(null);

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

    const sendMessage = async (text: string) => {
        if (!text.trim() || !user || isStreaming) return;

        const userMsg: Message = { role: "user", content: text.trim() };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsStreaming(true);

        // Add empty assistant message that we'll stream into
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
            inputRef.current?.focus();
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        sendMessage(input);
    };

    const handleStarterClick = (question: string) => {
        sendMessage(question);
    };

    return (
        <div className="flex flex-col h-full relative">
            {/* Messages area */}
            <div className="flex-1 overflow-auto p-4 sm:p-8 scroll-smooth">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full animate-fade-in max-w-2xl mx-auto text-center">
                        <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-3xl flex items-center justify-center text-4xl shadow-xl shadow-indigo-500/20 mb-8">
                            💬
                        </div>
                        <h2 className="text-3xl font-bold mb-3 tracking-tight text-white">
                            {t("chat_greeting")}{user ? `, ${user.name}` : ""}!
                        </h2>
                        <div className="text-[var(--text-secondary)] text-lg mb-12 leading-relaxed whitespace-pre-line">
                            {t("chat_intro")}
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
                            {starterQuestions.map((q) => (
                                <button
                                    key={q}
                                    onClick={() => handleStarterClick(q)}
                                    className="glass-card p-5 text-sm text-left text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-indigo-500/30 hover:bg-white/5 transition-all duration-200 group"
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
                    <div className="max-w-3xl mx-auto space-y-6 pb-24">
                        {messages.map((msg, i) => (
                            <div
                                key={i}
                                className={`animate-fade-in flex ${msg.role === "user" ? "justify-end" : "justify-start"
                                    }`}
                            >
                                <div
                                    className={`max-w-[85%] px-6 py-4 rounded-[2rem] text-[15px] leading-relaxed shadow-sm ${msg.role === "user"
                                            ? "bg-indigo-600 text-white rounded-br-sm shadow-indigo-500/10"
                                            : "glass-card rounded-bl-sm border-white/5 bg-zinc-800/50"
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
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* Input area - Floating */}
            <div className="absolute bottom-6 left-0 right-0 px-4 pointer-events-none">
                <div className="max-w-3xl mx-auto pointer-events-auto">
                    <form
                        onSubmit={handleSubmit}
                        className="glass-card p-2 pl-4 rounded-full flex gap-2 shadow-2xl shadow-black/20 border-white/10 bg-[#18181b]/80 backdrop-blur-xl"
                    >
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={t("chat_input_placeholder")}
                            disabled={isStreaming}
                            className="flex-1 bg-transparent border-none text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none px-2 text-[15px]"
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isStreaming}
                            className="p-3 rounded-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600 text-white transition-all duration-200 shrink-0 shadow-lg shadow-indigo-500/20"
                        >
                            {isStreaming ? (
                                <span className="block w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    viewBox="0 0 24 24"
                                    fill="currentColor"
                                    className="w-5 h-5 translate-x-0.5"
                                >
                                    <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
                                </svg>
                            )}
                        </button>
                    </form>
                    <p className="text-center text-[10px] text-[var(--text-muted)] mt-3 opacity-60">
                        {t("chat_disclaimer")}
                    </p>
                </div>
            </div>
        </div>
    );
}
