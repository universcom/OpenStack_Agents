// ── Domain types ──────────────────────────────────────────────────────────────

/** A single message in the chat history (either from the user or the agent). */
export interface ChatMessage {
  id: string
  role: 'user' | 'agent'
  content: string
  timestamp: Date
  /** false only when the orchestrator explicitly reports a failure. */
  success?: boolean
  /** true when the orchestrator queued actions waiting for user approval. */
  hasPendingApprovals?: boolean
}

// ── API types (mirrors FastAPI /chat endpoint) ────────────────────────────────

/** Body sent to POST /chat */
export interface ChatRequest {
  message: string
  user_id: string
  project_id?: string
  session_id?: string
}

/** Body returned by POST /chat */
export interface ChatResponse {
  final_response: string
  session_id: string
  success: boolean
  pending_approvals?: unknown[]
}

// ── Session history types ─────────────────────────────────────────────────────

/** Serialised form of ChatMessage stored in localStorage (Date → ISO string). */
export interface StoredMessage {
  id: string
  role: 'user' | 'agent'
  content: string
  timestamp: string
  success?: boolean
  hasPendingApprovals?: boolean
}

/** One entry in the local chat history list. */
export interface SessionEntry {
  id: string               // local UUID (not the backend session_id)
  sessionId: string | null // backend session_id
  title: string            // first user message, truncated
  createdAt: string        // ISO string
  messages: StoredMessage[]
}

// ── UI state types ────────────────────────────────────────────────────────────

/** User-configurable connection and identity settings. */
export interface AppSettings {
  serverUrl: string
  userId: string
  projectId: string
}

/** One demo prompt + its in-progress or completed response. */
export interface DemoPair {
  message: string
  userId: string
  projectId: string
  response: ChatMessage | null
  loading: boolean
}
