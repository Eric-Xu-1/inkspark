<template>
  <section class="mt-12">
    <h2 class="text-center text-sm font-medium text-gray-500 mb-6">你的 AI 创作团队</h2>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div
        v-for="agent in agents"
        :key="agent.name"
        class="bg-white rounded-2xl border border-gray-100 p-5 text-center hover:shadow-sm transition-shadow"
      >
        <div
          class="w-14 h-14 mx-auto mb-3 rounded-full flex items-center justify-center text-2xl"
          :class="agent.bgClass"
        >
          {{ agent.emoji }}
        </div>
        <h3 class="text-base font-semibold text-gray-900 mb-1">{{ agent.name }}</h3>
        <p class="text-xs text-teal-600 font-medium mb-2">{{ agent.role }}</p>
        <p class="text-xs text-gray-400 leading-relaxed">{{ agent.desc }}</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const agents = [
  {
    name: '小美',
    role: '深度调研研究员',
    emoji: '👩',
    bgClass: 'bg-pink-50',
    desc: '搜索全网资料，提供独特的写作角度与调研摘要',
  },
  {
    name: '小青',
    role: '文章创作者',
    emoji: '👩‍💻',
    bgClass: 'bg-blue-50',
    desc: '构建文章大纲，撰写高质量、有深度的正文内容',
  },
  {
    name: '小尹',
    role: '文章审核员',
    emoji: '👩‍🏫',
    bgClass: 'bg-amber-50',
    desc: '审核内容一致性、准确性与语法，确保专业流畅',
  },
]
</script>
