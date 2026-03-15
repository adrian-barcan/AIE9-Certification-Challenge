/**
 * Centralized API client for the Financial Agent backend.
 * API base is configurable for cloud deployments.
 */
const API_BASE =
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ||
    "http://localhost:8000";

/** Error thrown when chat stream fails. retryable indicates if the user can retry. */
export class ChatStreamError extends Error {
    constructor(
        message: string,
        public readonly retryable: boolean = false
    ) {
        super(message);
        this.name = "ChatStreamError";
    }
}

// ─── Types ───────────────────────────────────────────────────────

export interface User {
    id: string;
    name: string;
    email: string;
    preferred_language: string;
    risk_tolerance: string;
    created_at: string;
}

export interface Goal {
    id: string;
    user_id: string;
    name: string;
    icon: string;
    target_amount: number;
    saved_amount: number;
    monthly_contribution: number;
    deadline: string | null;
    priority: string;
    currency: string;
    status: string;
    notes: string | null;
    progress_percent: number;
    remaining_amount: number;
    created_at: string;
    updated_at: string;
}

export interface GoalCreate {
    name: string;
    icon?: string;
    target_amount: number;
    monthly_contribution?: number;
    deadline?: string;
    priority?: string;
    currency?: string;
    notes?: string;
}

export interface DocumentInfo {
    filename: string;
    chunk_count: number;
    indexed_at: string | null;
}

// ─── Helper ──────────────────────────────────────────────────────

type ApiFetchOptions = RequestInit & {
    timeoutMs?: number;
};

async function apiFetch<T>(path: string, options?: ApiFetchOptions): Promise<T> {
    const timeoutMs = options?.timeoutMs ?? 15000;
    const timeoutController = new AbortController();
    let didTimeout = false;

    const timeoutId = globalThis.setTimeout(() => {
        didTimeout = true;
        timeoutController.abort();
    }, timeoutMs);

    const externalSignal = options?.signal;
    const onExternalAbort = () => timeoutController.abort();
    if (externalSignal) {
        if (externalSignal.aborted) {
            timeoutController.abort();
        } else {
            externalSignal.addEventListener("abort", onExternalAbort);
        }
    }

    try {
        const res = await fetch(`${API_BASE}${path}`, {
            credentials: "include",
            headers: { "Content-Type": "application/json", ...options?.headers },
            ...options,
            signal: timeoutController.signal,
        });
        if (!res.ok) {
            const err = await res.text();
            throw new Error(err || res.statusText);
        }
        return res.json() as Promise<T>;
    } catch (error) {
        if (
            didTimeout &&
            error instanceof DOMException &&
            error.name === "AbortError"
        ) {
            throw new Error("Request timed out. Please try again.");
        }
        throw error;
    } finally {
        globalThis.clearTimeout(timeoutId);
        if (externalSignal) {
            externalSignal.removeEventListener("abort", onExternalAbort);
        }
    }
}

// ─── Auth ────────────────────────────────────────────────────────

export async function register(
    name: string,
    email: string,
    password: string,
    preferred_language: string,
    risk_tolerance: string
): Promise<User> {
    return apiFetch<User>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ name, email, password, preferred_language, risk_tolerance }),
    });
}

export async function login(email: string, password: string): Promise<User> {
    return apiFetch<User>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
    });
}

export async function logout(): Promise<void> {
    await apiFetch<{ status: string }>("/api/auth/logout", { method: "POST" });
}

export async function getMe(signal?: AbortSignal): Promise<User> {
    return apiFetch<User>("/api/auth/me", { signal });
}

// ─── Chat ────────────────────────────────────────────────────────

/**
 * Send a message and stream the response via SSE.
 * Calls onToken for each content token and optionally onStatus when a tool runs (e.g. "Searching documents…").
 * Returns the full assembled response.
 */
export async function sendMessageStream(
    message: string,
    sessionId: string,
    onToken: (token: string) => void,
    onStatus?: (message: string) => void
): Promise<string> {
    const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            message,
            session_id: sessionId,
        }),
    });

    if (!res.ok) {
        const retryable = res.status >= 500 || res.status === 408;
        throw new ChatStreamError(
            res.statusText || "Chat request failed",
            retryable
        );
    }

    const reader = res.body?.getReader();
    if (!reader) throw new Error("No response stream");

    const decoder = new TextDecoder();
    let fullResponse = "";
    let buffer = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");

        // Keep the last chunk in the buffer if it doesn't end with a newline
        buffer = lines.pop() || "";

        for (const line of lines) {
            const trimmedLine = line.trim();
            if (trimmedLine.startsWith("data: ")) {
                try {
                    const data = JSON.parse(trimmedLine.slice(6));
                    if (data.token) {
                        fullResponse += data.token;
                        onToken(data.token);
                    }
                    if (data.status && onStatus) onStatus(data.status);
                    if (data.error) {
                        throw new ChatStreamError(
                            data.error,
                            data.retryable === true
                        );
                    }
                } catch {
                    // Ignore JSON parsing errors for partial lines
                }
            }
        }
    }

    return fullResponse;
}

