<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { AppSettings } from '../types'
import { useDemo } from '../composables/useDemo'
import SpinnerIcon from './SpinnerIcon.vue'
import StatusBadge from './StatusBadge.vue'

const props = defineProps<{ settings: AppSettings }>()

const { pairs, isRunning, isDone, currentIndex, run, reset } = useDemo()

const completedCount = computed(() => pairs.value.filter(p => !p.loading).length)

function renderMd(text: string): string {
  return marked.parse(text) as string
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-hidden">

    <div class="flex items-center justify-between px-6 py-4 border-b border-[rgba(255,255,255,0.12)] shrink-0 bg-[#141414]">
      <div>
        <p class="text-[14px] font-semibold text-[#f0f0f0]">Demo Run</p>
        <p class="text-[12px] text-[#aaa] mt-0.5">5 scripted prompts run sequentially — no interaction needed.</p>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="isRunning" class="text-[12px] text-[#aaa] font-mono tabular-nums">
          {{ completedCount }}&thinsp;/&thinsp;{{ pairs.length }}
        </span>
        <button
          @click="isDone ? reset() : run(props.settings)"
          :disabled="isRunning"
          class="flex items-center gap-2 px-4 py-2 rounded-xl text-[12px] font-semibold transition-all duration-150"
          :class="isRunning
            ? 'bg-[#1a1a1a] text-[#333] cursor-not-allowed border border-[rgba(255,255,255,0.04)]'
            : 'bg-cyan-500 text-white hover:bg-cyan-400 shadow-md shadow-cyan-500/20 active:scale-95'"
        >
          <SpinnerIcon v-if="isRunning" class="w-3.5 h-3.5" />
          <svg v-else-if="isDone" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
          <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          {{ isRunning ? 'Running…' : isDone ? 'Run Again' : 'Run Demo' }}
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-6 py-6 space-y-4">

      <div v-if="!isRunning && !isDone && pairs.length === 0"
        class="flex flex-col items-center justify-center h-full gap-6 text-center pb-8"
      >
        <div class="w-14 h-14 rounded-2xl bg-[#1a1a1a] border border-[rgba(255,255,255,0.07)] flex items-center justify-center">
          <svg class="w-7 h-7 text-cyan-400/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <div>
          <p class="text-[16px] font-semibold text-[#f0f0f0]">Ready to demo</p>
          <p class="text-[13px] text-[#bbb] mt-1.5 max-w-sm">
            Runs 5 prompts covering VM listing, creation, monitoring, diagnostics, and recommendations.
          </p>
        </div>
        <ol class="text-left space-y-2.5 max-w-sm w-full">
          <li
            v-for="(p, i) in ['List all running instances', 'Create a VM (web-server-01)', 'CPU usage of the cluster', 'Diagnose instance in ERROR', 'Performance recommendations']"
            :key="i"
            class="flex items-center gap-3 text-[13px] text-[#c0c0c0]"
          >
            <span class="shrink-0 w-5 h-5 rounded-full bg-[#2a2a2a] border border-[rgba(255,255,255,0.15)] flex items-center justify-center text-[10px] font-mono text-[#999]">
              {{ i + 1 }}
            </span>
            {{ p }}
          </li>
        </ol>
      </div>

      <div
        v-for="(pair, idx) in pairs"
        :key="idx"
        class="rounded-2xl border overflow-hidden transition-all duration-300 msg-in"
        :class="{
          'border-cyan-500/30 shadow-lg shadow-cyan-500/[0.04]': idx === currentIndex && isRunning,
          'border-[rgba(255,255,255,0.1)]': idx !== currentIndex || !isRunning,
        }"
      >
        <div class="flex items-center gap-3 px-5 py-3.5 bg-[#242424] border-b border-[rgba(255,255,255,0.12)]">
          <span class="shrink-0 w-5 h-5 rounded-full bg-[#2e2e2e] border border-[rgba(255,255,255,0.15)] flex items-center justify-center text-[10px] font-mono text-[#999]">
            {{ idx + 1 }}
          </span>
          <p class="text-[13px] font-medium text-[#d0d0d0] flex-1">{{ pair.message }}</p>
          <div class="shrink-0">
            <SpinnerIcon v-if="pair.loading" class="w-4 h-4 text-cyan-400" />
            <svg v-else-if="pair.response?.success !== false" class="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            <svg v-else class="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
            </svg>
          </div>
        </div>

        <div class="px-5 py-4 bg-[#1c1c1c]">
          <div v-if="pair.loading" class="flex items-center gap-2 text-[12px] text-[#aaa] py-1">
            <span class="w-1.5 h-1.5 rounded-full bg-[#777] dot-1"/>
            <span class="w-1.5 h-1.5 rounded-full bg-[#777] dot-2"/>
            <span class="w-1.5 h-1.5 rounded-full bg-[#777] dot-3"/>
            <span class="ml-1">Agent is thinking…</span>
          </div>
          <template v-else-if="pair.response">
            <div class="prose prose-sm prose-chat max-w-none" v-html="renderMd(pair.response.content)" />
            <div class="flex flex-wrap items-center gap-2 mt-3">
              <StatusBadge v-if="pair.response.hasPendingApprovals" variant="warning">Approval required</StatusBadge>
              <span class="text-[10px] text-[#888] font-mono ml-auto">
                {{ pair.response.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
              </span>
            </div>
          </template>
        </div>
      </div>

      <div v-if="isDone" class="rounded-2xl border border-green-500/[0.15] bg-green-500/[0.04] px-5 py-4 flex items-center gap-3">
        <svg class="w-5 h-5 text-green-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
        </svg>
        <div>
          <p class="text-[13px] font-semibold text-green-300">Demo complete</p>
          <p class="text-[12px] text-green-400/50 mt-0.5">All 5 prompts processed. Click "Run Again" to repeat.</p>
        </div>
      </div>

    </div>
  </div>
</template>
