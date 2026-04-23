import { ref } from 'vue'
import type { DemoPair, AppSettings } from '../types'
import { sendMessage } from '../api/client'

// Mirrors the demo_messages list in main.py _run_demo() so the frontend
// exercises exactly the same prompts as the Python CLI demo mode.
const DEMO_PROMPTS: Pick<DemoPair, 'message' | 'userId' | 'projectId'>[] = [
  { userId: 'alice', projectId: 'proj-demo', message: 'List all my running instances' },
  { userId: 'alice', projectId: 'proj-demo', message: 'Create a VM called web-server-01 with 2 vCPUs and 4GB RAM' },
  { userId: 'alice', projectId: 'proj-demo', message: 'What is the current CPU usage of the cluster?' },
  { userId: 'alice', projectId: 'proj-demo', message: 'Why is instance abc-123 in ERROR state?' },
  { userId: 'alice', projectId: 'proj-demo', message: 'Give me performance recommendations for my project' },
]

/**
 * Manages state for the scripted demo run.
 *
 * run() sends each demo prompt to the server sequentially, updating the
 * pairs array reactively so the UI can render results as they arrive.
 * Each prompt is sent as an independent conversation (no session_id) to keep
 * outputs self-contained — matching the behaviour of _run_demo() in main.py.
 */
export function useDemo() {
  const pairs        = ref<DemoPair[]>([])
  const isRunning    = ref(false)
  const isDone       = ref(false)
  const currentIndex = ref(-1)

  function reset() {
    pairs.value    = []
    isDone.value   = false
    currentIndex.value = -1
  }

  async function run(settings: AppSettings) {
    reset()
    isRunning.value = true

    for (let i = 0; i < DEMO_PROMPTS.length; i++) {
      const p = DEMO_PROMPTS[i]
      currentIndex.value = i

      // Push the entry immediately so the UI shows a loading card at once.
      const entry: DemoPair = {
        message:   p.message,
        userId:    p.userId,
        projectId: p.projectId,
        response:  null,
        loading:   true,
      }
      pairs.value.push(entry)

      try {
        const result = await sendMessage(settings.serverUrl, {
          message:    p.message,
          user_id:    p.userId,
          project_id: p.projectId,
          // session_id intentionally omitted → each prompt is independent
        })

        entry.response = {
          id:                  crypto.randomUUID(),
          role:                'agent',
          content:             result.final_response,
          timestamp:           new Date(),
          success:             result.success,
          hasPendingApprovals: (result.pending_approvals?.length ?? 0) > 0,
        }
      } catch (err) {
        entry.response = {
          id:        crypto.randomUUID(),
          role:      'agent',
          content:   `**Error:** ${err instanceof Error ? err.message : String(err)}`,
          timestamp: new Date(),
          success:   false,
        }
      } finally {
        entry.loading = false
      }
    }

    isRunning.value    = false
    isDone.value       = true
    currentIndex.value = -1
  }

  return { pairs, isRunning, isDone, currentIndex, run, reset }
}
