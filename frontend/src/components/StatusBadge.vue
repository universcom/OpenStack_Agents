<script setup lang="ts">
defineProps<{ variant: 'warning' | 'error' }>()
</script>

<template>
  <span
    class="inline-flex items-center gap-1 text-[11px] font-medium px-2.5 py-1 rounded-full"
    :class="{
      'bg-yellow-400/[0.08] border border-yellow-400/[0.18] text-yellow-400': variant === 'warning',
      'bg-red-400/[0.08]    border border-red-400/[0.18]    text-red-400':    variant === 'error',
    }"
  >
    <svg v-if="variant === 'warning'" class="w-3 h-3 shrink-0" fill="currentColor" viewBox="0 0 20 20">
      <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
    </svg>
    <svg v-else class="w-3 h-3 shrink-0" fill="currentColor" viewBox="0 0 20 20">
      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
    </svg>
    <slot />
  </span>
</template>
