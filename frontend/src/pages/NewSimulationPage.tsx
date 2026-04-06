import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

type Step = 'input' | 'analyzing' | 'review' | 'starting'

interface StructuredScenario {
  industry: string
  company: string
  target_audience: string
  market: string
  statement: string
  context: string
  scenario_type: string
  controversity_score: number
  missing_fields: string[]
  suggestions: string[]
  seed_posts: string[]
}

export function NewSimulationPage() {
  const { session } = useAuth()
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('input')
  const [inputText, setInputText] = useState('')
  const [scenario, setScenario] = useState<StructuredScenario | null>(null)
  const [platform, setPlatform] = useState<'public' | 'professional'>('public')
  const [agentCount, setAgentCount] = useState(200)
  const [rounds, setRounds] = useState(50)
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)

  const token = session?.access_token

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
      setScenario(data.scenario)
      setStep('review')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler bei der Analyse')
      setStep('input')
    }
  }

  const handleStart = async () => {
    if (!scenario || !token) return
    setStarting(true)

    try {
      const res = await fetch('/api/simulation/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          scenario,
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

  const controversityLabel = (score: number) => {
    if (score >= 0.6) return 'Krise'
    if (score >= 0.3) return 'Standard'
    return 'Routine'
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
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Neue Simulation</h2>
        <p className="text-gray-500 mb-8">
          Beschreibe dein Kommunikationsszenario und die KI analysiert es.
        </p>

        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm mb-6">{error}</div>
        )}

        {/* Step 1: Input */}
        {(step === 'input' || step === 'analyzing') && (
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dein Szenario
            </label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              rows={6}
              placeholder="z.B. SwissBank kündigt Entlassung von 200 Mitarbeitern an. Statement: 'Die Restrukturierung ist notwendig für die Zukunftsfähigkeit des Unternehmens.'"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
            <button
              onClick={handleAnalyze}
              disabled={!inputText.trim() || step === 'analyzing'}
              className="mt-4 w-full bg-gray-900 text-white py-2.5 rounded-lg font-medium hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {step === 'analyzing' ? 'Analysiere...' : 'Analysieren'}
            </button>
          </div>
        )}

        {/* Step 2: Review */}
        {step === 'review' && scenario && (
          <div className="space-y-6">
            {/* Extracted fields */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Erkannte Informationen</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                {scenario.industry && (
                  <div>
                    <span className="text-gray-500">Branche</span>
                    <p className="font-medium">{scenario.industry}</p>
                  </div>
                )}
                {scenario.company && (
                  <div>
                    <span className="text-gray-500">Unternehmen</span>
                    <p className="font-medium">{scenario.company}</p>
                  </div>
                )}
                {scenario.target_audience && (
                  <div>
                    <span className="text-gray-500">Zielgruppe</span>
                    <p className="font-medium">{scenario.target_audience}</p>
                  </div>
                )}
                {scenario.market && (
                  <div>
                    <span className="text-gray-500">Markt</span>
                    <p className="font-medium">{scenario.market}</p>
                  </div>
                )}
                <div>
                  <span className="text-gray-500">Szenario-Typ</span>
                  <p className="font-medium">{scenario.scenario_type.replace('_', ' ')}</p>
                </div>
                <div>
                  <span className="text-gray-500">Kontroversität</span>
                  <p className="font-medium">
                    {controversityLabel(scenario.controversity_score)} ({(scenario.controversity_score * 100).toFixed(0)}%)
                  </p>
                </div>
              </div>

              {scenario.statement && (
                <div className="mt-4">
                  <span className="text-sm text-gray-500">Statement</span>
                  <p className="text-sm font-medium mt-1">{scenario.statement}</p>
                </div>
              )}
            </div>

            {/* Missing fields */}
            {scenario.missing_fields.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-5">
                <h4 className="text-sm font-medium text-yellow-800 mb-2">Fehlende Informationen</h4>
                <ul className="text-sm text-yellow-700 space-y-1">
                  {scenario.missing_fields.map((f, i) => (
                    <li key={i}>- {f}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Seed posts preview */}
            {scenario.seed_posts.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Auslöser-Posts</h3>
                <p className="text-sm text-gray-500 mb-3">Diese Posts starten die Diskussion:</p>
                {scenario.seed_posts.map((post, i) => (
                  <div key={i} className="bg-gray-50 rounded-lg p-3 mb-2 text-sm text-gray-700">
                    {post}
                  </div>
                ))}
              </div>
            )}

            {/* Simulation parameters */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Parameter</h3>

              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">Plattform</label>
                  <div className="flex gap-3 mt-2">
                    <button
                      onClick={() => setPlatform('public')}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium border ${
                        platform === 'public'
                          ? 'bg-gray-900 text-white border-gray-900'
                          : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      Öffentlich (Twitter)
                    </button>
                    <button
                      onClick={() => setPlatform('professional')}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium border ${
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
                    <label className="text-sm font-medium text-gray-700">Agents</label>
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
                    <label className="text-sm font-medium text-gray-700">Runden</label>
                    <select
                      value={rounds}
                      onChange={(e) => setRounds(Number(e.target.value))}
                      className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                    >
                      <option value={10}>10 (Schnell)</option>
                      <option value={25}>25 (Kurz)</option>
                      <option value={50}>50 (Standard)</option>
                      <option value={100}>100 (Ausführlich)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={() => setStep('input')}
                className="flex-1 py-2.5 rounded-lg text-sm font-medium border border-gray-300 text-gray-700 hover:bg-gray-50"
              >
                Zurück
              </button>
              <button
                onClick={handleStart}
                disabled={starting}
                className="flex-1 bg-gray-900 text-white py-2.5 rounded-lg font-medium hover:bg-gray-800 disabled:opacity-50"
              >
                {starting ? 'Starte...' : 'Simulation starten'}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
