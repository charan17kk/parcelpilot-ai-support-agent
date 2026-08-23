import * as Dialog from "@radix-ui/react-dialog";
import { BookOpen, ExternalLink, X } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../lib/api";
import type { Citation, SourceChunk } from "../types/api";

export function SourceDrawer({ citation }: { citation: Citation | null }) {
  const [source, setSource] = useState<SourceChunk | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setSource(null);
    setError("");
    if (citation?.document_id && citation.chunk_id) {
      api.source(citation.document_id, citation.chunk_id).then(setSource).catch((reason: Error) => {
        setError(reason.message);
      });
    }
  }, [citation]);

  return (
    <Dialog.Root open={Boolean(citation)}>
      <Dialog.Portal>
        <Dialog.Overlay className="drawer-overlay" />
        <Dialog.Content className="source-drawer" aria-describedby={undefined}>
          <header className="drawer-header">
            <div><span className="eyebrow">Evidence</span><Dialog.Title>Source detail</Dialog.Title></div>
            <Dialog.Close className="icon-button" aria-label="Close source"><X size={19} /></Dialog.Close>
          </header>
          {!source && !error && <div className="source-loading">Loading source…</div>}
          {error && <div className="inline-error">{error}</div>}
          {source && (
            <div className="source-content">
              <span className={`source-authority authority-${source.authority_class}`}>
                <BookOpen size={14} /> {source.authority_class.replaceAll("_", " ")}
              </span>
              <h2>{source.title}</h2>
              <div className="source-meta">
                <span>{source.document_type.replaceAll("_", " ")}</span>
                <span>Page {source.page_start}</span>
                {source.version && <span>Version {source.version}</span>}
                <span>{source.status}</span>
              </div>
              {source.section_heading && <h3>{source.section_heading}</h3>}
              <blockquote>{source.excerpt}</blockquote>
              <p className="privacy-note"><ExternalLink size={14} /> This excerpt is access-scoped by the backend.</p>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
