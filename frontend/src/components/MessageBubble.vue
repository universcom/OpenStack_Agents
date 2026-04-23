<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { ChatMessage } from '../types'

const props = defineProps<{ message: ChatMessage }>()

const isUser = computed(() => props.message.role === 'user')

// Parse agent responses as Markdown so code blocks, lists, and headings render.
// Synchronous by default in marked; cast removes the spurious Promise overload.
const htmlContent = computed(() =>
  isUser.value ? null : (marked.parse(props.message.content) as string)
)

function fmtTime(d: Date) {
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="flex gap-3" :class="isUser ? 'flex-row-reverse' : 'flex-row'">

    <!-- Avatar circle -->
    <div
      class="shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold mt-0.5"
      :class="isUser
        ? 'bg-cyan-500/20 border border-cyan-500/40 text-cyan-300'
        : 'bg-zinc-700  border border-zinc-600  text-zinc-300'"
    >
      {{ isUser ? 'YOU' : 'AI' }}
    </div>

    <!-- Content column -->
    <div class="flex flex-col gap-1" :class="isUser ? 'items-end max-w-[75%]' : 'items-start max-w-[85%]'">

      <!-- Bubble -->
      <div
        class="rounded-2xl px-4 py-2.5 text-sm leading-relaxed"
        :class="isUser
          ? 'bg-cyan-600/90 text-white rounded-tr-sm'
          : 'bg-zinc-800 border border-zinc-700/80 text-zinc-200 rounded-tl-sm'"
      >
        <!-- User: plain text (no Markdown needed) -->
        <p v-if="isUser" class="whitespace-pre-wrap break-words">{{ message.content }}</p>

        <!-- Agent: Markdown rendered into HTML -->
        <div
          v-else
          class="prose prose-sm prose-chat max-w-none"
          v-html="htmlContent"
        />
      </div>

      <!-- Status badges (agent only) -->
      <div v-if="!isUser && (message.hasPendingApprovals || message.success === false)" class="flex flex-wrap gap-1.5">
        <span
          v-if="message.hasPendingApprovals"
          class="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-yellow-400/10 border border-yellow-400/25 text-yellow-300"
        >
          <!-- Warning triangle icon -->
          <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
          </svg>
          Approval required
        </span>

        <span
          v-if="message.success === false"
          class="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-red-400/10 border border-red-400/25 text-red-300"
        >
          <!-- X circle icon -->
          <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
          </svg>
          Agent error
        </span>
      </div>

      <!-- Timestamp -->
      <span class="text-[10px] text-zinc-600 px-1">{{ fmtTime(message.timestamp) }}</span>

    </div>
  </div>
</template>
