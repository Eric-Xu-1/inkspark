import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Step, Artifact, Conversation } from '../api'
import { fetchSteps, fetchConversation, fetchArtifact, fetchExportContent, submitAction, streamUrl } from '../api'

function applyConversationStatus(raw: string) {
  if (raw === 'done') return 'done'
  if (raw === 'failed') return 'error'
  return raw
}

export const useConversationStore = defineStore('conversation', () => {
  const steps = ref<Step[]>([])
  const currentArtifact = ref<Artifact | null>(null)
  const activeStepId = ref<string | null>(null)
  const status = ref('idle')
  let eventSource: EventSource | null = null
  let currentConvId: string | null = null

  async function autoPreviewIfNeeded(step: Step) {
    if (step.status !== 'awaiting_user' || !step.artifact_key || !currentConvId) return
    await viewArtifact(currentConvId, step.step_id)
  }

  function connectSSE(convId: string) {
    currentConvId = convId
    if (eventSource) eventSource.close()
    eventSource = new EventSource(streamUrl(convId))

    eventSource.addEventListener('init', (e) => {
      const data = JSON.parse(e.data)
      if (data.steps) steps.value = data.steps
      if (data.status) status.value = applyConversationStatus(data.status)
      const awaiting = [...steps.value].reverse().find(
        s => s.status === 'awaiting_user' && s.artifact_key,
      )
      if (awaiting) autoPreviewIfNeeded(awaiting)
      else if (status.value === 'done' && currentConvId) autoPreviewExport(currentConvId)
    })

    eventSource.addEventListener('message', (e) => {
      const event = JSON.parse(e.data)
      if (event.step) {
        const idx = steps.value.findIndex(s => s.step_id === event.step.step_id)
        if (idx >= 0) {
          steps.value[idx] = event.step
        } else {
          steps.value.push(event.step)
        }
        autoPreviewIfNeeded(event.step)
      }
      if (event.type === 'awaiting_user' && event.step_id) {
        const step = steps.value.find(s => s.step_id === event.step_id)
        if (step) autoPreviewIfNeeded(step)
      }
      if (event.type === 'conversation_done') {
        status.value = 'done'
        if (currentConvId) autoPreviewExport(currentConvId)
      }
      if (event.type === 'error') {
        status.value = 'error'
      }
    })
  }

  async function loadSteps(convId: string): Promise<Conversation> {
    currentConvId = convId
    const [loadedSteps, conv] = await Promise.all([
      fetchSteps(convId),
      fetchConversation(convId),
    ])
    steps.value = loadedSteps
    status.value = applyConversationStatus(conv.status)
    const awaiting = [...steps.value].reverse().find(
      s => s.status === 'awaiting_user' && s.artifact_key,
    )
    if (awaiting) await autoPreviewIfNeeded(awaiting)
    else if (status.value === 'done') await autoPreviewExport(convId)
    return conv
  }

  async function viewExport(convId: string) {
    activeStepId.value = null
    currentArtifact.value = await fetchExportContent(convId)
  }

  async function autoPreviewExport(convId: string) {
    try {
      await viewExport(convId)
    } catch {
      // export may not be ready yet
    }
  }

  async function viewArtifact(convId: string, stepId: string) {
    activeStepId.value = stepId
    currentArtifact.value = await fetchArtifact(convId, stepId)
  }

  async function confirm(convId: string, stepId: string, payload?: Record<string, unknown>) {
    await submitAction(convId, stepId, 'confirm', payload)
  }

  async function revise(convId: string, stepId: string, feedback: string) {
    await submitAction(convId, stepId, 'revise', { feedback })
  }

  function disconnect() {
    eventSource?.close()
    eventSource = null
  }

  return {
    steps, currentArtifact, activeStepId, status,
    connectSSE, loadSteps, viewArtifact, viewExport, confirm, revise, disconnect,
  }
})
