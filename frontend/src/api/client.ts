import type { ChatRequest, ChatResponse } from '../types'

// Strips trailing slash so callers don't need to worry about it.
function base(url: string) {
  return url.replace(/\/$/, '')
}

/**
 * POST /chat — send one message and receive the agent's structured response.
 * Throws an Error (with a human-readable message) on non-2xx responses.
 */
export async function sendMessage(
  serverUrl: string,
  req: ChatRequest,
): Promise<ChatResponse> {
  const res = await fetch(`${base(serverUrl)}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })

  if (!res.ok) {
    // Try to read the error body for a useful message; fall back to status text.
    const body = await res.text().catch(() => res.statusText)
    throw new Error(`Server ${res.status}: ${body}`)
  }

  return res.json() as Promise<ChatResponse>
}

/**
 * GET /health — quick liveness check.
 * Returns true if the server responds with HTTP 200, false for anything else
 * including network errors and timeouts (3 second limit).
 */
export async function checkHealth(serverUrl: string): Promise<boolean> {
  try {
    const res = await fetch(`${base(serverUrl)}/health`, {
      signal: AbortSignal.timeout(3000),
    })
    return res.ok
  } catch {
    return false
  }
}
