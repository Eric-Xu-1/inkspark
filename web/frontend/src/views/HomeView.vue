<template>
  <div class="min-h-screen bg-ink-bg">
    <AppHeader />
    <main class="max-w-3xl mx-auto px-4 md:px-6 pt-6 md:pt-8 pb-12 md:pb-16">
      <div class="text-center mb-6 md:mb-8">
        <div class="text-5xl md:text-6xl mb-4 md:mb-6">⌨️</div>
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 mb-2 md:mb-3">你好，创作者！</h1>
        <p class="text-sm md:text-base text-gray-500 px-2">今天想创作什么？选择需要的模式，开始你的创作冒险吧～</p>
      </div>

      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 md:p-6">
        <textarea
          v-model="prompt"
          class="w-full border-0 resize-none text-gray-800 placeholder-gray-400 focus:outline-none text-base min-h-[80px]"
          placeholder="描述你的创作需求，比如：写一篇关于AI发展的深度文章"
        />

        <div class="flex items-center gap-2 mt-4 flex-wrap">
          <button class="w-8 h-8 flex items-center justify-center rounded-lg border text-gray-400 hover:bg-gray-50">+</button>
          <select v-model="mode" class="text-sm border rounded-full px-3 py-1.5 bg-gray-50 text-gray-700">
            <option>启发模式 (预览版)</option>
            <option>快速模式</option>
          </select>
          <select v-model="category" class="text-sm border rounded-full px-3 py-1.5 bg-gray-50 text-gray-700">
            <option>技术文章</option>
            <option>深度报告</option>
            <option>行业分析</option>
          </select>
          <div class="flex-1" />
          <button
            class="w-9 h-9 bg-gray-900 text-white rounded-full flex items-center justify-center hover:bg-gray-700 disabled:opacity-50"
            :disabled="submitting || !prompt.trim()"
            @click="submit"
          >
            ↑
          </button>
        </div>

        <SearchScopeGrid v-model="searchScope" />
      </div>

      <AgentProfiles />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import SearchScopeGrid from '../components/SearchScopeGrid.vue'
import AgentProfiles from '../components/AgentProfiles.vue'
import { createConversation, startConversation } from '../api'

const router = useRouter()
const prompt = ref('')
const mode = ref('启发模式 (预览版)')
const category = ref('技术文章')
const submitting = ref(false)
const searchScope = ref({
  notes: false,
  knowledge_base: false,
  web: true,
  literature: true,
})

async function submit() {
  if (!prompt.value.trim() || submitting.value) return
  submitting.value = true
  try {
    const id = await createConversation()
    await startConversation(id, {
      topic: prompt.value.trim(),
      requirements: '',
      mode: mode.value,
      category: category.value,
      search_scope: searchScope.value,
    })
    router.push(`/workspace/${id}`)
  } finally {
    submitting.value = false
  }
}
</script>
