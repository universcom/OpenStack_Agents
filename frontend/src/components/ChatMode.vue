<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import type { AppSettings } from '../types'
import { useChat } from '../composables/useChat'
import MessageBubble from './MessageBubble.vue'

const props = defineProps<{ settings: AppSettings }>()

const { messages, sessionId, isLoading, error, hasMessages, send, clearSession, clearError } = useChat()

// Quick-prompt suggestions shown in the empty state.
const SUGGESTIONS = [
  'List all my running instances',
  'Create a VM with 4 vCPUs and 8GB RAM',
  'What is the current CPU usage?',
  'Why is instance abc-123 in ERROR state?',
]

const inputText    = ref('')
const scrollAnchor = ref<HTMLElement | null>(null)
const textareaRef  = ref<HTMLTextAreaElement | null>(null)

// Scroll to the bottom whenever messages change (new message or loading state).
watch([messages, isLoading], async () => {
  await nextTick()
  scrollAnchor.value?.scrollIntoView({ behavior: 'smooth' })
})

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return
  inputText.value = ''
  resetTextareaHeight()
  await send(text, props.settings)
}

// Enter sends; Shift+Enter inserts a newline.
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// Auto-resize textarea as the user types (up to 8 lines / ~128px).
function handleInput(e: Event) {
  const el = e.target as HTMLTextAreaElement
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 128)}px`
}

function resetTextareaHeight() {
  if (textareaRef.value) textareaRef.value.style.height = 'auto'
}

function fillSuggestion(text: string) {
  inputText.value = text
  textareaRef.value?.focus()
}

// Expose clearSession so App.vue can call it from the sidebar button.
defineExpose({ clearSession })
</script>

<template>
  <div class="flex-1 flex flex-col overflow-hidden">

    <!-- ── Message list ──────────────────────────────────────────────────── -->
    <div class="flex-1 overflow-y-auto px-5 py-5 space-y-4">

      <!-- Empty state with suggestion chips -->
      <div v-if="!hasMessages" class="flex flex-col items-center justify-center h-full gap-5 text-center pb-8">
        <div class="w-14 h-14 rounded-2xl bg-zinc-800 border border-zinc-700 flex items-center justify-center">
          <svg class="w-7 h-7 text-cyan-500/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"/>
          </svg>
        </div>
        <div>
          <p class="text-zinc-200 font-medium">How can I help?</p>
          <p class="text-zinc-500 text-sm mt-1">Ask about your OpenStack infrastructure in plain English.</p>
        </div>
        <!-- Quick-start suggestion chips -->
        <div class="grid grid-cols-2 gap-2 max-w-sm w-full">
          <button
            v-for="s in SUGGESTIONS"
            :key="s"
            @click="fillSuggestion(s)"
            class="text-left text-xs bg-zinc-800/80 border border-zinc-700 rounded-xl px-3 py-2.5 text-zinc-400 hover:border-cyan-500/40 hover:text-zinc-200 hover:bg-zinc-800 transition-colors leading-snug"
          >
            {{ s }}
          </button>
        </div>
      </div>

      <!-- Chat bubbles -->
      <template v-else>
        <MessageBubble
          v-for="msg in messages"
          :key="msg.id"
          :message="msg"
        />

        <!-- Animated "thinking" indicator while waiting for a response -->
        <div v-if="isLoading" class="flex gap-3">
          <div class="w-7 h-7 rounded-full bg-zinc-700 border border-zinc-600 flex items-center justify-center text-[10px] font-bold text-zinc-300 mt-0.5">
            AI
          </div>
          <div class="bg-zinc-800 border border-zinc-700/80 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 rounded-full bg-zinc-400 dot-1"/>
            <span class="w-1.5 h-1.5 rounded-full bg-zinc-400 dot-2"/>
            <span class="w-1.5 h-1.5 rounded-full bg-zinc-400 dot-3"/>
          </div>
        </div>
      </template>

      <!-- Invisible div used as the scroll target -->
      <div ref="scrollAnchor" />
    </div>

    <!-- ── Error banner ──────────────────────────────────────────────────── -->
    <div v-if="error"
      class="mx-4 mb-2 px-4 py-2.5 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3"
    >
      <svg class="w-4 h-4 text-red-400 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
      </svg>
      <div class="flex-1 min-w-0">
        <p class="text-xs font-semibold text-red-400">Request failed</p>
        <p class="text-xs text-red-400/70 mt-0.5 break-words">{{ error }}</p>
      </div>
      <button @click="clearError" class="text-red-400/40 hover:text-red-400 transition-colors shrink-0">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>

    <!-- ── Input bar ─────────────────────────────────────────────────────── -->
    <div class="px-4 pb-4 pt-3 border-t border-zinc-800 bg-zinc-950/60 backdrop-blur-sm shrink-0">
      <div class="flex items-end gap-2">
        <!-- Auto-resizing textarea -->
        <textarea
          ref="textareaRef"
          v-model="inputText"
          @keydown="handleKeydown"
          @input="handleInput"
          placeholder="Ask about your OpenStack infrastructure… (Enter to send)"
          rows="1"
          class="flex-1 bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-600 resize-none focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20 transition-colors leading-6"
          style="min-height:42px; max-height:128px;"
        />

        <!-- Send button -->
        <button
          @click="handleSend"
          :disabled="!inputText.trim() || isLoading"
          class="shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-150"
          :class="inputText.trim() && !isLoading
            ? 'bg-cyan-500 text-white hover:bg-cyan-400 shadow-lg shadow-cyan-500/25 active:scale-95'
            : 'bg-zinc-700 text-zinc-500 cursor-not-allowed'"
          title="Send (Enter)"
        >
          <svg v-if="!isLoading" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
          </svg>
          <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
        </button>
      </div>

      <!-- Session hint -->
      <p class="text-[10px] text-zinc-600 mt-2 font-mono truncate">
        Session:
        <span class="text-zinc-500">{{ sessionId ?? 'none — starts on first message' }}</span>
      </p>
    </div>

  </div>
</template>
