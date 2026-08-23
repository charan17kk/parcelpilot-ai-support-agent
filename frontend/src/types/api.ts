export type Account = {
  id: string;
  external_id: string;
  name: string;
  plan: string;
};

export type User = {
  id: string;
  email: string;
  display_name: string;
  role: "customer" | "support_agent" | "operations_manager";
  accounts: Account[];
  permissions: string[];
};

export type Chat = {
  id: string;
  mode: "customer" | "internal";
  title: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type Citation = {
  id?: string;
  document_id?: string;
  chunk_id?: string;
  entity_type?: string;
  entity_id?: string;
  label: string;
  reliability_class: string;
  page_start?: number;
  page_end?: number;
  supports_claim?: string;
};

export type ToolEvent = {
  id?: string;
  tool_name: string;
  status: string;
  input_summary: string;
  output_summary?: string;
  duration_ms?: number;
};

export type PendingAction = {
  id: string;
  action_type: string;
  display_summary: string;
  status: string;
  expires_at: string;
  proposed_payload: Record<string, unknown>;
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  confidence: "high" | "medium" | "low" | null;
  run_status: string;
  created_at: string;
  citations: Citation[];
  tool_events: ToolEvent[];
  pending_action?: PendingAction | null;
};

export type ChatDetail = { chat: Chat; messages: Message[] };

export type SourceChunk = {
  document_id: string;
  chunk_id: string;
  title: string;
  document_type: string;
  version?: string;
  status: string;
  authority_class: string;
  page_start: number;
  page_end: number;
  section_heading?: string;
  excerpt: string;
};
