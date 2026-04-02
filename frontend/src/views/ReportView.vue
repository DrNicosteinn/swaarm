<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">Report</h1>
      <router-link :to="`/simulation/${id}`" class="text-blue-400 hover:text-blue-300 text-sm">
        Zurueck zur Simulation
      </router-link>
    </div>

    <!-- Report Content -->
    <div v-if="loading" class="text-center py-12 text-gray-400">
      Report wird generiert... Dies kann 1-2 Minuten dauern.
    </div>

    <div v-else-if="report" class="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <div class="prose prose-invert max-w-none" v-html="renderedReport"></div>
    </div>

    <div v-else class="text-center py-12">
      <button
        @click="generateReport"
        class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
      >
        Report generieren
      </button>
    </div>

    <!-- Chat -->
    <div v-if="report" class="space-y-4">
      <h2 class="text-lg font-semibold text-gray-300">Fragen zum Report</h2>
      <div class="space-y-3 max-h-96 overflow-y-auto">
        <div
          v-for="(msg, i) in chatHistory"
          :key="i"
          :class="msg.role === 'user' ? 'text-right' : 'text-left'"
        >
          <div
            :class="msg.role === 'user'
              ? 'bg-blue-900/50 text-blue-100 inline-block rounded-lg px-4 py-2 max-w-[80%] text-sm'
              : 'bg-gray-800 text-gray-200 inline-block rounded-lg px-4 py-2 max-w-[80%] text-sm'"
          >
            {{ msg.content }}
          </div>
        </div>
      </div>
      <form @submit.prevent="sendChat" class="flex gap-2">
        <input
          v-model="chatInput"
          type="text"
          class="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
          placeholder="Frage zum Report stellen..."
          :disabled="chatLoading"
        />
        <button
          type="submit"
          :disabled="chatLoading || !chatInput"
          class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
        >
          {{ chatLoading ? '...' : 'Senden' }}
        </button>
      </form>
    </div>

    <div v-if="error" class="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-300 text-sm">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/index.js'

const props = defineProps({ id: String })

const report = ref(null)
const loading = ref(false)
const error = ref(null)
const chatInput = ref('')
const chatLoading = ref(false)
const chatHistory = ref([])

const renderedReport = computed(() => {
  if (!report.value) return ''
  return report.value
    .replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold text-gray-200 mt-4 mb-2">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold text-gray-100 mt-6 mb-3">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold text-white mt-6 mb-3">$1</h1>')
    .replace(/^\- (.+)$/gm, '<li class="ml-4 text-gray-300">$1</li>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-gray-100">$1</strong>')
    .replace(/\n\n/g, '</p><p class="text-gray-300 mb-3">')
    .replace(/^(?!<)(.+)$/gm, '<p class="text-gray-300 mb-3">$1</p>')
})

async function generateReport() {
  loading.value = true
  error.value = null
  try {
    const { data } = await api.generateReport(props.id)
    report.value = data.report
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    loading.value = false
  }
}

async function sendChat() {
  const msg = chatInput.value.trim()
  if (!msg) return

  chatHistory.value.push({ role: 'user', content: msg })
  chatInput.value = ''
  chatLoading.value = true

  try {
    const { data } = await api.chatWithReport(props.id, msg, chatHistory.value.slice(0, -1))
    chatHistory.value.push({ role: 'assistant', content: data.response })
  } catch (e) {
    chatHistory.value.push({ role: 'assistant', content: 'Fehler: ' + (e.response?.data?.error || e.message) })
  } finally {
    chatLoading.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await api.getReport(props.id)
    report.value = data.report
  } catch {
    // Report not yet generated
  }
})
</script>
