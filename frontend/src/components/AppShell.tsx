import { Bot, ChevronDown, LogOut, MessageSquarePlus, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

import { useAuthStore } from "../store/auth";
import type { Chat } from "../types/api";

type Props = {
  chats: Chat[];
  activeChatId?: string;
  mode: "customer" | "internal";
  onModeChange: (mode: "customer" | "internal") => void;
  onNewChat: () => void;
  onSelectChat: (id: string) => void;
  children: ReactNode;
};

export function AppShell(props: Props) {
  const { user, signOut } = useAuthStore();
  const canUseInternal = user?.role !== "customer";
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark"><Bot size={21} /></span><span>ParcelPilot <small>Assist</small></span></div>
        <button className="new-chat" onClick={props.onNewChat}><MessageSquarePlus size={17} /> New conversation</button>
        <nav className="chat-history" aria-label="Conversation history">
          <p className="nav-label">Recent</p>
          {props.chats.length === 0 && <p className="nav-empty">Your conversations will appear here.</p>}
          {props.chats.map((chat) => (
            <button className={chat.id === props.activeChatId ? "active" : ""} key={chat.id} onClick={() => props.onSelectChat(chat.id)}>
              <span>{chat.title || "Support conversation"}</span><small>{chat.mode}</small>
            </button>
          ))}
        </nav>
        <div className="user-card">
          <span className="avatar">{user?.display_name.slice(0, 1)}</span>
          <div><strong>{user?.display_name}</strong><small>{user?.role.replaceAll("_", " ")}</small></div>
          <button aria-label="Sign out" onClick={() => void signOut()}><LogOut size={16} /></button>
        </div>
      </aside>
      <main className="workspace">
        <header className="topbar">
          <div className="mode-switch">
            <button className={props.mode === "customer" ? "active" : ""} onClick={() => props.onModeChange("customer")}>Customer support</button>
            {canUseInternal && <button className={props.mode === "internal" ? "active" : ""} onClick={() => props.onModeChange("internal")}><ShieldCheck size={14} /> Internal operations</button>}
          </div>
          <div className="account-context"><span className="status-dot" /> Data snapshot · 16 Aug 2026 <ChevronDown size={14} /></div>
        </header>
        {props.children}
      </main>
    </div>
  );
}
