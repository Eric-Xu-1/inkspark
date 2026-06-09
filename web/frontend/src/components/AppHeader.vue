<template>
  <header class="flex items-center justify-between px-4 md:px-6 py-3 md:py-4 shrink-0">
    <div class="flex items-center gap-2 md:gap-3 min-w-0">
      <span class="text-lg md:text-xl">⌨️</span>
      <span class="text-base md:text-lg font-semibold text-gray-800 truncate">InkSpark</span>
      <button class="hidden sm:inline-flex ml-2 md:ml-4 px-3 py-1 text-sm bg-gray-100 rounded-full text-gray-600 hover:bg-gray-200">
        历史记录
      </button>
    </div>
    <div v-if="showActions" class="flex items-center gap-2 md:gap-3 shrink-0">
      <router-link to="/" class="px-3 md:px-4 py-1.5 text-xs md:text-sm border rounded-full hover:bg-gray-50 whitespace-nowrap">
        新建对话
      </router-link>
      <button class="hidden sm:inline-flex px-3 md:px-4 py-1.5 text-xs md:text-sm border rounded-full hover:bg-gray-50">
        分享
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{ showActions?: boolean }>()
</script>
