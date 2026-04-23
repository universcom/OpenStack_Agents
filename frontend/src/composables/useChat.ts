import { ref, computed } from 'vue'
import type { ChatMessage, AppSettings } from '../types'
import { sendMessage } from '../api/client'

/**
 * Manages the state and logic for a single interactive chat session.
 *
 * Returns reactive state (messages, loading, error) and two actions:
 *   send()         — appends the user message, calls the API, appends the response.
 *   clearSession() — wipes history and resets the session ID so the next message
 *                    starts a brand-new conversation thread.
 */
export function useChat() {
  const messages  = ref<ChatMessage[]>([])
  const sessionId = ref<string | null>(null)
  const isLoading = ref(false)
  const error     = ref<string | null>(null)

  const hasMessages = computed(() => messages.value.length > 0)

  async function send(text: string, settings: AppSettings) {
    if (!text.trim() || isLoading.value) return

    // Immediately append the user bubble so the UI feels responsive.
    messages.value.push({
      id:        crypto.randomUUID(),
      role:      'user',
      content:   text.trim(),
      timestamp: new Date(),
    })

    isLoading.value = true
    error.value     = null

    try {
      const result = await sendMessage(settings.serverUrl, {
        message:    text.trim(),
        user_id:    settings.userId,
        project_id: settings.projectId || undefined,
        session_id: sessionId.value ?? undefined,
      })

      // Store the returned session ID so subsequent turns share the same thread.
      sessionId.value = result.session_id

      messages.value.push({
        id:                  crypto.randomUUID(),
        role:                'agent',
        content:             result.final_response,
        timestamp:           new Date(),
        success:             result.success,
        hasPendingApprovals: (result.pending_approvals?.length ?? 0) > 0,
      })
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
    } finally {
      isLoading.value = false
    }
  }

  function clearSession() {
    messages.value  = []
    sessionId.value = null
    error.value     = null
  }

  function clearError() {
    error.value = null
  }

  return { messages, sessionId, isLoading, error, hasMessages, send, clearSession, clearError }
}
