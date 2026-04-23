<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { AppSettings } from '../types'
import { useDemo } from '../composables/useDemo'

const props = defineProps<{ settings: AppSettings }>()

const { pairs, isRunning, isDone, currentIndex, run, reset } = useDemo()

const completedCount = computed(() => pairs.value.filter(p => !p.loading).length)
const totalCount     = computed(() => pairs.value.length)

function renderMd(text: string): string {
  return marked.parse(text) as string
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-hidden">

    <!-- ── Toolbar ───────────────────────────────────────────────────────── -->
    <div class="flex items-center justify-between px-5 py-3 border-b border-zinc-800 shrink-0">
      <div>
        <p class="text-sm font-medium text-zinc-200">Demo Run</p>
        <p class="text-xs text-zinc-500 mt-0.5">
          Runs 5 scripted prompts sequentially through the agent — no interaction needed.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <!-- Progress text -->
        <span v-if="isRunning" class="text-xs text-zinc-500 font-mono">
          {{ completedCount }}&thinsp;/&thinsp;{{ totalCount }}
        </span>

        <!-- Run / Run Again button -->
        <button
          @click="isDone ? reset() : run(props.settings)"
          :disabled="isRunning"
          class="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all duration-150"
          :class="isRunning
            ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed'
            : 'bg-cyan-500 text-white hover:bg-cyan-400 shadow-md shadow-cyan-500/20 active:scale-95'"
        >
          <svg v-if="isRunning" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
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

    <!-- ── Results list ──────────────────────────────────────────────────── -->
    <div class="flex-1 overflow-y-auto px-5 py-5 space-y-5">

      <!-- Idle state (nothing run yet) -->
      <div v-if="!isRunning && !isDone && pairs.length === 0"
        class="flex flex-col items-center justify-center h-full gap-4 text-center pb-8"
      >
        <div class="w-14 h-14 rounded-2xl bg-zinc-800 border border-zinc-700 flex items-center justify-center">
          <svg class="w-7 h-7 text-cyan-500/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <div>
          <p class="text-zinc-200 font-medium">Ready to demo</p>
          <p class="text-zinc-500 text-sm mt-1 max-w-sm">
            Runs 5 prompts covering VM listing, creation, monitoring, diagnostics, and recommendations.
          </p>
        </div>
        <!-- Preview of the 5 prompts -->
        <ol class="text-left space-y-1.5 max-w-sm w-full">
          <li v-for="(p, i) in ['List all running instances', 'Create a VM (web-server-01)', 'CPU usage of the cluster', 'Diagnose instance in ERROR', 'Performance recommendations']"
            :key="i"
            class="flex items-start gap-2 text-xs text-zinc-500"
          >
            <span class="shrink-0 w-4 h-4 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-[9px] font-mono text-zinc-400 mt-0.5">
              {{ i + 1 }}
            </span>
            {{ p }}
          </li>
        </ol>
      </div>

      <!-- Prompt + Response cards -->
      <div
        v-for="(pair, idx) in pairs"
        :key="idx"
        class="rounded-2xl border overflow-hidden transition-all duration-300"
        :class="{
          'border-cyan-500/40 shadow-lg shadow-cyan-500/5':  idx === currentIndex && isRunning,
          'border-zinc-700':                                  idx !== currentIndex || !isRunning,
        }"
      >
        <!-- Prompt header -->
        <div class="flex items-center gap-3 px-4 py-3 bg-zinc-800/60 border-b border-zinc-700/60">
          <!-- Step number badge -->
          <span class="shrink-0 w-5 h-5 rounded-full bg-zinc-700 border border-zinc-600 flex items-center justify-center text-[10px] font-mono text-zinc-400">
            {{ idx + 1 }}
          </span>
          <p class="text-sm font-medium text-zinc-200 flex-1">{{ pair.message }}</p>

          <!-- Status icon on the right -->
          <div class="shrink-0">
            <!-- Loading spinner -->
            <svg v-if="pair.loading" class="w-4 h-4 text-cyan-400 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            <!-- Success check -->
            <svg v-else-if="pair.response?.success !== false" class="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            <!-- Error X -->
            <svg v-else class="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
            </svg>
          </div>
        </div>

        <!-- Response body -->
        <div class="px-4 py-3 bg-zinc-900">
          <!-- Still loading -->
          <div v-if="pair.loading" class="flex items-center gap-2 text-xs text-zinc-500 py-1">
            <span class="w-1.5 h-1.5 rounded-full bg-zinc-500 dot-1"/>
            <span class="w-1.5 h-1.5 rounded-full bg-zinc-500 dot-2"/>
            <span class="w-1.5 h-1.5 rounded-full bg-zinc-500 dot-3"/>
            <span class="ml-1">Agent is thinking…</span>
          </div>

          <!-- Rendered response -->
          <div
            v-else-if="pair.response"
            class="prose prose-sm prose-chat max-w-none"
            v-html="renderMd(pair.response.content)"
          />

          <!-- Badges row -->
          <div v-if="pair.response && !pair.loading" class="flex flex-wrap gap-2 mt-3">
            <span
              v-if="pair.response.hasPendingApprovals"
              class="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-yellow-400/10 border border-yellow-400/20 text-yellow-300"
            >
              <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
              </svg>
              Approval required
            </span>
            <span class="text-[10px] text-zinc-600 font-mono ml-auto">
              {{ pair.response.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Completion banner -->
      <div v-if="isDone" class="rounded-2xl border border-green-500/20 bg-green-500/5 px-4 py-3 flex items-center gap-3">
        <svg class="w-5 h-5 text-green-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
        </svg>
        <div>
          <p class="text-sm font-medium text-green-300">Demo complete</p>
          <p class="text-xs text-green-400/60 mt-0.5">All 5 prompts processed. Click "Run Again" to repeat.</p>
        </div>
      </div>

    </div>
  </div>
</template>
