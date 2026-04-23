<script setup lang="ts">
import type { AppSettings } from '../types'
import SpinnerIcon    from './SpinnerIcon.vue'
import ConnectionPill from './ConnectionPill.vue'

const props = defineProps<{
  show:        boolean
  modelValue:  AppSettings
  isConnected: boolean | null
  isChecking:  boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: AppSettings]
  'check-connection':  []
  'close':             []
}>()

function patch(key: keyof AppSettings, value: string) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center p-4">

        <div class="absolute inset-0 bg-black/70 backdrop-blur-[2px]" @click="$emit('close')" />

        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 scale-[0.97] translate-y-1"
          enter-to-class="opacity-100 scale-100 translate-y-0"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="opacity-100 scale-100 translate-y-0"
          leave-to-class="opacity-0 scale-[0.97] translate-y-1"
        >
          <div
            v-if="show"
            class="relative z-10 bg-[#222] border border-[rgba(255,255,255,0.15)] rounded-2xl w-full max-w-[440px] shadow-2xl shadow-black/60"
          >
            <!-- Header -->
            <div class="flex items-center justify-between px-6 py-5 border-b border-[rgba(255,255,255,0.07)]">
              <div class="flex items-center gap-2.5">
                <svg class="w-4 h-4 text-[#aaa]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round"
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
                <h2 class="text-[15px] font-semibold text-[#f0f0f0]">Settings</h2>
              </div>
              <button
                @click="$emit('close')"
                class="w-7 h-7 rounded-lg flex items-center justify-center text-[#3e3e3e] hover:text-[#d0d0d0] hover:bg-[rgba(255,255,255,0.06)] transition-all"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>

            <div class="px-6 py-5 space-y-6">

              <!-- Connection -->
              <section>
                <h3 class="text-[11px] font-semibold text-[#aaa] uppercase tracking-[0.1em] mb-4">Connection</h3>
                <div class="space-y-3">
                  <div>
                    <label class="block text-[12px] text-[#aaa] mb-1.5 font-medium">Server URL</label>
                    <input
                      :value="modelValue.serverUrl"
                      @input="patch('serverUrl', ($event.target as HTMLInputElement).value)"
                      type="text"
                      placeholder="http://localhost:8080"
                      spellcheck="false"
                      class="field-input font-mono"
                      style="font-size:13px; padding:10px 14px; border-radius:12px;"
                    />
                  </div>
                  <div class="flex items-center gap-2">
                    <button
                      @click="$emit('check-connection')"
                      :disabled="isChecking"
                      class="flex items-center gap-2 px-3.5 py-2 rounded-xl text-[12px] font-medium border transition-all duration-150"
                      :class="isChecking
                        ? 'border-[rgba(255,255,255,0.04)] bg-[rgba(255,255,255,0.02)] text-[#333] cursor-not-allowed'
                        : 'border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.04)] text-[#888] hover:border-cyan-500/35 hover:text-cyan-400 hover:bg-cyan-500/[0.06]'"
                    >
                      <SpinnerIcon v-if="isChecking" class="w-3 h-3" />
                      <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                      </svg>
                      {{ isChecking ? 'Checking…' : 'Test Connection' }}
                    </button>
                    <ConnectionPill :is-connected="isConnected" :is-checking="isChecking" />
                  </div>
                </div>
              </section>

              <!-- Identity -->
              <section class="border-t border-[rgba(255,255,255,0.06)] pt-5">
                <h3 class="text-[11px] font-semibold text-[#aaa] uppercase tracking-[0.1em] mb-4">Identity</h3>
                <div class="space-y-3">
                  <div>
                    <label class="block text-[12px] text-[#aaa] mb-1.5 font-medium">User ID</label>
                    <input
                      :value="modelValue.userId"
                      @input="patch('userId', ($event.target as HTMLInputElement).value)"
                      type="text"
                      placeholder="engineer"
                      spellcheck="false"
                      class="field-input"
                      style="font-size:13px; padding:10px 14px; border-radius:12px;"
                    />
                  </div>
                  <div>
                    <label class="block text-[12px] text-[#aaa] mb-1.5 font-medium">
                      Project ID
                      <span class="text-[#999] font-normal ml-1">optional</span>
                    </label>
                    <input
                      :value="modelValue.projectId"
                      @input="patch('projectId', ($event.target as HTMLInputElement).value)"
                      type="text"
                      placeholder="my-openstack-project"
                      spellcheck="false"
                      class="field-input"
                      style="font-size:13px; padding:10px 14px; border-radius:12px;"
                    />
                  </div>
                </div>
              </section>

            </div>

            <!-- Footer -->
            <div class="px-6 py-4 border-t border-[rgba(255,255,255,0.06)] flex justify-between items-center">
              <p class="text-[11px] text-[#999] font-mono">
                python main.py --mode server
              </p>
              <button
                @click="$emit('close')"
                class="px-4 py-2 rounded-xl bg-cyan-500 text-white text-[13px] font-semibold hover:bg-cyan-400 transition-all duration-150 active:scale-95"
              >
                Done
              </button>
            </div>

          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
