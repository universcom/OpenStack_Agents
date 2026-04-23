<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import type { AppSettings } from '../types'
import { useChat } from '../composables/useChat'
import MessageBubble from './MessageBubble.vue'
import SpinnerIcon   from './SpinnerIcon.vue'
import type { StoredMessage } from '../types'

const props = defineProps<{ settings: AppSettings }>()

const { messages, sessionId, isLoading, error, hasMessages, send, clearSession, loadSession, clearError } = useChat()

const SUGGESTIONS = [
  'List all my running instances',
  'Create a VM with 4 vCPUs and 8 GB RAM',
  'What is the current CPU usage?',
  'Why is instance abc-123 in ERROR state?',
]

const inputText    = ref('')
const scrollAnchor = ref<HTMLElement | null>(null)
const textareaRef  = ref<HTMLTextAreaElement | null>(null)

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

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handleInput(e: Event) {
  const el = e.target as HTMLTextAreaElement
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`
}

function resetTextareaHeight() {
  if (textareaRef.value) textareaRef.value.style.height = 'auto'
}

function fillSuggestion(text: string) {
  inputText.value = text
  textareaRef.value?.focus()
}

defineExpose({
  clearSession,
  loadSession: (msgs: StoredMessage[], sid: string | null) => loadSession(msgs, sid),
  getMessages:  () => messages.value,
  getSessionId: () => sessionId.value,
})
</script>

<template>
  <div class="flex-1 flex flex-col overflow-hidden">

    <div class="flex-1 overflow-y-auto">
      <div class="min-h-full flex flex-col max-w-3xl mx-auto px-6">

        <div v-if="!hasMessages" class="flex-1 flex flex-col items-center justify-center text-center gap-8 py-20">
          <div>
            <div class="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center mx-auto mb-5">
              <svg class="w-8 h-8 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round"
                  d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
            <h2 class="text-[22px] font-semibold text-[#f0f0f0] tracking-tight">How can I help?</h2>
            <p class="text-[14px] text-[#c8c8c8] mt-2">Ask about your OpenStack infrastructure in plain English.</p>
          </div>

          <div class="flex flex-wrap justify-center gap-2 max-w-lg">
            <button
              v-for="s in SUGGESTIONS"
              :key="s"
              @click="fillSuggestion(s)"
              class="text-[13px] bg-[#272727] border border-[rgba(255,255,255,0.18)] rounded-xl px-4 py-2.5 text-[#d0d0d0] hover:text-white hover:border-cyan-500/50 hover:bg-cyan-500/[0.08] transition-all duration-150"
            >
              {{ s }}
            </button>
          </div>
        </div>

        <template v-else>
          <div class="py-6 space-y-1">
            <MessageBubble
              v-for="msg in messages"
              :key="msg.id"
              :message="msg"
            />

            <div v-if="isLoading" class="flex gap-4 py-4">
              <div class="w-7 h-7 rounded-full bg-cyan-500/[0.1] border border-cyan-500/[0.18] flex items-center justify-center shrink-0 mt-0.5">
                <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
              <div class="flex items-center gap-1.5 py-1">
                <span class="w-1.5 h-1.5 rounded-full bg-[#666] dot-1"/>
                <span class="w-1.5 h-1.5 rounded-full bg-[#666] dot-2"/>
                <span class="w-1.5 h-1.5 rounded-full bg-[#666] dot-3"/>
              </div>
            </div>
          </div>
        </template>

        <div ref="scrollAnchor" />
      </div>
    </div>

    <div v-if="error" class="max-w-3xl mx-auto w-full px-6 mb-2">
      <div class="px-4 py-3 bg-red-500/[0.07] border border-red-500/[0.15] rounded-xl flex items-start gap-3">
        <svg class="w-4 h-4 text-red-400 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
        </svg>
        <div class="flex-1 min-w-0">
          <p class="text-[12px] font-semibold text-red-400">Request failed</p>
          <p class="text-[12px] text-red-400/60 mt-0.5 break-words">{{ error }}</p>
        </div>
        <button @click="clearError" class="text-red-400/30 hover:text-red-400 transition-colors shrink-0">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
    </div>

    <div class="px-6 pb-5 pt-2 shrink-0">
      <div class="max-w-3xl mx-auto">
        <div class="input-card p-4">
          <textarea
            ref="textareaRef"
            v-model="inputText"
            @keydown="handleKeydown"
            @input="handleInput"
            placeholder="Ask about your OpenStack infrastructure…"
            rows="1"
            class="w-full bg-transparent text-[15px] text-[#f0f0f0] placeholder-[#888] resize-none focus:outline-none leading-relaxed"
            style="min-height: 28px; max-height: 160px;"
          />
          <div class="flex items-center justify-between mt-3">
            <p class="text-[11px] text-[#888] font-mono truncate">
              {{ sessionId ? `session · ${sessionId.slice(0, 16)}…` : 'Enter to send · Shift+Enter for newline' }}
            </p>
            <button
              @click="handleSend"
              :disabled="!inputText.trim() || isLoading"
              class="shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-150"
              :class="inputText.trim() && !isLoading
                ? 'bg-cyan-500 text-white hover:bg-cyan-400 shadow-md shadow-cyan-500/20 active:scale-95'
                : 'bg-[#252525] text-[#555] cursor-not-allowed'"
              title="Send (Enter)"
            >
              <SpinnerIcon v-if="isLoading" class="w-3.5 h-3.5" />
              <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>
