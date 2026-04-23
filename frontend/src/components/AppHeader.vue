<script setup lang="ts">
// Connection status is null = not yet checked, true = online, false = offline.
defineProps<{
  isConnected: boolean | null
  isChecking:  boolean
}>()
</script>

<template>
  <header class="flex items-center justify-between px-5 py-3 bg-zinc-900 border-b border-zinc-800 shrink-0 select-none">

    <!-- Brand -->
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-lg bg-cyan-500/15 border border-cyan-500/25 flex items-center justify-center shrink-0">
        <!-- Server/cloud icon -->
        <svg class="w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M5 12H3a9 9 0 1018 0h-2M12 3v9m0 0l-3-3m3 3l3-3" />
        </svg>
      </div>
      <div class="leading-none">
        <p class="text-sm font-semibold text-zinc-100">OpenStack AI Agent</p>
        <p class="text-xs text-zinc-500 mt-0.5">Multi-agent infrastructure management</p>
      </div>
    </div>

    <!-- Connection pill -->
    <div class="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border"
      :class="{
        'border-yellow-500/30 bg-yellow-500/10 text-yellow-400': isChecking,
        'border-green-500/30 bg-green-500/10 text-green-400':   !isChecking && isConnected === true,
        'border-red-500/30   bg-red-500/10   text-red-400':     !isChecking && isConnected === false,
        'border-zinc-700     bg-zinc-800     text-zinc-500':    !isChecking && isConnected === null,
      }"
    >
      <!-- Animated pulse for checking / connected, static for others -->
      <span class="w-1.5 h-1.5 rounded-full"
        :class="{
          'bg-yellow-400 animate-pulse': isChecking,
          'bg-green-400':  !isChecking && isConnected === true,
          'bg-red-400':    !isChecking && isConnected === false,
          'bg-zinc-600':   !isChecking && isConnected === null,
        }"
      />
      <span v-if="isChecking">Checking…</span>
      <span v-else-if="isConnected === true">Connected</span>
      <span v-else-if="isConnected === false">Disconnected</span>
      <span v-else>Not checked</span>
    </div>

  </header>
</template>
