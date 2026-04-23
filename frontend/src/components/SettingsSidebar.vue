<script setup lang="ts">
import type { AppSettings } from '../types'

const props = defineProps<{
  modelValue:  AppSettings
  isConnected: boolean | null
  isChecking:  boolean
}>()

const emit = defineEmits<{
  'update:modelValue':  [value: AppSettings]
  'check-connection':  []
  'clear-session':     []
}>()

// Emits a shallow copy of settings with one field updated so the parent's
// v-model ref is always replaced (avoids mutating a prop directly).
function patch(key: keyof AppSettings, value: string) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}
</script>

<template>
  <aside class="w-60 shrink-0 bg-zinc-900 border-r border-zinc-800 flex flex-col overflow-y-auto">
    <div class="p-4 flex flex-col gap-6">

      <!-- ── Connection ──────────────────────────────────────────────────── -->
      <section>
        <h2 class="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest mb-3">
          Connection
        </h2>

        <div class="space-y-2.5">
          <!-- Server URL input -->
          <div>
            <label class="block text-xs text-zinc-400 mb-1">Server URL</label>
            <input
              :value="modelValue.serverUrl"
              @input="patch('serverUrl', ($event.target as HTMLInputElement).value)"
              type="text"
              placeholder="http://localhost:8080"
              spellcheck="false"
              class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-zinc-200 placeholder-zinc-600 font-mono focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20 transition-colors"
            />
          </div>

          <!-- Test connection button -->
          <button
            @click="$emit('check-connection')"
            :disabled="isChecking"
            class="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border transition-colors"
            :class="isChecking
              ? 'border-zinc-700 bg-zinc-800 text-zinc-500 cursor-not-allowed'
              : 'border-zinc-700 bg-zinc-800 text-zinc-300 hover:border-cyan-500/50 hover:text-cyan-400 hover:bg-zinc-750'"
          >
            <svg v-if="isChecking" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            {{ isChecking ? 'Checking…' : 'Test Connection' }}
          </button>
        </div>
      </section>

      <!-- ── Identity ────────────────────────────────────────────────────── -->
      <section class="border-t border-zinc-800 pt-5">
        <h2 class="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest mb-3">
          Identity
        </h2>

        <div class="space-y-2.5">
          <div>
            <label class="block text-xs text-zinc-400 mb-1">User ID</label>
            <input
              :value="modelValue.userId"
              @input="patch('userId', ($event.target as HTMLInputElement).value)"
              type="text"
              placeholder="engineer"
              spellcheck="false"
              class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20 transition-colors"
            />
          </div>

          <div>
            <label class="block text-xs text-zinc-400 mb-1">
              Project ID
              <span class="text-zinc-600">(optional)</span>
            </label>
            <input
              :value="modelValue.projectId"
              @input="patch('projectId', ($event.target as HTMLInputElement).value)"
              type="text"
              placeholder="my-openstack-project"
              spellcheck="false"
              class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20 transition-colors"
            />
          </div>
        </div>
      </section>

      <!-- ── Session ─────────────────────────────────────────────────────── -->
      <section class="border-t border-zinc-800 pt-5">
        <h2 class="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest mb-3">
          Session
        </h2>

        <!-- Clear session: resets session_id so next message starts fresh -->
        <button
          @click="$emit('clear-session')"
          class="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border border-zinc-700 bg-zinc-800 text-zinc-400 hover:border-red-500/40 hover:text-red-400 transition-colors"
        >
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Clear Chat History
        </button>
      </section>

    </div>

    <!-- Footer hint -->
    <div class="mt-auto p-4 border-t border-zinc-800">
      <p class="text-[10px] text-zinc-600 leading-relaxed text-center">
        Start the backend with:<br/>
        <code class="text-zinc-500 font-mono">python main.py --mode server</code>
      </p>
    </div>
  </aside>
</template>
