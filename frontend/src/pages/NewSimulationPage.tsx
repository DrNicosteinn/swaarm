import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

type Step = 'input' | 'analyzing' | 'review' | 'starting'

interface ScenarioFields {
  statement: string
  industry: string
  company: string
  target_audience: string
  market: string
  context: string
  scenario_type: string
  controversity_score: number
  seed_posts: string[]
  suggestions: string[]
  missing_fields: string[]
}

const EMPTY_FIELDS: ScenarioFields = {
  statement: '',
  industry: '',
  company: '',
  target_audience: '',
  market: '',
  context: '',
  scenario_type: 'default',
  controversity_score: 0.5,
  seed_posts: [],
  suggestions: [],
  missing_fields: [],
}

const REQUIRED_FIELDS: (keyof ScenarioFields)[] = [
  'statement',
  'industry',
  'target_audience',
  'market',
]

const FIELD_LABELS: Record<string, string> = {
  statement: 'Statement / Kampagne',
  industry: 'Branche',
  company: 'Unternehmen',
  target_audience: 'Zielgruppe',
  market: 'Markt (Region)',
  context: 'Kontext / Hintergrund',
}

export function NewSimulationPage() {
  const { session } = useAuth()
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('input')
  const [inputText, setInputText] = useState('')
  const [fields, setFields] = useState<ScenarioFields>(EMPTY_FIELDS)
  const [platform, setPlatform] = useState<'public' | 'professional'>('public')
  const [agentCount, setAgentCount] = useState(200)
  const [rounds, setRounds] = useState(50)
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)

  const token = session?.access_token

  // Check if all required fields are filled
  const requiredComplete = REQUIRED_FIELDS.every(
    (f) => typeof fields[f] === 'string' && (fields[f] as string).trim().length > 0
  )

  const handleAnalyze = async () => {
    if (!inputText.trim() || !token) return
    setStep('analyzing')
    setError('')

    try {
      const res = await fetch('/api/simulation/analyze-input', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ text: inputText }),
      })

      if (!res.ok) throw new Error('Analyse fehlgeschlagen')
      const data = await res.json()
      setFields({
        ...EMPTY_FIELDS,
        ...data.scenario,
      })
      setStep('review')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler bei der Analyse')
      setStep('input')
    }
  }

  const handleStart = async () => {
    if (!requiredComplete || !token) return
    setStarting(true)
    setError('')

    try {
      const res = await fetch('/api/simulation/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          scenario: fields,
          platform,
          agent_count: agentCount,
          round_count: rounds,
        }),
      })

      if (!res.ok) throw new Error('Simulation konnte nicht gestartet werden')
      const data = await res.json()
      navigate(`/simulation/${data.simulation_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Start')
      setStarting(false)
    }
  }

  const updateField = (key: keyof ScenarioFields, value: string) => {
    setFields((prev) => ({ ...prev, [key]: value }))
  }

  const controversityLabel = (score: number) => {
    if (score >= 0.6) return 'Krise (hohe Aktivitaet)'
    if (score >= 0.3) return 'Standard'
    return 'Routine (niedrige Aktivitaet)'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">Swaarm</h1>
          <a href="/dashboard" className="text-sm text-gray-500 hover:text-gray-700">
            Abbrechen
          </a>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm mb-6">{error}</div>
        )}

        {/* ===== STEP 1: Freitext-Eingabe ===== */}
        {(step === 'input' || step === 'analyzing') && (
          <>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Neue Simulation</h2>
            <p className="text-gray-500 mb-8">
              Beschreibe dein Szenario in einem Satz — die KI erkennt den Rest automatisch.
            </p>

            <div className="bg-white rounded-xl shadow-sm border p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Was willst du testen?
              </label>
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                rows={4}
                placeholder='z.B. "Wie reagiert die Öffentlichkeit wenn SwissBank 200 Stellen streicht?"'
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
              <button
                onClick={handleAnalyze}
                disabled={!inputText.trim() || step === 'analyzing'}
                className="mt-4 w-full bg-gray-900 text-white py-3 rounded-lg font-medium hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {step === 'analyzing' ? 'KI analysiert...' : 'Weiter'}
              </button>
            </div>
          </>
        )}

        {/* ===== STEP 2: Review + Felder bearbeiten ===== */}
        {step === 'review' && (
          <>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Szenario vervollstaendigen</h2>
            <p className="text-gray-500 mb-6">
              Die KI hat folgende Informationen erkannt. Bitte pruefe und ergaenze die fehlenden
              Felder.
            </p>

            {/* Editable fields */}
            <div className="bg-white rounded-xl shadow-sm border p-6 space-y-5 mb-6">
              {(
                Object.entries(FIELD_LABELS) as [keyof ScenarioFields, string][]
              ).map(([key, label]) => {
                const value = (fields[key] as string) || ''
                const isRequired = REQUIRED_FIELDS.includes(key)
                const isEmpty = !value.trim()
                const isLongField = key === 'statement' || key === 'context'

                return (
                  <div key={key}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {label}
                      {isRequired && <span className="text-red-500 ml-1">*</span>}
                      {!isEmpty && (
                        <span className="ml-2 text-xs text-green-600 font-normal">
                          automatisch erkannt
                        </span>
                      )}
                    </label>
                    {isLongField ? (
                      <textarea
                        value={value}
                        onChange={(e) => updateField(key, e.target.value)}
                        rows={3}
                        placeholder={`${label} eingeben...`}
                        className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                          isEmpty && isRequired
                            ? 'border-orange-300 bg-orange-50'
                            : 'border-gray-300'
                        }`}
                      />
                    ) : (
                      <input
                        type="text"
                        value={value}
                        onChange={(e) => updateField(key, e.target.value)}
                        placeholder={`${label} eingeben...`}
                        className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                          isEmpty && isRequired
                            ? 'border-orange-300 bg-orange-50'
                            : 'border-gray-300'
                        }`}
                      />
                    )}
                  </div>
                )
              })}
            </div>

            {/* Kontroversitaet (read-only info) */}
            <div className="bg-gray-50 rounded-xl border p-4 mb-6 text-sm">
              <span className="text-gray-500">Geschaetzte Kontroversitaet: </span>
              <span className="font-medium text-gray-900">
                {controversityLabel(fields.controversity_score)}
              </span>
              <span className="text-gray-400 ml-2">
                ({(fields.controversity_score * 100).toFixed(0)}%)
              </span>
            </div>

            {/* Seed posts preview */}
            {fields.seed_posts.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border p-5 mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-3">
                  Ausloeser-Posts (automatisch generiert)
                </h3>
                {fields.seed_posts.map((post, i) => (
                  <div
                    key={i}
                    className="bg-gray-50 rounded-lg p-3 mb-2 text-sm text-gray-700 italic"
                  >
                    "{post}"
                  </div>
                ))}
              </div>
            )}

            {/* Simulation parameters */}
            <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-4">Simulations-Parameter</h3>

              <div className="mb-4">
                <label className="text-sm text-gray-600 mb-2 block">Plattform</label>
                <div className="flex gap-3">
                  <button
                    onClick={() => setPlatform('public')}
                    className={`flex-1 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                      platform === 'public'
                        ? 'bg-gray-900 text-white border-gray-900'
                        : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    Oeffentlich (Twitter)
                  </button>
                  <button
                    onClick={() => setPlatform('professional')}
                    className={`flex-1 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                      platform === 'professional'
                        ? 'bg-gray-900 text-white border-gray-900'
                        : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    Professionell (LinkedIn)
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600">Agents</label>
                  <select
                    value={agentCount}
                    onChange={(e) => setAgentCount(Number(e.target.value))}
                    className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  >
                    <option value={50}>50 (Schnelltest)</option>
                    <option value={200}>200 (Standard)</option>
                    <option value={500}>500 (Detailliert)</option>
                    <option value={1000}>1'000 (Umfangreich)</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Runden</label>
                  <select
                    value={rounds}
                    onChange={(e) => setRounds(Number(e.target.value))}
                    className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  >
                    <option value={10}>10 (Schnell)</option>
                    <option value={25}>25 (Kurz)</option>
                    <option value={50}>50 (Standard)</option>
                    <option value={100}>100 (Ausfuehrlich)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Incomplete warning */}
            {!requiredComplete && (
              <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 mb-6 text-sm text-orange-700">
                Bitte fuelle alle Pflichtfelder (*) aus, bevor du die Simulation startest.
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={() => setStep('input')}
                className="flex-1 py-2.5 rounded-lg text-sm font-medium border border-gray-300 text-gray-700 hover:bg-gray-50"
              >
                Zurueck
              </button>
              <button
                onClick={handleStart}
                disabled={!requiredComplete || starting}
                className="flex-1 bg-gray-900 text-white py-2.5 rounded-lg font-medium hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {starting ? 'Starte Simulation...' : 'Simulation starten'}
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
