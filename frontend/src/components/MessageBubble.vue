<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { ChatMessage } from '../types'
import StatusBadge from './StatusBadge.vue'

const props = defineProps<{ message: ChatMessage }>()

const isUser = computed(() => props.message.role === 'user')

const htmlContent = computed(() =>
  isUser.value ? null : (marked.parse(props.message.content) as string)
)

function fmtTime(d: Date) {
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div v-if="isUser" class="flex justify-end py-3 msg-in">
    <div class="max-w-[72%]">
      <div class="bg-[#252525] border border-[rgba(255,255,255,0.1)] rounded-2xl rounded-br-sm px-4 py-3">
        <p class="text-[15px] text-[#f0f0f0] leading-relaxed whitespace-pre-wrap break-words">{{ message.content }}</p>
      </div>
      <p class="text-[10px] text-[#888] mt-1.5 text-right pr-1">{{ fmtTime(message.timestamp) }}</p>
    </div>
  </div>

  <div v-else class="flex gap-4 py-3 msg-in">
    <div class="w-7 h-7 rounded-full bg-cyan-500/[0.1] border border-cyan-500/[0.18] flex items-center justify-center shrink-0 mt-0.5">
      <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
        <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
      </svg>
    </div>

    <div class="flex-1 min-w-0">
      <div class="prose prose-sm prose-chat max-w-none text-[15px] leading-relaxed" v-html="htmlContent" />

      <div v-if="message.hasPendingApprovals || message.success === false" class="flex flex-wrap gap-1.5 mt-3">
        <StatusBadge v-if="message.hasPendingApprovals" variant="warning">Approval required</StatusBadge>
        <StatusBadge v-if="message.success === false"   variant="error">Agent error</StatusBadge>
      </div>

      <p class="text-[10px] text-[#888] mt-2">{{ fmtTime(message.timestamp) }}</p>
    </div>
  </div>
</template>
