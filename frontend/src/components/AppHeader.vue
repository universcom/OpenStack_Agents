<script setup lang="ts">
import ConnectionPill from './ConnectionPill.vue'

defineProps<{
  isConnected: boolean | null
  isChecking:  boolean
}>()
</script>

<template>
  <header class="flex items-center justify-between px-6 h-14 border-b border-[rgba(255,255,255,0.06)] shrink-0 select-none bg-[#0d0d0d]">
    <div class="flex items-center gap-3">
      <div class="w-7 h-7 rounded-lg bg-cyan-500/[0.12] border border-cyan-500/[0.2] flex items-center justify-center shrink-0">
        <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
      </div>
      <div class="flex items-baseline gap-2">
        <span class="text-[13px] font-semibold text-[#f0f0f0] tracking-tight">OpenStack AI Agent</span>
        <span class="text-[11px] text-[#3a3a3a] hidden sm:inline">Multi-agent infrastructure</span>
      </div>
    </div>

    <ConnectionPill :is-connected="isConnected" :is-checking="isChecking" />
  </header>
</template>
