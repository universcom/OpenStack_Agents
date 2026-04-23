import { ref, computed } from 'vue'
import type { ChatMessage, AppSettings, StoredMessage } from '../types'
import { sendMessage } from '../api/client'

export function useChat() {
  const messages  = ref<ChatMessage[]>([])
  const sessionId = ref<string | null>(null)
  const isLoading = ref(false)
  const error     = ref<string | null>(null)

  const hasMessages = computed(() => messages.value.length > 0)

  async function send(text: string, settings: AppSettings) {
    if (!text.trim() || isLoading.value) return

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

  function loadSession(saved: StoredMessage[], savedId: string | null) {
    messages.value  = saved.map(m => ({ ...m, timestamp: new Date(m.timestamp) }))
    sessionId.value = savedId
    error.value     = null
  }

  function clearError() {
    error.value = null
  }

  return { messages, sessionId, isLoading, error, hasMessages, send, clearSession, loadSession, clearError }
}
