<template>
  <div class="space-y-6">
    <!-- Status Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">Simulation {{ id }}</h1>
        <p class="text-gray-400 text-sm mt-1">{{ sim?.scenario?.slice(0, 100) }}...</p>
      </div>
      <div class="flex items-center gap-3">
        <span :class="statusClass" class="px-3 py-1 rounded-full text-sm font-medium">
          {{ statusLabel }}
        </span>
        <button
          v-if="sim?.status === 'ready'"
          @click="runSim"
          class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Simulation starten
        </button>
        <button
          v-if="sim?.status === 'running'"
          @click="stopSim"
          class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Stoppen
        </button>
        <button
          v-if="sim?.status === 'completed'"
          @click="goToReport"
          class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Report generieren
        </button>
      </div>
    </div>

    <!-- Progress -->
    <div v-if="sim" class="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <div class="flex justify-between text-sm text-gray-400 mb-2">
        <span>Runde {{ sim.current_round }} / {{ sim.num_rounds }}</span>
        <span>{{ sim.total_actions }} Aktionen</span>
      </div>
      <div class="w-full bg-gray-800 rounded-full h-2">
        <div
          class="bg-blue-600 h-2 rounded-full transition-all duration-500"
          :style="{ width: progressPercent + '%' }"
        ></div>
      </div>
    </div>

    <!-- Feed -->
    <div class="space-y-3">
      <h2 class="text-lg font-semibold text-gray-300">Live Feed</h2>
      <div v-if="actions.length === 0" class="text-gray-500 text-center py-12">
        {{ sim?.status === 'generating_personas' ? 'Personas werden generiert...' :
           sim?.status === 'ready' ? 'Bereit. Klicke "Simulation starten".' :
           sim?.status === 'running' ? 'Warte auf erste Aktionen...' : 'Noch keine Aktionen.' }}
      </div>
      <div
        v-for="action in actions"
        :key="action.timestamp"
        class="bg-gray-900 border border-gray-800 rounded-lg p-4"
      >
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center text-xs font-bold shrink-0">
            {{ (action.agent_name || '?')[0].toUpperCase() }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 text-sm">
              <span class="font-medium text-gray-200">{{ action.agent_name }}</span>
              <span class="text-gray-600">Runde {{ action.round }}</span>
              <span :class="actionTypeClass(action.action_type)" class="px-2 py-0.5 rounded text-xs">
                {{ action.action_type }}
              </span>
            </div>
            <p v-if="action.content" class="text-gray-300 mt-1 text-sm">{{ action.content }}</p>
          </div>
        </div>
      </div>
      <button
        v-if="actions.length > 0 && actions.length < (sim?.total_actions || 0)"
        @click="loadMore"
        class="w-full text-center text-blue-400 hover:text-blue-300 py-2 text-sm"
      >
        Mehr laden...
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/index.js'

const props = defineProps({ id: String })
const router = useRouter()

const sim = ref(null)
const actions = ref([])
let pollInterval = null

const progressPercent = computed(() => {
  if (!sim.value) return 0
  return Math.round((sim.value.current_round / sim.value.num_rounds) * 100)
})

const statusLabel = computed(() => {
  const labels = {
    created: 'Erstellt',
    generating_personas: 'Personas generieren...',
    ready: 'Bereit',
    running: 'Laeuft...',
    completed: 'Abgeschlossen',
    failed: 'Fehler',
    stopped: 'Gestoppt',
  }
  return labels[sim.value?.status] || sim.value?.status
})

const statusClass = computed(() => {
  const classes = {
    created: 'bg-gray-700 text-gray-300',
    generating_personas: 'bg-yellow-900/50 text-yellow-300',
    ready: 'bg-blue-900/50 text-blue-300',
    running: 'bg-green-900/50 text-green-300',
    completed: 'bg-green-900/50 text-green-300',
    failed: 'bg-red-900/50 text-red-300',
    stopped: 'bg-gray-700 text-gray-300',
  }
  return classes[sim.value?.status] || 'bg-gray-700 text-gray-300'
})

function actionTypeClass(type) {
  if (type?.includes('POST') || type?.includes('post')) return 'bg-blue-900/50 text-blue-300'
  if (type?.includes('LIKE') || type?.includes('like')) return 'bg-pink-900/50 text-pink-300'
  if (type?.includes('REPOST') || type?.includes('repost')) return 'bg-green-900/50 text-green-300'
  if (type?.includes('FOLLOW') || type?.includes('follow')) return 'bg-purple-900/50 text-purple-300'
  return 'bg-gray-700 text-gray-400'
}

async function poll() {
  try {
    const { data } = await api.getStatus(props.id)
    sim.value = data

    if (['running', 'completed'].includes(data.status)) {
      const res = await api.getActions(props.id, 0, 100)
      actions.value = res.data.actions
    }

    if (['completed', 'failed', 'stopped'].includes(data.status)) {
      clearInterval(pollInterval)
    }
  } catch (e) {
    console.error('Poll error:', e)
  }
}

async function runSim() {
  await api.runSimulation(props.id)
  poll()
  pollInterval = setInterval(poll, 2000)
}

async function stopSim() {
  await api.stopSimulation(props.id)
  poll()
}

function goToReport() {
  router.push(`/report/${props.id}`)
}

async function loadMore() {
  const res = await api.getActions(props.id, actions.value.length, 50)
  actions.value.push(...res.data.actions)
}

onMounted(() => {
  poll()
  pollInterval = setInterval(poll, 2000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>
