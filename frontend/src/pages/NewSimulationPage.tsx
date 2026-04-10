import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

type Step = 'input' | 'analyzing' | 'questions' | 'summary' | 'starting'

interface AnalysisResult {
  scenario_summary: string
  follow_up_questions: string[]
  entities: Array<{
    name: string
    entity_type: string
    sub_type: string
    importance: number
    enrichment: string
  }>
  persona_strategy: {
    total: number
    recommended_platform: string
  }
}

const ENTITY_TYPE_COLORS: Record<string, string> = {
  real_person: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  real_company: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
  role: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  institution: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  media_outlet: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
  product: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  event: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
}

const ENTITY_TYPE_LABELS: Record<string, string> = {
  real_person: 'Person',
  real_company: 'Unternehmen',
  role: 'Rolle',
  institution: 'Institution',
  media_outlet: 'Medium',
  product: 'Produkt',
  event: 'Ereignis',
}

const EXAMPLE_PROMPTS = [
  'Wie reagiert die Oeffentlichkeit auf unsere neue Marketingkampagne?',
  'Novartis plant den Abbau von 800 Stellen in Basel. Wie reagieren Mitarbeiter und Medien?',
  'Welche LinkedIn-Strategie kommt bei unserer B2B-Zielgruppe besser an?',
]

