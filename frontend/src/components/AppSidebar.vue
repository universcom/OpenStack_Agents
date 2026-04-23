<script setup lang="ts">
import { computed } from 'vue'
import type { SessionEntry } from '../types'

const props = defineProps<{
  sessions: SessionEntry[]
  activeId: string | null
}>()

const emit = defineEmits<{
  'new-chat':       []
  'load-session':   [session: SessionEntry]
  'delete-session': [id: string]
  'clear-all':      []
  'open-settings':  []
}>()

interface Group { label: string; items: SessionEntry[] }

const grouped = computed<Group[]>(() => {
  const todayMs = new Date(new Date().toDateString()).getTime()
  const yestMs  = todayMs - 86_400_000
  const weekMs  = todayMs - 7 * 86_400_000

  const groups: Group[] = [
    { label: 'Today',     items: [] },
    { label: 'Yesterday', items: [] },
    { label: 'This week', items: [] },
    { label: 'Older',     items: [] },
  ]

  for (const s of props.sessions) {
    const t = new Date(s.createdAt).getTime()
    if      (t >= todayMs) groups[0].items.push(s)
    else if (t >= yestMs)  groups[1].items.push(s)
    else if (t >= weekMs)  groups[2].items.push(s)
    else                   groups[3].items.push(s)
  }

  return groups.filter(g => g.items.length > 0)
})
</script>

<template>
  <aside class="w-[220px] shrink-0 bg-[#1c1c1c] border-r border-[rgba(255,255,255,0.12)] flex flex-col overflow-hidden select-none">

    <!-- Brand + New Chat -->
    <div class="px-4 pt-5 pb-3 shrink-0">
      <div class="flex items-center gap-2.5 mb-4">
        <div class="w-7 h-7 rounded-lg bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center shrink-0">
          <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
        </div>
        <span class="text-[13px] font-semibold text-[#f0f0f0] tracking-tight leading-none">OpenStack AI</span>
      </div>

      <button
        @click="$emit('new-chat')"
        class="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-cyan-500 text-white text-[13px] font-semibold hover:bg-cyan-400 transition-all duration-150 shadow-lg shadow-cyan-500/25 active:scale-[0.98]"
      >
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/>
        </svg>
        New Chat
      </button>
    </div>

    <!-- Session list -->
    <div class="flex-1 overflow-y-auto px-2 pb-2">
      <div v-if="sessions.length === 0" class="flex flex-col items-center justify-center py-12 gap-2.5">
        <div class="w-10 h-10 rounded-xl bg-[#272727] border border-[rgba(255,255,255,0.15)] flex items-center justify-center">
          <svg class="w-5 h-5 text-[#999]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
          </svg>
        </div>
        <p class="text-[12px] text-[#c0c0c0] text-center font-medium">No chats yet</p>
        <p class="text-[11px] text-[#888] text-center">Start a conversation above</p>
      </div>

      <template v-for="group in grouped" :key="group.label">
        <p class="text-[10px] font-semibold text-[#aaa] uppercase tracking-[0.1em] px-2 pt-4 pb-1.5">
          {{ group.label }}
        </p>
        <div v-for="session in group.items" :key="session.id" class="relative group">
          <button
            @click="$emit('load-session', session)"
            class="w-full text-left px-2.5 py-2 rounded-lg text-[12.5px] transition-all duration-100 pr-8 leading-snug"
            :class="activeId === session.id
              ? 'bg-cyan-500/[0.15] text-white border border-cyan-500/30'
              : 'text-[#c8c8c8] hover:bg-[rgba(255,255,255,0.08)] hover:text-white'"
          >
            <span class="block truncate">{{ session.title }}</span>
          </button>
          <button
            @click.stop="$emit('delete-session', session.id)"
            class="absolute right-1.5 top-1/2 -translate-y-1/2 w-5 h-5 rounded-md flex items-center justify-center text-[#555] hover:text-red-400 hover:bg-red-400/10 opacity-0 group-hover:opacity-100 transition-all duration-100"
            title="Delete"
          >
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </template>
    </div>

    <!-- Bottom: Clear all + Settings -->
    <div class="shrink-0 p-2 border-t border-[rgba(255,255,255,0.12)] space-y-0.5">
      <button
        v-if="sessions.length > 0"
        @click="$emit('clear-all')"
        class="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[12px] text-[#b0b0b0] hover:text-red-400 hover:bg-red-400/[0.07] transition-all duration-150"
      >
        <svg class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
        </svg>
        Clear all chats
      </button>

      <button
        @click="$emit('open-settings')"
        class="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[12px] text-[#b0b0b0] hover:text-white hover:bg-[rgba(255,255,255,0.08)] transition-all duration-150"
      >
        <svg class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
        </svg>
        Settings
      </button>
    </div>

  </aside>
</template>
