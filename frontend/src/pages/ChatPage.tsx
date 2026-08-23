import { ArrowUp, BookOpen, Bot, LoaderCircle, ShieldAlert, Sparkles } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { ActionCard } from "../components/ActionCard";
import { AppShell } from "../components/AppShell";
import { SourceDrawer } from "../components/SourceDrawer";
import { ToolTimeline } from "../components/ToolTimeline";
import { TrustBadge } from "../components/TrustBadge";
import { api } from "../lib/api";
import { useAuthStore } from "../store/auth";
import type { Chat, Citation, Message } from "../types/api";

const prompts = {
  customer: ["Can Northstar cancel ORD-1001 without a cancellation fee? Explain why.", "Where is order ORD-1002 right now?", "Create an escalation for my shipment issue."],
  internal: ["A pickup is three hours late because of carrier fault. Should ORD-2002 get a service credit?", "Investigate TKT-501 and tell me its severity and applicable SLA.", "What guidance should we give for the bulk upload failure in TKT-502?"],
};

function temporaryUserMessage(content: string): Message {
  return { id: crypto.randomUUID(), role: "user", content, confidence: null, run_status: "completed", created_at: new Date().toISOString(), citations: [], tool_events: [] };
}

export function ChatPage() {
  const user = useAuthStore((state) => state.user)!;
  const [mode, setMode] = useState<"customer" | "internal">(user.role === "customer" ? "customer" : "internal");
  const [chats, setChats] = useState<Chat[]>([]);
  const [chatId, setChatId] = useState<string>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { api.listChats().then(setChats).catch(() => setError("Could not load conversation history.")); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, sending]);

  const loadChat = async (id: string) => {
    setError("");
    try { const detail = await api.getChat(id); setChatId(id); setMode(detail.chat.mode); setMessages(detail.messages); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load chat"); }
  };

  const newChat = () => { setChatId(undefined); setMessages([]); setError(""); };

  const changeMode = (next: "customer" | "internal") => {
    if (next === "internal" && user.role === "customer") return;
    setMode(next); newChat();
  };

  const send = async (content: string) => {
    const trimmed = content.trim();
    if (!trimmed || sending) return;
    setInput(""); setError(""); setSending(true);
    setMessages((current) => [...current, temporaryUserMessage(trimmed)]);
    try {
      let target = chatId;
      if (!target) {
        const created = await api.createChat(mode, mode === "customer" ? user.accounts[0]?.external_id : undefined);
        target = created.id; setChatId(target); setChats((current) => [created, ...current]);
      }
      const result = await api.sendMessage(target, trimmed);
      setMessages((current) => [...current, result.assistant_message]);
      setChats((current) => current.map((chat) => chat.id === target ? { ...chat, title: chat.title || trimmed.slice(0, 48) } : chat));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The agent could not answer right now.");
    } finally { setSending(false); }
  };

  const submit = (event: FormEvent) => { event.preventDefault(); void send(input); };

  return (
    <AppShell chats={chats} activeChatId={chatId} mode={mode} onModeChange={changeMode} onNewChat={newChat} onSelectChat={(id) => void loadChat(id)}>
      <section className="chat-stage">
        {messages.length === 0 ? (
          <div className="welcome-state">
            <span className="assistant-orb"><Sparkles size={25} /></span>
            <span className="eyebrow">{mode === "customer" ? "Customer support" : "Authorised workspace"}</span>
            <h1>{mode === "customer" ? `How can I help, ${user.display_name.split(" ")[0]}?` : "What should we investigate?"}</h1>
            <p>{mode === "customer" ? "Ask about your shipments, policies, entitlements, or request an escalation." : "Combine policy, agreement, order, and ticket evidence in one investigation."}</p>
            <div className="prompt-grid">{prompts[mode].map((prompt) => <button key={prompt} onClick={() => void send(prompt)}><span>{prompt}</span><ArrowUp size={15} /></button>)}</div>
            <div className="trust-note"><ShieldAlert size={16} /> Answers use the supplied snapshot only. Uncertain cases are flagged for human review.</div>
          </div>
        ) : (
          <div className="message-list">
            {messages.map((message) => (
              <article className={`message ${message.role}`} key={message.id}>
                {message.role === "assistant" && <span className="message-avatar"><Bot size={17} /></span>}
                <div className="message-body">
                  {message.role === "assistant" && <div className="message-label">ParcelPilot Assist <TrustBadge confidence={message.confidence} /></div>}
                  <div className="message-copy"><ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown></div>
                  <ToolTimeline events={message.tool_events} />
                  {message.citations.length > 0 && <div className="citations"><span><BookOpen size={14} /> Sources</span>{message.citations.map((citation, index) => <button key={citation.id ?? index} onClick={() => citation.document_id && setSelectedCitation(citation)} disabled={!citation.document_id}>{index + 1}. {citation.label}</button>)}</div>}
                  {message.pending_action && <ActionCard action={message.pending_action} />}
                </div>
              </article>
            ))}
            {sending && <article className="message assistant"><span className="message-avatar"><Bot size={17} /></span><div className="thinking"><LoaderCircle className="spin" size={17} /><span>Checking the applicable sources and records…</span></div></article>}
            <div ref={endRef} />
          </div>
        )}
        {error && <div className="chat-error">{error}<button onClick={() => setError("")}>Dismiss</button></div>}
        <form className="composer" onSubmit={submit}><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void send(input); } }} placeholder={mode === "customer" ? "Ask about an order, policy, or support request…" : "Investigate an account, order, ticket, policy, or known issue…"} rows={2} /><button aria-label="Send message" disabled={sending || !input.trim()}><ArrowUp size={18} /></button><small>Enter to send · Shift + Enter for a new line</small></form>
      </section>
      <SourceDrawer citation={selectedCitation} />
    </AppShell>
  );
}
