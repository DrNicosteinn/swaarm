<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <header class="border-b border-gray-800 px-6 py-4">
      <div class="max-w-5xl mx-auto flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-3 hover:opacity-80">
          <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-sm font-bold">S</div>
          <span class="text-lg font-semibold">SwarmSight AI</span>
        </router-link>
        <span class="text-xs text-gray-500">Multi-Agent Social Simulation</span>
      </div>
    </header>
    <main class="max-w-5xl mx-auto px-6 py-8">
      <router-view />
    </main>
  </div>
</template>

<style>
@import "tailwindcss";
</style>
