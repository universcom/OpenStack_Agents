import { ref } from 'vue'
import type { SessionEntry, ChatMessage } from '../types'

const STORAGE_KEY = 'openstack-chat-sessions'

function read(): SessionEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as SessionEntry[]) : []
  } catch {
    return []
  }
}

function write(sessions: SessionEntry[]) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions)) } catch { /* quota */ }
}

// Module-level so all callers share the same reactive list.
const sessions = ref<SessionEntry[]>(read())

export function useSessionHistory() {
  function save(sessionId: string | null, messages: ChatMessage[]) {
    if (!messages.length) return

    const existingIdx = sessionId
      ? sessions.value.findIndex(s => s.sessionId === sessionId)
      : -1

    const title = messages.find(m => m.role === 'user')?.content.slice(0, 60) ?? 'New chat'

    const entry: SessionEntry = {
      id:        existingIdx >= 0 ? sessions.value[existingIdx].id : crypto.randomUUID(),
      sessionId,
      title,
      createdAt: existingIdx >= 0 ? sessions.value[existingIdx].createdAt : new Date().toISOString(),
      messages:  messages.map(m => ({
        id:                  m.id,
        role:                m.role,
        content:             m.content,
        timestamp:           m.timestamp.toISOString(),
        success:             m.success,
        hasPendingApprovals: m.hasPendingApprovals,
      })),
    }

    if (existingIdx >= 0) {
      sessions.value[existingIdx] = entry
    } else {
      sessions.value.unshift(entry)
      if (sessions.value.length > 100) sessions.value = sessions.value.slice(0, 100)
    }

    write(sessions.value)
  }

  function remove(id: string) {
    sessions.value = sessions.value.filter(s => s.id !== id)
    write(sessions.value)
  }

  function clearAll() {
    sessions.value = []
    write([])
  }

  return { sessions, save, remove, clearAll }
}
