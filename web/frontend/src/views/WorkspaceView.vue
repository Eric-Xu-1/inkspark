<template>
  <div class="h-screen flex flex-col bg-ink-bg">
    <AppHeader show-actions />
    <div class="flex flex-1 overflow-hidden flex-col md:flex-row">
      <!-- Left: Chat -->
      <div
        class="w-full md:w-[42%] flex flex-col border-r border-gray-200 bg-white min-h-0"
        :class="{ 'hidden md:flex': showDoc }"
      >
        <div class="flex-1 overflow-y-auto px-4 md:px-6 py-4 space-y-4">
          <!-- User message -->
          <div class="flex gap-3">
            <div class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-sm shrink-0">🐼</div>
            <div>
              <p class="text-xs text-gray-400 mb-1">阿强</p>
              <p class="text-sm text-gray-800 bg-gray-50 rounded-2xl px-4 py-2">{{ userPrompt }}</p>
            </div>
          </div>

          <!-- Agent steps -->
          <div v-for="step in store.steps" :key="step.step_id" class="flex gap-3">
            <div class="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center text-sm shrink-0">
              {{ agentEmoji(step.agent) }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-xs text-gray-400 mb-1">{{ step.agent || 'AI' }}</p>
              <StepCard
                :step="step"
                @view="onView"
                @confirm="onConfirm"
                @revise="onRevise"
              />
            </div>
          </div>

          <!-- Completion bubble + export -->
          <div v-if="store.status === 'done'" class="flex gap-3">
            <div class="w-8 h-8 rounded-full bg-green-50 flex items-center justify-center text-sm shrink-0">✨</div>
            <div class="flex-1 min-w-0">
              <p class="text-xs text-gray-400 mb-1">InkSpark</p>
              <div
                class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 p-3 rounded-xl bg-gray-50 border border-gray-100 hover:border-gray-200 transition-colors"
              >
                <span class="text-lg shrink-0">✅</span>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-800">创作完成</p>
                  <p class="text-xs text-gray-400 truncate">最终结果已生成</p>
                </div>
                <div class="flex items-center gap-2 shrink-0 flex-wrap justify-end">
                  <button
                    class="text-sm text-blue-600 hover:underline"
                    @click="onViewCompletion"
                  >
                    查看
                  </button>
                </div>
              </div>
              <button
                type="button"
                class="mt-2 w-full sm:w-auto px-4 py-2 bg-gray-900 text-white text-sm rounded-full hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="exporting"
                @click="onExport"
              >
                {{ exporting ? '导出中...' : '导出 Markdown' }}
              </button>
              <p v-if="exportError" class="mt-2 text-xs text-red-500">{{ exportError }}</p>
            </div>
          </div>
        </div>

        <!-- Bottom input -->
        <div class="p-3 md:p-4 border-t pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          <div class="bg-blue-50 text-blue-700 text-xs px-4 py-2 rounded-xl mb-3 hidden sm:block">
            来试试创建自己的写作画像吧！让阿强更懂你~
          </div>
          <div class="flex items-center gap-2 bg-gray-50 rounded-2xl px-4 py-2.5">
            <input
              v-model="extraInput"
              class="flex-1 bg-transparent text-sm focus:outline-none min-w-0"
              placeholder="描述你的创作需求..."
              disabled
            />
            <button class="w-9 h-9 shrink-0 bg-gray-900 text-white rounded-full text-sm">↑</button>
          </div>
        </div>
      </div>

      <!-- Right: Document -->
      <div
        class="flex-1 flex flex-col min-w-0 min-h-0"
        :class="showDoc ? 'fixed inset-0 z-40 md:relative md:inset-auto' : 'hidden md:flex'"
      >
        <DocumentPanel
          :visible="showDoc"
          :title="docTitle"
          :artifact="store.currentArtifact"
          :article-mode="isArticleView"
          @close="showDoc = false"
        />
        <div v-if="!showDoc" class="flex-1 flex items-center justify-center text-gray-400 text-sm">
          待确认内容将自动展示在此处
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import StepCard from '../components/StepCard.vue'
import DocumentPanel from '../components/DocumentPanel.vue'
import { useConversationStore } from '../stores/conversation'
import { downloadMarkdown } from '../api'

const props = defineProps<{ id: string }>()
const store = useConversationStore()
const showDoc = ref(false)
const docTitle = ref('文档预览')
const userPrompt = ref('创作任务进行中...')
const extraInput = ref('')
const exporting = ref(false)
const exportError = ref('')

const isArticleView = computed(() => store.status === 'done' && !store.activeStepId)

function agentEmoji(agent: string) {
  return { '小美': '👩', '小青': '👩‍💻', '小尹': '👩‍🏫' }[agent] || '🤖'
}

function openPreview(stepId?: string | null) {
  const id = stepId ?? store.activeStepId
  const step = store.steps.find(s => s.step_id === id)
  docTitle.value = step?.title || '文档预览'
  showDoc.value = true
}

async function onView(stepId: string) {
  await store.viewArtifact(props.id, stepId)
  openPreview(stepId)
}

async function onViewCompletion() {
  await store.viewExport(props.id)
}

watch(
  () => store.currentArtifact,
  (artifact) => {
    if (!artifact) return
    if (store.activeStepId) {
      openPreview()
    } else if (store.status === 'done') {
      docTitle.value = artifact.meta?.title || '创作完成'
      showDoc.value = true
    }
  },
)

async function onConfirm(stepId: string) {
  const step = store.steps.find(s => s.step_id === stepId)
  let payload: Record<string, unknown> | undefined
  if (step?.phase === 'research') {
    payload = { chosen_direction: store.currentArtifact?.content?.split('\n')[0] || '' }
  }
  await store.confirm(props.id, stepId, payload)
}

async function onRevise(stepId: string, feedback: string) {
  await store.revise(props.id, stepId, feedback)
}

async function onExport() {
  exporting.value = true
  exportError.value = ''
  try {
    await downloadMarkdown(props.id)
  } catch (err) {
    exportError.value = err instanceof Error ? err.message : '导出失败，请稍后重试'
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  store.connectSSE(props.id)
  const conv = await store.loadSteps(props.id)
  userPrompt.value = conv.topic || userPrompt.value
})

onUnmounted(() => store.disconnect())
</script>
