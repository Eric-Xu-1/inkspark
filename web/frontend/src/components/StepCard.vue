<template>
  <div
    class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 p-3 rounded-xl bg-gray-50 border border-gray-100 hover:border-gray-200 transition-colors"
  >
    <span class="text-lg shrink-0">{{ icon }}</span>
    <div class="flex-1 min-w-0">
      <p class="text-sm font-medium text-gray-800">{{ step.title }}</p>
      <p class="text-xs text-gray-400 truncate">
        <span v-if="step.status === 'running'" class="text-blue-500">执行中...</span>
        <span v-else-if="step.status === 'awaiting_user'" class="text-amber-600">等待确认</span>
        <span v-else>{{ step.detail || step.agent }}</span>
      </p>
    </div>
    <div class="flex items-center gap-2 shrink-0 flex-wrap justify-end">
      <button
        v-if="step.artifact_key"
        class="text-sm text-blue-600 hover:underline"
        @click="$emit('view', step.step_id)"
      >
        查看
      </button>
      <template v-if="step.status === 'awaiting_user'">
        <button
          class="px-3 py-1 text-xs bg-gray-900 text-white rounded-full hover:bg-gray-700"
          @click="$emit('confirm', step.step_id)"
        >
          确认
        </button>
        <button
          class="px-3 py-1 text-xs border rounded-full hover:bg-gray-50"
          @click="showRevise = true"
        >
          修改
        </button>
      </template>
      <span
        v-if="step.status === 'running'"
        class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"
      />
    </div>
    <div v-if="showRevise" class="fixed inset-0 bg-black/30 flex items-end sm:items-center justify-center z-50 p-4" @click.self="showRevise = false">
      <div class="bg-white rounded-2xl p-5 sm:p-6 w-full max-w-sm shadow-xl">
        <h3 class="font-medium mb-3">修改建议</h3>
        <textarea
          v-model="feedback"
          class="w-full border rounded-xl p-3 text-sm h-24 resize-none focus:outline-none focus:ring-2 focus:ring-blue-200"
          placeholder="请输入修改意见..."
        />
        <div class="flex justify-end gap-2 mt-4">
          <button class="px-4 py-1.5 text-sm border rounded-full" @click="showRevise = false">取消</button>
          <button
            class="px-4 py-1.5 text-sm bg-gray-900 text-white rounded-full"
            @click="submitRevise"
          >
            提交
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Step } from '../api'

const props = defineProps<{ step: Step }>()
const emit = defineEmits<{ view: [string]; confirm: [string]; revise: [string, string] }>()

const showRevise = ref(false)
const feedback = ref('')

const iconMap: Record<string, string> = {
  research: '🔍',
  outline: '📋',
  section: '✍️',
  review: '✅',
}

const icon = computed(() => iconMap[props.step.phase] || '📌')

function submitRevise() {
  emit('revise', props.step.step_id, feedback.value)
  showRevise.value = false
  feedback.value = ''
}
</script>
