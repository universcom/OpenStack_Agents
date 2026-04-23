<script setup lang="ts">
import { ref } from 'vue'
import type { AppSettings, SessionEntry } from './types'
import { checkHealth } from './api/client'
import { useSessionHistory } from './composables/useSessionHistory'
import AppSidebar    from './components/AppSidebar.vue'
import SettingsModal from './components/SettingsModal.vue'
import ChatMode      from './components/ChatMode.vue'
import DemoMode      from './components/DemoMode.vue'

const settings = ref<AppSettings>({
  serverUrl: 'http://localhost:8080',
  userId:    'engineer',
  projectId: '',
})

const isConnected = ref<boolean | null>(null)
const isChecking  = ref(false)

async function testConnection() {
  isChecking.value  = true
  isConnected.value = await checkHealth(settings.value.serverUrl)
  isChecking.value  = false
}

const showSettings = ref(false)

const TABS = [
  { id: 'chat', label: 'Chat' },
  { id: 'demo', label: 'Demo' },
] as const
type TabId = typeof TABS[number]['id']
const activeTab = ref<TabId>('chat')

const chatModeRef = ref<InstanceType<typeof ChatMode> | null>(null)

const { sessions, save: saveSession, remove: deleteSession, clearAll } = useSessionHistory()
const activeSessionId = ref<string | null>(null)

function snapshotCurrent() {
  const msgs = chatModeRef.value?.getMessages() ?? []
  const sid  = chatModeRef.value?.getSessionId() ?? null
  if (msgs.length) saveSession(sid, msgs)
}

function handleNewChat() {
  snapshotCurrent()
  chatModeRef.value?.clearSession()
  activeSessionId.value = null
  activeTab.value = 'chat'
}

function handleLoadSession(entry: SessionEntry) {
  snapshotCurrent()
  chatModeRef.value?.loadSession(entry.messages, entry.sessionId)
  activeSessionId.value = entry.id
  activeTab.value = 'chat'
}

function handleDeleteSession(id: string) {
  deleteSession(id)
  if (activeSessionId.value === id) activeSessionId.value = null
}

function handleClearAll() {
  clearAll()
  activeSessionId.value = null
}
</script>

<template>
  <div class="flex h-screen bg-[#141414] text-[#efefef] overflow-hidden">

    <AppSidebar
      :sessions="sessions"
      :active-id="activeSessionId"
      @new-chat="handleNewChat"
      @load-session="handleLoadSession"
      @delete-session="handleDeleteSession"
      @clear-all="handleClearAll"
      @open-settings="showSettings = true"
    />

    <main class="flex-1 flex flex-col overflow-hidden">

      <nav class="flex items-center border-b border-[rgba(255,255,255,0.12)] px-6 shrink-0 bg-[#141414]">
        <button
          v-for="tab in TABS"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="flex items-center gap-2 px-1 py-4 mr-8 text-[13px] font-medium border-b-2 transition-all duration-200"
          :class="activeTab === tab.id
            ? 'border-cyan-400 text-[#efefef]'
            : 'border-transparent text-[#b0b0b0] hover:text-[#e8e8e8]'"
        >
          <svg v-if="tab.id === 'chat'" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
          </svg>
          <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          {{ tab.label }}
        </button>
      </nav>

      <ChatMode
        v-if="activeTab === 'chat'"
        ref="chatModeRef"
        :settings="settings"
      />

      <DemoMode
        v-else
        :settings="settings"
      />

    </main>

    <SettingsModal
      :show="showSettings"
      v-model="settings"
      :is-connected="isConnected"
      :is-checking="isChecking"
      @check-connection="testConnection"
      @close="showSettings = false"
    />

  </div>
</template>
