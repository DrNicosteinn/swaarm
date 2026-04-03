# Swaarm — CLAUDE.md

## Projekt

Swaarm ist eine SaaS-Plattform die mit KI-Agenten simuliert, wie die Öffentlichkeit auf Unternehmenskommunikation reagiert — bevor sie veröffentlicht wird. Pre-Testing Platform for Strategic Communications.

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, Pydantic, asyncio, networkx, SQLite (Simulation), ARQ (Redis Queue)
- **Frontend:** React 18+, Vite, Tailwind CSS, shadcn/ui, D3.js, TypeScript
- **Datenbank:** Supabase (PostgreSQL + Auth)
- **Billing:** Stripe
- **Deployment:** Railway (Backend), Vercel (Frontend)
- **Monitoring:** Sentry, Loguru
- **LLM:** OpenAI GPT-4o-mini (provider-agnostisch gebaut)

## Befehle

```bash
# Backend
cd backend && uv run uvicorn app.main:app --reload
cd backend && uv run pytest
cd backend && uv run ruff check .
cd backend && uv run ruff format .

# Frontend
cd frontend && npm run dev
cd frontend && npm run build
cd frontend && npm run lint
cd frontend && npm run test
```

## Architektur-Regeln

IMPORTANT: Diese Regeln müssen eingehalten werden.

1. **Provider-agnostisch:** LLM-Calls gehen über ein Adapter-Interface, NICHT direkt an OpenAI SDK. Jeder Provider muss austauschbar sein.
2. **Platform Abstraction:** Jede simulierte Plattform (Öffentliches/Professionelles Netzwerk) ist ein austauschbares Modul hinter einem gemeinsamen Interface.
3. **SQLite pro Simulation:** Jede Simulation bekommt eine eigene SQLite-DB. Nach Abschluss werden Ergebnisse in PostgreSQL persistiert.
4. **Pydantic everywhere:** Alle Datenmodelle, API-Schemas, und Konfigurationen als Pydantic Models.
5. **Async-first:** Alle IO-Operationen (LLM-Calls, DB, Redis) sind async. Keine blocking Calls im Event Loop.
6. **Deutsche UI:** Alle User-facing Strings auf Deutsch. Code, Comments, Variablennamen auf Englisch.
7. **Deep Modules:** Lieber wenige Module mit einfachen Interfaces und komplexer Implementierung als viele kleine Wrapper.

## Code Style

- Python: Ruff (Linting + Formatting), Type Hints überall, Docstrings für öffentliche Funktionen
- TypeScript: ESLint + Prettier, strict mode, keine `any` Types
- Commits: Konventionelle Commit Messages (feat:, fix:, refactor:, docs:, test:)
- Tests: Verhalten testen, nicht Implementierung. Öffentliche Interfaces testen, keine privaten Methoden.

## Projektstruktur

```
swaarm/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── api/                 # REST + WebSocket endpoints
│   │   ├── core/                # Config, Auth, Dependencies
│   │   ├── models/              # Pydantic models
│   │   ├── services/            # Business logic
│   │   ├── simulation/          # Simulation Engine
│   │   │   ├── engine.py        # Core loop
│   │   │   ├── agents.py        # Agent state management
│   │   │   ├── graph.py         # Social graph (networkx)
│   │   │   ├── actions.py       # Action system
│   │   │   ├── platforms/       # Platform modules
│   │   │   │   ├── base.py      # Abstract platform interface
│   │   │   │   ├── public.py    # Öffentliches Netzwerk (Twitter-like)
│   │   │   │   └── professional.py  # Professionelles Netzwerk (LinkedIn-like)
│   │   │   ├── personas.py      # Persona generator
│   │   │   └── willingness.py   # Willingness scoring
│   │   ├── llm/                 # LLM adapter layer
│   │   │   ├── base.py          # Abstract LLM interface
│   │   │   └── openai.py        # OpenAI implementation
│   │   └── reports/             # Report generation
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Route pages
│   │   ├── hooks/               # Custom React hooks
│   │   ├── lib/                 # Utilities, API client, Supabase client
│   │   └── i18n/                # Internationalization (German first)
│   └── public/
├── PRD.md
├── task_plan.md
├── findings.md
└── progress.md
```

## Wichtige Referenzen

- PRD: `PRD.md` (oder GitHub Issue #1)
- GitHub Issues: #2-#14 (vertikale Slices)
- Businessplan: `Businessplan_SwarmSight_AI.docx`
- Wettbewerbsanalyse: `competitor_research_pricing.md`
- Technische Notizen: `WORKING_NOTES.md`

## Gotchas

- Supabase Auth JWT muss im Backend validiert werden (nicht nur im Frontend)
- Stripe Webhooks brauchen Raw Body für Signature Verification — FastAPI Middleware beachten
- WebSocket-Connections müssen bei Railway korrekt konfiguriert sein (Proxy-Timeout)
- SQLite ist nicht thread-safe — pro Simulation ein eigener Connection-Pool oder async via aiosqlite
- GPT-4o-mini Function Calling: max 128 Tools, wir brauchen nur 6-15 Actions pro Plattform