export async function sendMessageSync(
    message: string,
    sessionId: string
): Promise<string> {
    const data = await apiFetch<{ response: string }>("/api/chat/sync", {
        method: "POST",
        body: JSON.stringify({
            message,
            session_id: sessionId,
        }),
    });
    return data.response;
}

export interface ChatMessage {
    role: string;
    content: string;
    timestamp?: string;
}

export async function getChatHistory(
    sessionId: string
): Promise<ChatMessage[]> {
    return apiFetch<ChatMessage[]>(`/api/chat/history/${sessionId}`);
}

export interface ChatSession {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
}

export async function getChatSessions(): Promise<ChatSession[]> {
    return apiFetch<ChatSession[]>(`/api/chat/sessions`);
}

export async function createChatSession(title?: string): Promise<ChatSession> {
    return apiFetch<ChatSession>("/api/chat/sessions", {
        method: "POST",
        body: JSON.stringify({ title: title || "New Conversation" }),
    });
}

export async function updateChatSession(sessionId: string, title: string): Promise<ChatSession> {
    return apiFetch<ChatSession>(`/api/chat/sessions/${sessionId}`, {
        method: "PATCH",
        body: JSON.stringify({ title }),
    });
}

export async function deleteChatSession(sessionId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/chat/sessions/${sessionId}`, {
        method: "DELETE",
        credentials: "include",
    });
    if (!res.ok) {
        throw new Error("Failed to delete chat session");
    }
}

// ─── Goals ───────────────────────────────────────────────────────

export async function listGoals(): Promise<Goal[]> {
    return apiFetch<Goal[]>(`/api/goals`);
}

export async function createGoal(
    data: GoalCreate
): Promise<Goal> {
    return apiFetch<Goal>(`/api/goals`, {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export async function updateGoal(
    goalId: string,
    data: Partial<GoalCreate>
): Promise<Goal> {
    return apiFetch<Goal>(`/api/goals/${goalId}`, {
        method: "PUT",
        body: JSON.stringify(data),
    });
}

export async function deleteGoal(goalId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/goals/${goalId}`, {
        method: "DELETE",
        credentials: "include",
    });
    if (!res.ok) {
        throw new Error("Failed to delete goal");
    }
}

export async function contributeToGoal(
    goalId: string,
    amount: number
): Promise<Goal> {
    return apiFetch<Goal>(`/api/goals/${goalId}/contribute`, {
        method: "POST",
        body: JSON.stringify({ amount }),
    });
}

// ─── Documents ───────────────────────────────────────────────────

export async function ingestDocuments(): Promise<{
    documents_processed: number;
    total_chunks: number;
    collection: string;
}> {
    return apiFetch("/api/documents/ingest", { method: "POST" });
}

export async function listDocuments(): Promise<DocumentInfo[]> {
    return apiFetch<DocumentInfo[]>("/api/documents");
}

// ─── Transactions ─────────────────────────────────────────────────

export interface TransactionSourceResponse {
    id: string;
    bank_label: string;
    imported_at: string;
    format: string;
    transaction_count?: number;
}

export interface TransactionResponse {
    id: string;
    source_id: string;
    date: string;
    amount: number;
    currency: string;
    category: string;
    is_recurring: boolean;
    created_at: string;
}

export interface TransactionIngestResponse {
    source_id: string;
    transactions_imported: number;
    bank_label: string;
    categorization_source?: string; // "ollama" | "rules"
}

const API_BASE_TRANSACTIONS = API_BASE;

export async function ingestTransactions(
    file: File,
    bankLabel?: string
): Promise<TransactionIngestResponse> {
    const form = new FormData();
    form.append("file", file);
    if (bankLabel) form.append("bank_label", bankLabel);
    const res = await fetch(
        `${API_BASE_TRANSACTIONS}/api/transactions/ingest`,
        { method: "POST", credentials: "include", body: form }
    );
    if (!res.ok) {
        const err = await res.text();
        throw new Error(err || res.statusText);
    }
    return res.json();
}

export async function listTransactionSources(): Promise<TransactionSourceResponse[]> {
    return apiFetch<TransactionSourceResponse[]>(`/api/transactions/sources`);
}

export async function listTransactions(
    params?: { source_id?: string; from_date?: string; to_date?: string; limit?: number }
): Promise<TransactionResponse[]> {
    const search = new URLSearchParams();
    if (params?.source_id) search.set("source_id", params.source_id);
    if (params?.from_date) search.set("from_date", params.from_date);
    if (params?.to_date) search.set("to_date", params.to_date);
    if (params?.limit != null) search.set("limit", String(params.limit));
    return apiFetch<TransactionResponse[]>(`/api/transactions?${search}`);
}

export async function deleteTransactionSource(
    sourceId: string
): Promise<void> {
    const res = await fetch(
        `${API_BASE_TRANSACTIONS}/api/transactions/sources/${sourceId}`,
        { method: "DELETE", credentials: "include" }
    );
    if (!res.ok) throw new Error("Failed to delete source");
}
