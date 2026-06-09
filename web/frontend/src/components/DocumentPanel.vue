<template>
  <aside v-if="visible" class="flex flex-col flex-1 w-full bg-white h-full min-h-0">
    <div class="flex items-center gap-3 px-4 md:px-6 py-3 md:py-4 border-b shrink-0">
      <button
        class="md:hidden text-sm text-gray-600 hover:text-gray-800 shrink-0"
        @click="$emit('close')"
      >
        ← 返回
      </button>
      <h2 class="font-medium text-gray-800 truncate flex-1 min-w-0">{{ title }}</h2>
      <button class="hidden md:block text-gray-400 hover:text-gray-600 shrink-0" @click="$emit('close')">✕</button>
    </div>
    <div
      class="flex-1 overflow-y-auto px-4 md:px-8 py-4 md:py-6 pb-[max(1rem,env(safe-area-inset-bottom))]"
      :class="articleMode ? 'bg-gray-50/50' : ''"
    >
      <div v-if="artifact" :class="articleMode ? 'max-w-3xl mx-auto' : ''">
        <div
          v-if="articleMode && metaEntries.length"
          class="flex flex-wrap gap-2 mb-6"
        >
          <span
            v-for="item in metaEntries"
            :key="item.label"
            class="text-xs text-gray-500 bg-white border border-gray-100 px-2.5 py-1 rounded-full"
          >
            {{ item.label }}：{{ item.value }}
          </span>
        </div>
        <div
          class="markdown-body"
          :class="articleMode ? 'article-body bg-white rounded-2xl border border-gray-100 px-5 md:px-8 py-6 md:py-8 shadow-sm' : ''"
          v-html="rendered"
        />
      </div>
      <p v-else class="text-gray-400 text-sm">点击步骤卡片「查看」预览内容</p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { Artifact } from '../api'

marked.setOptions({ gfm: true, breaks: true })

const props = defineProps<{
  visible: boolean
  title: string
  artifact: Artifact | null
  articleMode?: boolean
}>()

defineEmits<{ close: [] }>()

const SOURCE_TAG_PATTERN = /（(?:权威数据|官方确认|行业报告|学术研究|专家观点|公开资料|媒体报道|统计数据)[^）]*）/g

const META_LABELS: Record<string, string> = {
  topic: '主题',
  mode: '模式',
  category: '分类',
  date: '日期',
}

const metaEntries = computed(() => {
  if (!props.artifact?.meta) return []
  return Object.entries(props.artifact.meta)
    .filter(([key]) => key !== 'title' && META_LABELS[key])
    .map(([key, value]) => ({ label: META_LABELS[key], value }))
})

function postProcessHtml(html: string): string {
  return html.replace(SOURCE_TAG_PATTERN, '<span class="source-tag">$&</span>')
}

const rendered = computed(() => {
  if (!props.artifact) return ''
  if (props.artifact.format === 'json') {
    return `<pre class="text-sm">${props.artifact.content}</pre>`
  }
  const html = marked.parse(props.artifact.content) as string
  return postProcessHtml(html)
})
</script>
