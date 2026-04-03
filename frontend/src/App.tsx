import { useEffect, useState } from 'react'

function App() {
  const [health, setHealth] = useState<string>('Verbinde...')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => setHealth(data.status))
      .catch(() => setHealth('Nicht verbunden'))
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Swaarm</h1>
        <p className="text-lg text-gray-600 mb-8">
          Pre-Testing Platform for Strategic Communications
        </p>
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white shadow-sm border">
          <span
            className={`w-2 h-2 rounded-full ${
              health === 'healthy' ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-600">
            API: {health === 'healthy' ? 'Verbunden' : health}
          </span>
        </div>
      </div>
    </div>
  )
}

export default App
