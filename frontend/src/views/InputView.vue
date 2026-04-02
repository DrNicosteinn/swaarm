<template>
  <div class="space-y-8">
    <div>
      <h1 class="text-3xl font-bold mb-2">Neue Simulation</h1>
      <p class="text-gray-400">Beschreibe dein Szenario und SwarmSight simuliert die Social-Media-Reaktion.</p>
    </div>

    <form @submit.prevent="startSimulation" class="space-y-6">
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">Szenario *</label>
        <textarea
          v-model="form.scenario"
          rows="4"
          class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          placeholder="z.B. Nestle kuendigt an, Cailler-Schokolade neu in Plastik statt Karton zu verpacken. Das Unternehmen betont die bessere Recycelbarkeit."
          required
        ></textarea>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">Kontext</label>
        <textarea
          v-model="form.context"
          rows="2"
          class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          placeholder="z.B. Schweizer Markt, Nachhaltigkeit ist Topthema, Migros und Coop haben kuerzlich auf weniger Plastik umgestellt"
        ></textarea>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">Zielgruppe</label>
        <input
          v-model="form.target_audience"
          type="text"
          class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          placeholder="z.B. Schweizer Social-Media-Nutzer, 20-55 Jahre"
        />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">Anzahl Agenten</label>
          <select v-model="form.num_agents" class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 focus:outline-none focus:border-blue-500">
            <option :value="10">10 (Schnelltest)</option>
            <option :value="50">50 (Standard)</option>
            <option :value="100">100 (Detailliert)</option>
            <option :value="200">200 (Umfassend)</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">Simulationsrunden</label>
          <select v-model="form.num_rounds" class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 focus:outline-none focus:border-blue-500">
            <option :value="5">5 Runden (Schnelltest)</option>
            <option :value="10">10 Runden</option>
            <option :value="20">20 Runden (Standard)</option>
            <option :value="50">50 Runden (Ausfuehrlich)</option>
          </select>
        </div>
      </div>

      <div v-if="error" class="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-300">
        {{ error }}
      </div>

      <button
        type="submit"
        :disabled="loading || !form.scenario"
        class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium py-3 px-6 rounded-lg transition-colors"
      >
        {{ loading ? 'Personas werden generiert...' : 'Simulation erstellen' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/index.js'

const router = useRouter()
const loading = ref(false)
const error = ref(null)

const form = ref({
  scenario: '',
  context: '',
  target_audience: '',
  num_agents: 50,
  num_rounds: 20,
})

async function startSimulation() {
  loading.value = true
  error.value = null
  try {
    const { data } = await api.createSimulation(form.value)
    router.push(`/simulation/${data.id}`)
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    loading.value = false
  }
}
</script>
