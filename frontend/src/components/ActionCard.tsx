import { AlertTriangle, CheckCircle2, LoaderCircle, ShieldCheck } from "lucide-react";
import { useState } from "react";

import { api } from "../lib/api";
import type { PendingAction } from "../types/api";

export function ActionCard({ action }: { action: PendingAction }) {
  const [status, setStatus] = useState(action.status);
  const [reference, setReference] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const run = async (choice: "confirm" | "cancel") => {
    setBusy(true);
    setError("");
    try {
      if (choice === "confirm") {
        const result = await api.confirmAction(action.id);
        setStatus(result.action.status);
        setReference(result.escalation?.external_reference ?? "");
      } else {
        const result = await api.cancelAction(action.id);
        setStatus(result.status);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Action failed");
    } finally {
      setBusy(false);
    }
  };

  if (status !== "pending") {
    return (
      <div className={`action-complete ${status === "executed" ? "executed" : "cancelled"}`}>
        <CheckCircle2 size={18} />
        <span>{status === "executed" ? `Escalation created${reference ? ` · ${reference}` : ""}` : "Action cancelled"}</span>
      </div>
    );
  }

  return (
    <section className="action-card">
      <div className="action-heading"><ShieldCheck size={20} /><div><strong>Confirmation required</strong><p>No change has been made yet.</p></div></div>
      <p className="action-summary">{action.display_summary}</p>
      <div className="action-warning"><AlertTriangle size={15} /> Review the details before creating this escalation.</div>
      {error && <div className="inline-error">{error}</div>}
      <div className="action-buttons">
        <button className="button secondary" disabled={busy} onClick={() => void run("cancel")}>Cancel</button>
        <button className="button primary" disabled={busy} onClick={() => void run("confirm")}>
          {busy ? <LoaderCircle className="spin" size={16} /> : null} Confirm & create
        </button>
      </div>
    </section>
  );
}
