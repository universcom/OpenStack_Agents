<script setup lang="ts">
import { ref } from 'vue'
import type { AppSettings } from './types'
import { checkHealth } from './api/client'
import AppHeader      from './components/AppHeader.vue'
import SettingsSidebar from './components/SettingsSidebar.vue'
import ChatMode       from './components/ChatMode.vue'
import DemoMode       from './components/DemoMode.vue'

// ── Global settings (shared by ChatMode and DemoMode via props) ───────────────
const settings = ref<AppSettings>({
  serverUrl: 'http://localhost:8080',
  userId:    'engineer',
  projectId: '',
})

// ── Connection status ─────────────────────────────────────────────────────────
// null = not yet checked, true = reachable, false = unreachable
const isConnected = ref<boolean | null>(null)
const isChecking  = ref(false)

async function testConnection() {
  isChecking.value  = true
  isConnected.value = await checkHealth(settings.value.serverUrl)
  isChecking.value  = false
}

// ── Active tab ────────────────────────────────────────────────────────────────
const TABS = [
  { id: 'chat', label: 'Chat',  description: 'Interactive conversation with the agent' },
  { id: 'demo', label: 'Demo',  description: 'Run 5 scripted prompts automatically' },
] as const

type TabId = typeof TABS[number]['id']
const activeTab = ref<TabId>('chat')

// ── ChatMode component ref — used to call clearSession() from the sidebar ─────
const chatModeRef = ref<InstanceType<typeof ChatMode> | null>(null)

function handleClearSession() {
  chatModeRef.value?.clearSession()
}
</script>

<template>
  <div class="flex flex-col h-screen bg-zinc-950 text-zinc-100 overflow-hidden">

    <!-- Top header bar with branding and connection status -->
    <AppHeader :is-connected="isConnected" :is-checking="isChecking" />

    <div class="flex flex-1 overflow-hidden">

      <!-- Left settings sidebar -->
      <SettingsSidebar
        v-model="settings"
        :is-connected="isConnected"
        :is-checking="isChecking"
        @check-connection="testConnection"
        @clear-session="handleClearSession"
      />

      <!-- Main content area -->
      <main class="flex-1 flex flex-col overflow-hidden">

        <!-- Mode tab bar -->
        <nav class="flex items-center border-b border-zinc-800 px-5 shrink-0 bg-zinc-900/40">
          <button
            v-for="tab in TABS"
            :key="tab.id"
            @click="activeTab = tab.id"
            class="flex items-center gap-2 px-1 py-3.5 mr-6 text-sm font-medium border-b-2 transition-colors"
            :class="activeTab === tab.id
              ? 'border-cyan-500 text-cyan-400'
              : 'border-transparent text-zinc-500 hover:text-zinc-300'"
            :title="tab.description"
          >
            <!-- Chat icon -->
            <svg v-if="tab.id === 'chat'" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
            </svg>
            <!-- Demo / play icon -->
            <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            {{ tab.label }}
          </button>
        </nav>

        <!-- Tab content — only one rendered at a time; both share the same settings -->
        <ChatMode
          v-if="activeTab === 'chat'"
          ref="chatModeRef"
          :settings="settings"
        />

        <DemoMode
          v-else-if="activeTab === 'demo'"
          :settings="settings"
        />

      </main>
    </div>
  </div>
</template>
