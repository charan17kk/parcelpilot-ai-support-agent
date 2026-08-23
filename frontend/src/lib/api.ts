import type { Chat, ChatDetail, Message, SourceChunk, User } from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    let message = "Something went wrong. Please try again.";
    try {
      const payload = (await response.json()) as { detail?: string; message?: string };
      message = payload.detail ?? payload.message ?? message;
    } catch {
      // Preserve the safe fallback when an upstream response is not JSON.
    }
    throw new ApiError(response.status, message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ user: User; expires_at: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  me: () => request<User>("/auth/me"),
  listChats: () => request<Chat[]>("/chats"),
  getChat: (id: string) => request<ChatDetail>(`/chats/${id}`),
  createChat: (mode: "customer" | "internal", accountExternalId?: string) =>
    request<Chat>("/chats", {
      method: "POST",
      body: JSON.stringify({ mode, account_external_id: accountExternalId }),
    }),
  sendMessage: (chatId: string, content: string) =>
    request<{ user_message_id: string; assistant_message: Message; snapshot_at: string }>(
      `/chats/${chatId}/messages`,
      { method: "POST", body: JSON.stringify({ content }) },
    ),
  confirmAction: (actionId: string) =>
    request<{ action: { status: string }; escalation?: { external_reference: string } }>(
      `/actions/${actionId}/confirm`,
      { method: "POST" },
    ),
  cancelAction: (actionId: string) =>
    request<{ status: string }>(`/actions/${actionId}/cancel`, {
      method: "POST",
      body: JSON.stringify({ reason: "Cancelled by user" }),
    }),
  source: (documentId: string, chunkId: string) =>
    request<SourceChunk>(`/sources/${documentId}/chunks/${chunkId}`),
};
