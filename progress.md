# Swaarm - Progress Log

## Session 1 — 2026-04-03 (Planung)

### Actions
- [x] Cleaned project folder, connected new GitHub remote (swaarm)
- [x] Analyzed Businessplan, Competitor Research, Working Notes
- [x] Installed 10 skills
- [x] Completed grill-me: 29 architectural decisions documented
- [x] Wrote full PRD (PRD.md) → GitHub Issue #1
- [x] Created 13 vertical-slice issues (#2-#14)
- [x] Created CLAUDE.md, SIMULATION_ENGINE_BLUEPRINT.md (22 Teile, 1032 Zeilen)
- [x] Deep research: OASIS architecture, willingness scoring, agent memory, prompt engineering
- [x] Deep research: DACH personas, social graph algorithms, narrative detection, feed algorithms
- [x] Created BAUPLAN_ERKLAERT.docx (non-technical explanation)

---

## Session 2 — 2026-04-06 (Building)

### Issue #2: Projekt-Setup & Infrastruktur ✅
**Commit:** `0579866` on `main`
- FastAPI backend with health check endpoint
- React + Vite + Tailwind CSS frontend
- Supabase project connected (frontend + backend)
- OpenAI API key configured
- Sentry + Loguru integration
- Project structure matching PRD architecture
- Auto-format hooks (ruff for Python, prettier for JS/TS)
- Security gate hook (blocks force-push, rm -rf)
- **Tests:** 1 passed (health check)

### Issue #3: Auth: Registrierung & Login ✅
**Commit:** `5f651b4` on `main`
- Backend: Supabase JWT validation middleware, `/api/auth/me` endpoint
- Frontend: Login page, Register page (German UI)
- Dashboard with empty state and logout
- Protected routes (redirect to /login)
- useAuth hook (signIn, signUp, signOut, session management)
- Supabase client for React (NOT Next.js — adapted correctly)
- **Tests:** 1 passed (health check, auth tested via preview)
- **Verified:** Login + Register pages render correctly in preview

### Issue #4: Simulation Engine Core — IN PROGRESS
**Branch:** `feature/simulation-engine` (separate branch, each step = 1 commit)

#### Step 1/12: Data Models ✅
**Commit:** `157345d`
- Persona model: Big Five, Sinus-Milieu, stakeholder roles, opinion seeds, posting style
- AgentState model: memory (sliding window + important + summary), cooldown, sentiment
- Actions: PublicNetworkAction (6 types), ProfessionalNetworkAction (15 types)
- SimulationConfig: tier distributions, controversity levels, quality metrics
- AgentAction, FeedItem, RoundMetrics, SimulationEvent, QualityMetrics
- **Tests:** 18/18 passed

#### Step 2/12: SQLite Schema & CRUD ✅
**Commit:** `c17752e`
- 9 tables: users, posts, comments, likes, follows, reposts, action_log, round_metrics, checkpoints
- WAL mode + performance pragmas (64MB cache, busy timeout)
- Batch insert for users and action logs
- Feed query with round filtering and engagement ordering
- Duplicate-safe likes and follows (INSERT OR IGNORE)
- **Tests:** 11/11 passed

#### Step 3/12: Social Graph ✅
**Commit:** `86bf0c2`
- Community structure based on stakeholder roles
- Directed graph for public network (Twitter-like follows)
- Undirected graph for professional network (LinkedIn-like connections)
- Influencer hubs (power creators get extra cross-community connections)
- Weak ties (Granovetter bridges, ~5% inter-community edges)
- Deterministic generation with seed parameter
- **Tests:** 14/14 passed

#### Step 4/12: LLM Adapter ✅
**Commit:** `f24b068`
- Abstract LLMProvider interface (any provider implements chat + generate_simple)
- OpenAI implementation: async client, function calling, prompt caching tracking
- Retry with exponential backoff + full jitter (5 retries)
- Error classification: rate limit → retry, bad request → permanent, timeout → retry
- LLMUsageTracker with cost calculation (cached token pricing)
- **Tests:** 10/10 passed

#### Step 5/12: Willingness Scoring ✅
**Commit:** `b6c0152`
- Socialtrait-inspired: s_persona × exp(-λ × (s_context - s_persona))
- Persona factors: extraversion, tier bonus, posting frequency, opinion strength
- Context factors: topic relevance, network activity, emotional valence
- Dynamic tier distribution (routine/standard/crisis)
- Cooldown per tier (creator=2, responder=3, engager=5, observer=12)
- Vectorized numpy — <5ms for 50k agents
- **Tests:** 10/10 passed

#### Step 6/12: Public Network Platform ✅
**Commit:** `d6dd567`
- Abstract PlatformBase interface
- PublicNetworkPlatform: 6 actions via OpenAI function calling
- Feed algorithm: Twitter engagement weights (Like=1x, RT=20x, Reply=13.5x)
- Feed assembly: 85% relevant + 15% serendipity
- Compact feed-to-prompt serialization (~200 tokens)
- **Tests:** 13/13 passed

#### Step 7/12: Agent Memory System ✅
**Commit:** `1897fa6`
- Sliding window (5 observations), importance scoring, periodic LLM summary
- Observation text generator (German)
- Memory prompt builder (~150 tokens budget)
- **Tests:** 18/18 passed

#### Step 8/12: Simulation Engine Core Loop ✅
**Commit:** `1897fa6` (combined with step 7)
- Complete round loop: activation → feed → LLM → actions → metrics → events
- Tiered processing: full LLM / simplified / rule-based
- Async parallel with semaphore concurrency
- Event emission for live-streaming
- Error recovery: failed agents degrade to observers
- **Tests:** 7/7 passed (mock LLM)
- **LIVE TEST with GPT-4o-mini:** 10 agents, 5 rounds, $0.0021, 17.8s ✅

#### Security & Compliance ✅
**Commit:** `c51b5ef`
- Fixed error message leaking, global exception handler
- AI_SYSTEM_CARD.md for EU AI Act compliance
- CORS restricted, Swagger disabled in production

#### Steps 9-12 — NEXT
- Metrics & QA, Error Handling, Checkpoint, Integration Test

**Running total: 95+ tests, all green**

### Errors
(none)
