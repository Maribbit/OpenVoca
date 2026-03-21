<template>
  <div
    class="font-sans antialiased text-gray-900 bg-paper-light min-h-screen app-container"
  >
    <header class="p-6">
      <h1 class="font-serif text-3xl text-ink-light">OpenVoca</h1>
      <p class="text-ink-muted mt-2 font-sans text-sm tracking-wide uppercase">
        Learn Naturally.
      </p>
    </header>

    <main class="max-w-3xl mx-auto px-6 py-12">
      <router-view></router-view>

      <div
        class="mt-12 p-8 border border-gray-200 rounded-2xl bg-white shadow-sm font-serif"
      >
        <p class="text-lg leading-relaxed text-ink-light decoration-gray-300">
          OpenVoca is ready. We are starting
          <strong
            class="font-bold cursor-help hover:text-blue-700 transition-colors"
            >Phase 1</strong
          >
          to read LLM-generated sentences.
        </p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
  // OpenVoca App Entry
</script>
