<script setup lang="ts">
defineProps<{
  isConnected: boolean | null
  isChecking:  boolean
}>()
</script>

<template>
  <div
    class="flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-full border font-medium transition-colors"
    :class="{
      'border-yellow-500/25 bg-yellow-500/[0.07] text-yellow-400': isChecking,
      'border-green-500/25  bg-green-500/[0.07]  text-green-400':  !isChecking && isConnected === true,
      'border-red-500/25    bg-red-500/[0.07]    text-red-400':    !isChecking && isConnected === false,
      'border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.02)] text-[#444]': !isChecking && isConnected === null,
    }"
  >
    <span
      class="w-1.5 h-1.5 rounded-full"
      :class="{
        'bg-yellow-400 animate-pulse': isChecking,
        'bg-green-400':  !isChecking && isConnected === true,
        'bg-red-400':    !isChecking && isConnected === false,
        'bg-[#333]':     !isChecking && isConnected === null,
      }"
    />
    <span v-if="isChecking">Checking…</span>
    <span v-else-if="isConnected === true">Connected</span>
    <span v-else-if="isConnected === false">Disconnected</span>
    <span v-else>Not checked</span>
  </div>
</template>