export function NewSimulationPage() {
  const { session } = useAuth()
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('input')
  const [inputText, setInputText] = useState('')
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [questionAnswers, setQuestionAnswers] = useState<Record<number, string>>({})
  const [error, setError] = useState('')

  const token = session?.access_token

  // Step 1 → Step 2: Analyze input
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

      const result: AnalysisResult = {
        scenario_summary: data.decision?.scenario_summary || '',
        follow_up_questions: data.decision?.follow_up_questions || [],
        entities: data.decision?.entities || [],
        persona_strategy: data.decision?.persona_strategy || { total: 200, recommended_platform: 'public' },
      }

      setAnalysis(result)

      if (result.follow_up_questions.length > 0) {
        setStep('questions')
      } else {
        setStep('summary')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler bei der Analyse')
      setStep('input')
    }
  }

  // Step 2 → Step 3: Continue to summary
  const handleQuestionsComplete = () => {
    setStep('summary')
  }

  // Step 3: Quick-start
  const handleQuickStart = async () => {
    if (!token) return
    setStep('starting')
    setError('')

    // Build additional context from answered questions
    const additionalContext = Object.entries(questionAnswers)
      .filter(([, answer]) => answer.trim())
      .map(([idx, answer]) => {
        const question = analysis?.follow_up_questions[Number(idx)] || ''
        return `Frage: ${question}\nAntwort: ${answer}`
      })
      .join('\n\n')

    try {
      const res = await fetch('/api/simulation/quick-start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          input_text: inputText,
          additional_context: additionalContext,
        }),
      })

      if (!res.ok) throw new Error('Simulation konnte nicht gestartet werden')
      const data = await res.json()
      navigate(`/simulation/${data.simulation_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Start')
      setStep('summary')
    }
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

        {/* ===== STEP 1: Fragestellung ===== */}
        {(step === 'input' || step === 'analyzing') && (
          <>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Neue Simulation</h2>
            <p className="text-gray-500 mb-8">
              Beschreibe dein Szenario oder stelle eine Frage.
            </p>

            <div className="bg-white rounded-xl shadow-sm border p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Was willst du testen?
              </label>
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                rows={5}
                placeholder="Beschreibe dein Szenario oder stelle eine Frage..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm resize-y"
              />

              {/* Example chips */}
              <div className="flex flex-wrap gap-2 mt-3">
                {EXAMPLE_PROMPTS.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => setInputText(prompt)}
                    className="text-xs px-3 py-1.5 bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 transition-colors"
                  >
                    {prompt.slice(0, 50)}...
                  </button>
                ))}
              </div>

              <button
                onClick={handleAnalyze}
                disabled={!inputText.trim() || step === 'analyzing'}
                className="mt-6 w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {step === 'analyzing' ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    KI analysiert...
                  </>
                ) : (
                  'Analysieren'
                )}
              </button>
            </div>
          </>
        )}

        {/* ===== STEP 2: Gefuehrte Fragen ===== */}
        {step === 'questions' && analysis && (
          <>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Kontext ergaenzen</h2>
            <p className="text-gray-500 mb-8">
              Um eine bessere Simulation zu erstellen, haben wir noch ein paar Fragen.
            </p>

            <div className="bg-white rounded-xl shadow-sm border p-6 space-y-6">
              {analysis.follow_up_questions.map((question, i) => (
                <div key={i}>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {question}
                  </label>
                  <textarea
                    value={questionAnswers[i] || ''}
                    onChange={(e) =>
                      setQuestionAnswers((prev) => ({ ...prev, [i]: e.target.value }))
                    }
                    rows={2}
                    placeholder="Optional — du kannst auch ueberspringen"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
                  />
                </div>
              ))}
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setStep('input')}
                className="flex-1 py-2.5 rounded-lg text-sm font-medium border border-gray-300 text-gray-700 hover:bg-gray-50"
              >
                Zurueck
              </button>
              <button
                onClick={handleQuestionsComplete}
                className="flex-1 bg-indigo-600 text-white py-2.5 rounded-lg font-medium hover:bg-indigo-500"
              >
                Weiter
              </button>
            </div>
          </>
        )}

        {/* ===== STEP 3: Zusammenfassung ===== */}
        {(step === 'summary' || step === 'starting') && analysis && (
          <>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Zusammenfassung</h2>
            <p className="text-gray-500 mb-8">
              Pruefe ob das System dein Szenario korrekt verstanden hat.
            </p>

            {/* Scenario summary */}
            <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
              <p className="text-gray-800 text-sm leading-relaxed">
                {analysis.scenario_summary || inputText.slice(0, 200)}
              </p>
            </div>

            {/* Extracted entities */}
            {analysis.entities.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-3">
                  Erkannte Entitaeten ({analysis.entities.length})
                </h3>
                <div className="flex flex-wrap gap-2">
                  {analysis.entities.map((entity, i) => {
                    const colorClass = ENTITY_TYPE_COLORS[entity.entity_type] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'
                    return (
                      <span
                        key={i}
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border ${colorClass}`}
                      >
                        <span>{entity.name}</span>
                        <span className="opacity-60">
                          {ENTITY_TYPE_LABELS[entity.entity_type] || entity.entity_type}
                          {entity.sub_type ? ` — ${entity.sub_type}` : ''}
                        </span>
                        {entity.enrichment === 'enrich' && (
                          <span className="text-[10px] opacity-50">wird recherchiert</span>
                        )}
                      </span>
                    )
                  })}
                </div>
                <p className="text-xs text-gray-500 mt-3">
                  {analysis.entities.filter((e) => e.enrichment === 'enrich').length} Entitaeten
                  werden per Web-Recherche angereichert
                </p>
              </div>
            )}

            {/* Persona strategy info */}
            <div className="bg-gray-50 rounded-xl border p-4 mb-6 text-sm">
              <span className="text-gray-500">Geplant: </span>
              <span className="font-medium text-gray-900">
                ~{analysis.persona_strategy.total} Personas
              </span>
              <span className="text-gray-400 ml-2">
                auf {analysis.persona_strategy.recommended_platform === 'professional'
                  ? 'LinkedIn (Professionell)'
                  : 'Twitter (Oeffentlich)'}
              </span>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={() =>
                  analysis.follow_up_questions.length > 0
                    ? setStep('questions')
                    : setStep('input')
                }
                className="flex-1 py-2.5 rounded-lg text-sm font-medium border border-gray-300 text-gray-700 hover:bg-gray-50"
              >
                Zurueck
              </button>
              <button
                onClick={handleQuickStart}
                disabled={step === 'starting'}
                className="flex-1 bg-indigo-600 text-white py-2.5 rounded-lg font-medium hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {step === 'starting' ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Wird vorbereitet...
                  </>
                ) : (
                  'Simulation vorbereiten'
                )}
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
