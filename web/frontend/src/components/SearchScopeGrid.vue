<template>
  <div class="mt-4">
    <p class="text-sm text-gray-500 mb-3">选择搜索范围</p>
    <div class="grid grid-cols-1 gap-2">
      <div
        v-for="item in items"
        :key="item.key"
        class="flex items-center justify-between p-3 rounded-xl border border-gray-100 hover:bg-gray-50"
        :class="{ 'opacity-50': item.disabled }"
      >
        <div class="flex items-center gap-3">
          <span class="text-lg">{{ item.icon }}</span>
          <div>
            <p class="text-sm font-medium text-gray-800">{{ item.label }}</p>
            <p class="text-xs text-gray-400">{{ item.desc }}</p>
          </div>
        </div>
        <button
          class="w-10 h-5 rounded-full transition-colors relative"
          :class="model[item.key] ? 'bg-teal-500' : 'bg-gray-200'"
          :disabled="item.disabled"
          @click="toggle(item.key)"
        >
          <span
            class="absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform"
            :class="model[item.key] ? 'translate-x-5' : 'translate-x-0.5'"
          />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, boolean> }>()
const emit = defineEmits<{ 'update:modelValue': [Record<string, boolean>] }>()

const model = reactive({ ...props.modelValue })

watch(model, (v) => emit('update:modelValue', { ...v }), { deep: true })

const items = [
  { key: 'notes', icon: '📝', label: '我的笔记', desc: '基于你的所有笔记来回答', disabled: true },
  { key: 'knowledge_base', icon: '📚', label: '知识库', desc: '指定知识库来回答', disabled: true },
  { key: 'web', icon: '🌐', label: '全网', desc: '在整个互联网中搜索', disabled: false },
  { key: 'literature', icon: '📄', label: '文献', desc: '搜索论文资源', disabled: true },
]

function toggle(key: string) {
  const item = items.find(i => i.key === key)
  if (item?.disabled) return
  model[key] = !model[key]
}
</script>
