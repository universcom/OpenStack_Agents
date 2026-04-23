<script setup lang="ts">
import SpinnerIcon from './SpinnerIcon.vue'
import type { AppSettings } from '../types'

const props = defineProps<{
  modelValue:  AppSettings
  isConnected: boolean | null
  isChecking:  boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: AppSettings]
  'check-connection': []
  'clear-session':    []
}>()

function patch(key: keyof AppSettings, value: string) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}
</script>

<template>
  <aside class="w-56 shrink-0 bg-[#0f0f0f] border-r border-[rgba(255,255,255,0.1)] flex flex-col overflow-y-auto">
    <div class="p-5 flex flex-col gap-7">

      <section>
        <h2 class="text-[10px] font-semibold text-[#666] uppercase tracking-[0.1em] mb-3.5">Connection</h2>
        <div class="space-y-2">
          <div>
            <label class="block text-[11px] text-[#585858] mb-1.5 font-medium">Server URL</label>
            <input
              :value="modelValue.serverUrl"
              @input="patch('serverUrl', ($event.target as HTMLInputElement).value)"
              type="text"
              placeholder="http://localhost:8080"
              spellcheck="false"
              class="field-input font-mono"
            />
          </div>
          <button
            @click="$emit('check-connection')"
            :disabled="isChecking"
            class="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-[12px] font-medium border transition-all duration-150"
            :class="isChecking
              ? 'border-[rgba(255,255,255,0.04)] bg-[rgba(255,255,255,0.02)] text-[#333] cursor-not-allowed'
              : 'border-[rgba(255,255,255,0.07)] bg-[rgba(255,255,255,0.03)] text-[#777] hover:border-cyan-500/30 hover:text-cyan-400 hover:bg-cyan-500/[0.05]'"
          >
            <SpinnerIcon v-if="isChecking" class="w-3 h-3" />
            <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            {{ isChecking ? 'Checking…' : 'Test Connection' }}
          </button>
        </div>
      </section>

      <section class="border-t border-[rgba(255,255,255,0.1)] pt-6">
        <h2 class="text-[10px] font-semibold text-[#666] uppercase tracking-[0.1em] mb-3.5">Identity</h2>
        <div class="space-y-2">
          <div>
            <label class="block text-[11px] text-[#585858] mb-1.5 font-medium">User ID</label>
            <input
              :value="modelValue.userId"
              @input="patch('userId', ($event.target as HTMLInputElement).value)"
              type="text"
              placeholder="engineer"
              spellcheck="false"
              class="field-input"
            />
          </div>
          <div>
            <label class="block text-[11px] text-[#585858] mb-1.5 font-medium">
              Project ID
              <span class="text-[#555] font-normal ml-1">optional</span>
            </label>
            <input
              :value="modelValue.projectId"
              @input="patch('projectId', ($event.target as HTMLInputElement).value)"
              type="text"
              placeholder="my-project"
              spellcheck="false"
              class="field-input"
            />
          </div>
        </div>
      </section>

      <section class="border-t border-[rgba(255,255,255,0.1)] pt-6">
        <h2 class="text-[10px] font-semibold text-[#666] uppercase tracking-[0.1em] mb-3.5">Session</h2>
        <button
          @click="$emit('clear-session')"
          class="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-[12px] font-medium border border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.02)] text-[#555] hover:border-red-500/25 hover:text-red-400 hover:bg-red-500/[0.04] transition-all duration-150"
        >
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Clear Chat History
        </button>
      </section>

    </div>

    <div class="mt-auto p-5 border-t border-[rgba(255,255,255,0.1)]">
      <p class="text-[10px] text-[#555] leading-relaxed text-center">
        Start backend:<br/>
        <code class="text-[#777] font-mono">python main.py --mode server</code>
      </p>
    </div>
  </aside>
</template>
