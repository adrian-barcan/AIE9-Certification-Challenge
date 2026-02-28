"use client";

import { useState, useRef, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { useUser } from "@/lib/UserContext";
import { useLanguage } from "@/lib/LanguageContext";
import { sendMessageStream, getChatSessions, getChatHistory, createChatSession, deleteChatSession, updateChatSession, ChatSession } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Image from "next/image";

interface Message {
    role: "user" | "assistant";
    content: string;
}

export default function ChatPage() {
    const searchParams = useSearchParams();
    const { user } = useUser();
    const { t } = useLanguage();

    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

    useEffect(() => {
        document.title = `${t("nav_chat")} | BaniWise`;
    }, [t]);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");

    // Prefill input from ?q= (e.g. from Transactions "Ask BaniWise where I can save")
    useEffect(() => {
        const q = searchParams.get("q");
        if (q && decodeURIComponent(q).trim()) {
            setInput(decodeURIComponent(q).trim());
        }
    }, [searchParams]);
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamingStatus, setStreamingStatus] = useState<string | null>(null);
    const [isLoadingHistory, setIsLoadingHistory] = useState(false);

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

    // Initialize Sessions
    const isInitializingRef = useRef(false);

    useEffect(() => {
        if (user && !isInitializingRef.current) {
            isInitializingRef.current = true;
            getChatSessions(user.id).then(data => {
                setSessions(data);
                if (data.length > 0) {
                    setCurrentSessionId(data[0].id);
                } else {
                    createNewSession();
                }
            }).catch(err => {
                console.error("Failed to load sessions:", err);
                isInitializingRef.current = false;
            });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user]);

    // Fetch History when session changes
    useEffect(() => {
        if (currentSessionId) {
            setIsLoadingHistory(true);
            getChatHistory(currentSessionId).then(history => {
                setMessages(history.map(m => ({
                    role: m.role as "user" | "assistant",
                    content: m.content
                })));
            }).catch(console.error)
                .finally(() => setIsLoadingHistory(false));
        }
    }, [currentSessionId]);

    const createNewSession = async () => {
        if (!user) return;
        try {
            const newSession = await createChatSession(user.id, "New Conversation");
            setSessions(prev => [newSession, ...prev]);
            setCurrentSessionId(newSession.id);
            setMessages([]);
        } catch (err) {
            console.error("Failed to create session", err);
        }
    };

    const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!confirm("Are you sure you want to delete this chat history?")) return;

        try {
            await deleteChatSession(sessionId);
            setSessions(prev => prev.filter(s => s.id !== sessionId));
            if (currentSessionId === sessionId) {
                const remaining = sessions.filter(s => s.id !== sessionId);
                if (remaining.length > 0) {
                    setCurrentSessionId(remaining[0].id);
                } else {
                    createNewSession();
                }
            }
        } catch (err) {
            console.error("Failed to delete session", err);
        }
    };

    const sendMessage = async (text: string) => {
        if (!text.trim() || !user || isStreaming) return;

        // If no session exists, create one first (failsafe)
        let activeSessionId = currentSessionId;
        if (!activeSessionId) {
            try {
                const newTitle = text.trim().slice(0, 30) + (text.length > 30 ? "..." : "");
                const newSession = await createChatSession(user.id, newTitle);
                setSessions(prev => [newSession, ...prev]);
                setCurrentSessionId(newSession.id);
                activeSessionId = newSession.id;
            } catch (err) {
                console.error("Failsafe session creation failed", err);
                return;
            }
        } else {
            // We have an active session, let's check if it needs auto-titling
            const currentSession = sessions.find(s => s.id === activeSessionId);
            if (currentSession && currentSession.title === "New Conversation" && messages.length === 0) {
                try {
                    const newTitle = text.trim().slice(0, 30) + (text.length > 30 ? "..." : "");
                    await updateChatSession(activeSessionId, newTitle);
                    setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, title: newTitle } : s));
                } catch (err) {
                    console.error("Failed to auto-title session", err);
                }
            }
        }

        const userMsg: Message = { role: "user", content: text.trim() };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsStreaming(true);

        setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

        try {
            await sendMessageStream(
                text.trim(),
                user.id,
                activeSessionId,
                (token) => {
                    setStreamingStatus(null);
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
                },
                (status) => setStreamingStatus(status)
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
            setStreamingStatus(null);
            textareaRef.current?.focus();

            // Optionally, refresh session list to show updated titles
            if (activeSessionId && messages.length === 0) {
                getChatSessions(user.id).then(setSessions).catch(console.error);
            }
        }
    };

    const handleStarterClick = (question: string) => {
        sendMessage(question);
    };

    const hasContent = input.trim().length > 0;
    const userInitial = user?.name?.charAt(0).toUpperCase() || "U";

    return (
        <div className="flex h-full w-full">
            {/* Sessions Sidebar */}
            <div className="w-64 border-r border-[var(--border)] bg-[var(--bg-card)] hidden lg:flex flex-col shrink-0 shadow-sm z-10">
                <div className="p-5 border-b border-[var(--border)] flex justify-between items-center bg-[var(--bg-card)]">
                    <h3 className="font-bold text-sm text-[var(--text-primary)] uppercase tracking-wider">Chat History</h3>
                    <button onClick={createNewSession} className="text-[var(--accent)] hover:bg-[var(--accent)]/10 p-2 rounded-xl transition-all border border-[var(--border)] shadow-sm bg-[var(--bg-card)] hover:scale-105" title="New Chat">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                        </svg>
                    </button>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                    {sessions.length === 0 && <div className="text-xs text-center p-4 text-[var(--text-muted)] font-medium">No previous sessions</div>}
                    {sessions.map(s => (
                        <div key={s.id} className={`w-full text-left rounded-2xl text-sm transition-all flex items-center group mb-1 ${currentSessionId === s.id ? "bg-[var(--accent)]/10 text-[var(--text-primary)] font-bold border border-[var(--accent)]/20 shadow-sm" : "text-[var(--text-secondary)] hover:bg-[var(--bg-input)] hover:text-[var(--text-primary)] border border-transparent font-medium"}`}>
                            <button
                                onClick={() => setCurrentSessionId(s.id)}
                                className="flex-1 px-4 py-3 flex items-center gap-3 truncate"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 shrink-0 text-[var(--accent)]">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
                                </svg>
                                <span className="truncate flex-1 text-left">{s.title || "Conversation"}</span>
                            </button>
                            <button
                                onClick={(e) => handleDeleteSession(s.id, e)}
                                className="opacity-0 group-hover:opacity-100 p-2.5 mr-1 text-[var(--text-muted)] hover:text-red-500 hover:bg-red-500/10 rounded-xl transition-all shrink-0"
                                title="Delete Chat"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                                </svg>
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col h-full relative">
                {/* Messages area */}
                <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8">
                    {isLoadingHistory ? (
                        <div className="flex items-center justify-center h-full">
                            <span className="block w-6 h-6 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
                        </div>
                    ) : messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full animate-fade-in max-w-2xl mx-auto text-center">
                            <div className="mx-auto mb-8 flex items-center justify-center">
                                <Image src="/chat_icon.png" alt="Chat BaniWise" width={80} height={80} className="rounded-3xl shadow-lg drop-shadow-sm opacity-90" />
                            </div>
                            <h2 className="text-3xl font-bold mb-3 tracking-tight text-[var(--text-primary)]">
                                {t("chat_greeting")}{user ? `, ${user.name}` : ""}!
                            </h2>
                            <div className="text-[var(--text-secondary)] text-lg mb-12 leading-relaxed whitespace-pre-line font-medium">
                                {t("chat_intro")}
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
                                {starterQuestions.map((q) => (
                                    <button
                                        key={q}
                                        onClick={() => handleStarterClick(q)}
                                        className="p-5 text-sm font-medium text-left rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--accent)]/50 hover:shadow-md transition-all duration-300 group h-full flex flex-col hover:-translate-y-1"
                                    >
                                        <div className="mb-4 group-hover:scale-110 transition-transform duration-300 opacity-80 group-hover:opacity-100">
                                            <Image src="/lightning_icon.png" alt="Suggestion" width={28} height={28} className="rounded-lg shadow-sm" />
                                        </div>
                                        {q}
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="max-w-3xl mx-auto space-y-5 pb-40 md:pb-32">
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
                                        className={`max-w-[80%] px-5 py-3.5 rounded-3xl text-sm leading-relaxed shadow-sm ${msg.role === "user"
                                            ? "bg-[var(--accent)] text-[var(--accent-fg)] rounded-tr-sm"
                                            : "bg-[var(--bg-card)] text-[var(--text-primary)] border border-[var(--border)] rounded-tl-sm"
                                            }`}
                                    >
                                        {msg.role === "assistant" && isStreaming && i === messages.length - 1 && !msg.content && !streamingStatus ? (
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
                                        ) : msg.role === "assistant" && isStreaming && i === messages.length - 1 && streamingStatus ? (
                                            <span className="text-[var(--text-muted)] italic">{streamingStatus}</span>
                                        ) : (
                                            <div className="prose dark:prose-invert prose-sm max-w-none break-words">
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                    {msg.content}
                                                </ReactMarkdown>
                                            </div>
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
                <div className="absolute bottom-0 left-0 right-0 p-3 pb-6 md:p-4 pointer-events-none">
                    <div className="max-w-3xl mx-auto pointer-events-auto">
                        <div className="flex flex-col rounded-3xl border border-[var(--border)] bg-[var(--bg-card)] shadow-sm focus-within:border-[var(--accent)] focus-within:ring-2 focus-within:ring-[var(--accent)]/20 transition-all duration-200">
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
        </div>
    );
}
