# Simulation Engine — Alle 12 Schritte im Detail erklärt

Dieses Dokument erklärt jeden der 12 Entwicklungsschritte der Simulation Engine: was gebaut wurde, warum, wie es funktioniert, und welche Entscheidungen getroffen wurden.

---

## Schritt 1: Datenmodelle (Pydantic)

**Datei:** `backend/app/models/persona.py`, `agent.py`, `actions.py`, `simulation.py`
**Tests:** 18

### Was wurde gebaut?

Die "Bauzeichnungen" für alle Daten die in der Simulation vorkommen. In Python heissen diese "Datenmodelle" — sie definieren exakt welche Felder ein Objekt hat, welchen Typ die Felder haben, und welche Werte erlaubt sind.

### Warum Pydantic?

Pydantic ist eine Python-Bibliothek die Datenmodelle validiert. Wenn jemand versucht ein Alter von -5 zu setzen, wirft Pydantic sofort einen Fehler. Das verhindert Bugs bevor sie passieren. FastAPI nutzt Pydantic nativ — alle API-Inputs werden automatisch validiert.

### Was enthält jedes Modell?

**Persona (persona.py) — "Wer ist diese Person?"**

Eine Persona ist die komplette Identität eines simulierten Agents. Sie wird einmal erstellt und ändert sich nie während der Simulation. Enthält:

- **Identität:** Name, Alter, Geschlecht, Land (DE/CH/AT), Region, Stadt-Typ
- **Big Five Persönlichkeit:** 5 Werte zwischen 0.0 und 1.0 (Offenheit, Gewissenhaftigkeit, Extraversion, Verträglichkeit, Neurotizismus). Jeder Wert beeinflusst wie der Agent auf Social Media agiert.
- **Agent-Tier:** Power Creator (10%), Active Responder (40%), Selective Engager (30%), Observer (20%). Bestimmt wie oft und wie intensiv der Agent aktiv wird.
- **Posting-Stil:** Frequenz (täglich/wöchentlich/monatlich/selten), Ton (sachlich/emotional/provokativ/humorvoll), typische Themen, durchschnittliche Post-Länge.
- **Meinungs-Seeds:** 5 Grundhaltungen (Vertrauen in Institutionen, Umweltbewusstsein, Tech-Optimismus, Wirtschaftliche Sorgen, Soziale Progressivität). Je 0.0-1.0.
- **Stakeholder-Rolle:** z.B. "Mitarbeiter", "Journalist", "Kunde" — bestimmt die Perspektive.
- **Flags:** `is_zealot` (Meinung ändert sich nie), `is_contrarian` (widerspricht der Mehrheit).

Jedes Feld hat einen definierten Typ und Wertebereich. Pydantic stellt sicher, dass z.B. `age` immer zwischen 18 und 95 liegt.

**AgentState (agent.py) — "Was passiert gerade mit dieser Person?"**

Im Gegensatz zur Persona ändert sich der AgentState jede Runde. Enthält:

- **Memory:** Sliding Window der letzten 5 Beobachtungen, wichtige Erinnerungen, komprimierte Zusammenfassung.
- **Sentiment:** Aktuelle Stimmung (-1.0 bis +1.0).
- **Aktivitäts-Statistiken:** Wie viele Posts/Kommentare/Likes hat der Agent bisher gemacht?
- **Cooldown:** Bis zu welcher Runde muss der Agent pausieren?

Wichtige Methode: `is_on_cooldown(current_round)` — prüft ob der Agent gerade pausieren muss. `set_cooldown(round, duration)` — setzt den Cooldown nach einer Aktion.

**Actions (actions.py) — "Was kann ein Agent tun?"**

Definiert alle möglichen Aktionen auf den simulierten Plattformen:

- **PublicNetworkAction:** 6 Aktionen — create_post, like_post, repost, comment, follow_user, do_nothing
- **ProfessionalNetworkAction:** 15 Aktionen — post, article, 6 Reaktionstypen, comment, reply, share, connect, follow, endorse, do_nothing
- **AgentAction:** Eine konkrete Aktion die ein Agent in einer Runde ausführt — mit Agent-ID, Rundennummer, Aktionstyp, Inhalt, Ziel-Post/User.
- **FeedItem:** Ein einzelner Post im Feed eines Agents — mit Autor, Inhalt, Engagement-Zahlen, Sentiment.

**SimulationConfig (simulation.py) — "Wie soll die Simulation laufen?"**

Die komplette Konfiguration einer Simulation:

- Agent-Anzahl (10-100'000), Rundenanzahl (5-200), Plattform (public/professional)
- Kontroversität (routine/standard/crisis) — bestimmt die Tier-Verteilung
- LLM-Modell, Budget-Limit, Seed für Reproduzierbarkeit
- TierDistribution: dynamische Verteilung je nach Kontroversität (z.B. Krise → 10% Creator, 40% Responder, 30% Engager, 20% Observer)

Dazu: RoundMetrics, SimulationEvent, QualityMetrics, SimulationResult — alles was am Ende rauskommt.

---

## Schritt 2: SQLite-Datenbank

**Datei:** `backend/app/simulation/database.py`
**Tests:** 11

### Was wurde gebaut?

Eine komplette Datenbank für eine einzelne Simulation. Jede Simulation bekommt ihre eigene SQLite-Datei — z.B. `/tmp/swaarm_sim_abc123.db`.

### Warum SQLite statt PostgreSQL?

Während der Simulation werden tausende Schreib-Operationen pro Sekunde durchgeführt (Posts erstellen, Likes vergeben, Follows eintragen). SQLite ist dafür 10-100x schneller als PostgreSQL, weil:
- Keine Netzwerk-Verbindung nötig (Datei liegt lokal)
- Kein Overhead für Transaktions-Management über Netzwerk
- Perfekte Isolation: Simulationen beeinflussen sich nicht gegenseitig

Nach Abschluss der Simulation werden die Ergebnisse in PostgreSQL (Supabase) kopiert, wo sie dauerhaft gespeichert und über das Dashboard abrufbar sind.

### Die 9 Tabellen

| Tabelle | Inhalt | Beispiel |
|---------|--------|---------|
| `users` | Alle simulierten Personas | ID, Name, Persona-JSON, State-JSON |
| `posts` | Erstellte Posts | Autor, Inhalt, Hashtags, Likes/Comments/Reposts-Zähler |
| `comments` | Kommentare auf Posts | Post-ID, Autor, Inhalt, optional: Parent-Comment für Threads |
| `likes` | Likes/Reaktionen | Post-ID, User-ID, Reaktionstyp (Like/Celebrate/etc.), UNIQUE constraint |
| `follows` | Follow-Beziehungen | Follower → Followed, UNIQUE constraint |
| `reposts` | Geteilte Posts | Post-ID, User-ID |
| `action_log` | Audit-Trail aller Aktionen | Runde, Agent, Aktion, Inhalt, Ziel — jede Aktion wird protokolliert |
| `round_metrics` | Metriken pro Runde | JSON mit Sentiment, Engagement, Kosten |
| `checkpoints` | Simulation-Zustand für Recovery | JSON mit komplettem State, für Resume nach Crash |

### Performance-Optimierungen

- **WAL Mode** (Write-Ahead Logging): Erlaubt gleichzeitiges Lesen und Schreiben. Ohne WAL würde die DB bei jedem Schreiben für Leser blockiert.
- **Cache 64MB:** SQLite hält 64MB Daten im RAM statt ständig von Disk zu lesen.
- **Busy Timeout 5s:** Statt sofort mit Fehler abzubrechen wenn die DB kurz blockiert ist, wartet sie 5 Sekunden.
- **Batch Inserts:** `executemany()` statt einzelner `execute()` — 100x schneller für viele Einträge.

### Wie die CRUD-Operationen funktionieren

Jede Methode öffnet eine Verbindung, führt die Operation aus, committed, und schliesst. Beispiel `insert_like`:
1. Öffne Verbindung
2. `INSERT OR IGNORE` — wenn der Like schon existiert, wird er ignoriert (kein Fehler)
3. `UPDATE posts SET likes = likes + 1` — Zähler auf dem Post incrementieren
4. Commit + Schliessen

Das "OR IGNORE" Pattern verhindert Crashes wenn ein Agent versehentlich denselben Post zweimal liked.

---

## Schritt 3: Social Graph (networkx)

**Datei:** `backend/app/simulation/graph.py`
**Tests:** 14

### Was wurde gebaut?

Das virtuelle Beziehungsnetzwerk zwischen allen Agents — wer folgt wem, wer ist mit wem verbunden.

### Warum networkx?

networkx ist die Standard-Bibliothek für Netzwerkanalyse in Python. Sie bietet Directed Graphs (für Twitter: A folgt B heisst nicht B folgt A) und Undirected Graphs (für LinkedIn: Connection ist gegenseitig).

### Wie wird der Graph generiert?

Die Generierung passiert in 4 Phasen:

**Phase 1: Nodes anlegen**
Jeder Agent wird als Node im Graph registriert, mit seiner Community (= Stakeholder-Rolle) als Label.

**Phase 2: Intra-Community Edges (dichte Cluster)**
Agents innerhalb derselben Stakeholder-Gruppe (z.B. alle Mitarbeiter) werden stark vernetzt — jeder verbindet sich mit 15-35% seiner Gruppe. Das bildet die Realität ab: Mitarbeiter kennen sich untereinander, Journalisten kennen sich untereinander.

**Phase 3: Inter-Community Edges (Brücken)**
~5-10% der Verbindungen gehen ZWISCHEN Communities. Das sind die "Granovetter Weak Ties" — schwache Verbindungen die aber extrem wichtig sind, weil sie Informationen von einer Gruppe in eine andere tragen. Ein Journalist der mit Mitarbeitern verbunden ist, kann ein internes Thema in die Öffentlichkeit tragen.

**Phase 4: Influencer Hubs**
Power Creators (die 10% Vielschreiber) bekommen 2-3x mehr Verbindungen als normale Agents, auch cross-community. Auf echtem Twitter haben Influencer tausende Follower — wir bilden das skaliert ab.

### Plattform-Unterschiede

| | Öffentliches Netzwerk | Professionelles Netzwerk |
|---|---|---|
| Graph-Typ | Directed (A folgt B ≠ B folgt A) | Undirected (Connection = gegenseitig) |
| Community-Stärke | Stark (mu=0.15) | Schwächer (mu=0.25, mehr Cross-Community) |
| Degree-Exponent | 2.1 (extremere Power-Law) | 2.7 (weniger extrem) |

### Determinismus

Gleicher `seed` → gleicher Graph. Das ist wichtig für:
- Reproduzierbare Tests
- Vergleichbarkeit: Wenn du zwei Szenarien vergleichen willst, haben die Agents das gleiche Netzwerk

---

## Schritt 4: LLM Adapter

**Datei:** `backend/app/llm/base.py`, `openai.py`
**Tests:** 10

### Was wurde gebaut?

Eine abstrakte Schnittstelle für KI-Modell-Aufrufe, plus eine konkrete OpenAI-Implementierung.

### Das Adapter-Pattern (Provider-Agnostisch)

`LLMProvider` ist eine abstrakte Klasse mit zwei Methoden:
- `chat(messages, tools, temperature, max_tokens)` → `LLMResponse`
- `generate_simple(prompt, temperature)` → `str`

Jeder KI-Anbieter (OpenAI, Anthropic, Google) muss nur diese zwei Methoden implementieren. Der Rest der Anwendung ruft immer nur `LLMProvider` auf — er weiss nicht und muss nicht wissen ob dahinter OpenAI oder ein anderer Anbieter steht.

**Warum das wichtig ist:** Morgen könnte Anthropic Claude günstiger sein. Dann implementieren wir eine `ClaudeProvider`-Klasse, ändern eine Zeile Konfiguration, und die gesamte Simulation läuft auf Claude. Ohne das Adapter-Pattern müssten wir hunderte Code-Stellen ändern.

### OpenAI Implementation

Die `OpenAIProvider`-Klasse:
- **Async Client:** Alle Aufrufe sind nicht-blockierend. Während ein Agent auf seine LLM-Antwort wartet, können andere Agents gleichzeitig ihre Anfragen senden.
- **Function Calling:** Statt Freitext liefert das LLM strukturierte Aktionen zurück. Wir definieren "Tools" (Funktionen) die das LLM aufrufen kann — z.B. `create_post(content="...")` oder `like_post(post_id="...")`.
- **Prompt Caching:** OpenAI cached automatisch wiederkehrende Prompt-Prefixe (>1024 Tokens). Unsere Persona-Beschreibung ist bei jedem Aufruf eines Agents gleich → ~50% Rabatt auf diese Tokens.

### Retry-Strategie

LLM-API-Aufrufe können fehlschlagen (Netzwerk-Timeout, Rate-Limit, Server-Fehler). Unsere Strategie:

```
Versuch 1: Normaler Aufruf
Versuch 2: 1-2 Sekunden warten, nochmal
Versuch 3: 2-4 Sekunden warten
Versuch 4: 4-8 Sekunden warten
Versuch 5: 8-16 Sekunden warten
→ Danach: Fehler werfen
```

Das "Full Jitter" bedeutet: Die Wartezeit ist nicht exakt 2s, sondern irgendwo zwischen 0 und 2s. Das verhindert das "Thundering Herd" Problem — wenn 100 Agents gleichzeitig ein Rate-Limit bekommen und alle exakt nach 2s gleichzeitig nochmal anfragen.

### Kosten-Tracking

`LLMUsageTracker` zählt jeden Aufruf:
- Input Tokens (was wir an das LLM senden)
- Output Tokens (was das LLM antwortet)
- Cached Tokens (von den Input-Tokens, die aus dem Cache kamen)
- Berechnet Kosten in USD basierend auf dem Modell-Pricing

Beispiel: GPT-4o-mini kostet $0.15 pro Million Input-Tokens und $0.60 pro Million Output-Tokens. Gecachte Tokens kosten nur $0.075 (50% Rabatt).

---

## Schritt 5: Willingness Scoring

**Datei:** `backend/app/simulation/willingness.py`
**Tests:** 10

### Was wurde gebaut?

Das System das bestimmt WELCHE Agents in jeder Runde aktiv werden. Nicht alle 10'000 Agents posten jede Runde.

### Die Formel (Socialtrait-inspiriert)

```
s_unified = s_persona × exp(-λ × (s_context - s_persona))
```

Das klingt kompliziert, ist aber elegant:

**s_persona** (0-1): Wie aktiv ist diese Person grundsätzlich?
- 30% Extraversion (extrovertierte posten mehr)
- 25% Tier-Bonus (Creator=0.8, Observer=0.03)
- 20% Posting-Frequenz (täglich=0.9, selten=0.05)
- 15% Meinungsstärke (starke Meinungen → mehr Engagement)
- 10% Neurotizismus (emotionale Personen reagieren stärker)

**s_context** (0-1): Wie relevant ist die aktuelle Runde?
- 30% Themen-Relevanz (betrifft das Thema die Interessen des Agents?)
- 25% Netzwerk-Aktivität (hat jemand den der Agent folgt gerade gepostet?)
- 20% Emotionale Valenz (ist das Thema gerade kontrovers?)
- 15% Konversations-Momentum (wie aktiv war die letzte Runde?)
- 10% Zufall (Randomness für Variation)

**Die Exponentialfunktion** hat eine elegante Eigenschaft: Wenn der Kontext-Score höher ist als der Persona-Score (s_context > s_persona), wird das Ergebnis GEDÄMPFT. Das verhindert unrealistisches Verhalten — ein introvertierter Observer wird nicht plötzlich zum Vielschreiber nur weil das Thema kontrovers ist. Die Formel zieht ihn zu seiner "natürlichen Rate" zurück.

### Szenario-basierte Skalierung

Der `activation_scale` Multiplikator:
- Routine (z.B. Thought-Leadership): ×0.6 → nur ~20-30% aktiv
- Standard (z.B. Produktlaunch): ×1.0 → ~40-50% aktiv
- Krise (z.B. Entlassungen): ×1.5 → ~70-80% aktiv

### Cooldown-System

Nach einer Aktion muss ein Agent N Runden pausieren:
- Power Creator: 2 Runden (kann fast jede Runde posten)
- Active Responder: 3 Runden
- Selective Engager: 5 Runden
- Observer: 12 Runden (postet sehr selten)

### Performance

Alles ist als numpy-Array implementiert — keine Python-Schleifen. Die Berechnung für 50'000 Agents dauert <5ms. Das ist möglich weil numpy Operationen auf Arrays gleichzeitig (vektorisiert) ausführt, statt jeden Agent einzeln zu berechnen.

Die finale Aktivierung ist **stochastisch** (Bernoulli-Sampling): Der Score wird als Wahrscheinlichkeit interpretiert. Ein Agent mit Score 0.7 hat eine 70% Chance aktiv zu werden. Das erzeugt natürliche Variation.

---

## Schritt 6: Plattform-Modul (Öffentliches Netzwerk)

**Datei:** `backend/app/simulation/platforms/base.py`, `public.py`
**Tests:** 13

### Was wurde gebaut?

Ein austauschbares Modul das eine Twitter-ähnliche Plattform simuliert. Hinter einem abstrakten Interface, damit später LinkedIn als zweites Modul eingesteckt werden kann.

### Das Interface (base.py)

`PlatformBase` definiert was jede Plattform können muss:
- `get_action_types()` → welche Aktionen gibt es?
- `get_tools_schema()` → OpenAI Function-Calling Tools
- `generate_feed(agent_id, persona, round, feed_size)` → personalisierter Feed
- `format_feed_for_prompt(feed, round)` → Feed als Text für den LLM-Prompt
- `execute_action(action)` → Aktion in der DB ausführen
- `get_platform_rules_prompt()` → Regeln für den System-Prompt

### Feed-Algorithmus (Twitter-basiert)

Der Feed bestimmt welche Posts ein Agent in jeder Runde sieht. Basiert auf den echten Twitter-Gewichten (die Twitter 2023 open-sourced hat):

**Scoring-Formel:**
```
Score = log(1 + Engagement) × Recency × Proximity × Topic × Penalties
```

- **Engagement:** Like=1×, Retweet=20×, Reply=13.5×, Bookmark=10× (logarithmisch gedämpft, damit ein Post mit 1000 Likes nicht 1000× mehr Score bekommt als einer mit 1 Like)
- **Recency:** Halbwertszeit von 3 Runden. Ein Post verliert nach 3 Runden die Hälfte seines Scores. Nach 6 Runden nur noch 25%.
- **Social Proximity:** Direct Follow=1.0, Same Community=0.3, Kein Bezug=0.1.
- **Topic Relevance:** Hashtag-Overlap zwischen Agent-Interessen und Post-Hashtags.
- **Link Penalty:** Posts mit externen Links bekommen nur 0.4× Score (wie bei echtem Twitter).

**Feed-Assembly:** 85% relevanteste Posts + 15% Serendipity. Die 15% kommen aus anderen Communities als der des Agents — das verhindert Echo-Kammern.

### Feed-zu-Prompt Serialisierung

Der Feed wird in ein kompaktes Textformat umgewandelt (~200 Tokens für 5 Posts):

```
DEIN FEED:
[p-abc123] @agent-001 (vor 2 Runden): "Die Entlassungen sind..." | 12L 3K 1R #SwissBank
[p-def456] @agent-007 (vor 1 Runde): "Employer Branding wird..." | 5L 1K 0R
```

Jede Zeile enthält: Post-ID (damit der Agent darauf reagieren kann), Autor, Alter, Inhalt (gekürzt), Engagement-Zahlen (Likes, Kommentare, Reposts).

### Action Execution

Wenn das LLM entscheidet "Agent erstellt einen Post", passiert:
1. Neue UUID generieren (z.B. `p-3f8a92b1`)
2. Post in `posts`-Tabelle einfügen (Autor, Inhalt, Hashtags, Runde)
3. Aktion in `action_log` protokollieren (Audit Trail)
4. Wenn Follow: auch den Social Graph aktualisieren

---

## Schritt 7: Agent Memory System

**Datei:** `backend/app/simulation/memory.py`
**Tests:** 18

### Was wurde gebaut?

Ein Gedächtnis-System damit Agents sich über Runden hinweg erinnern. Ohne Memory würde ein Agent in Runde 20 vergessen dass er in Runde 5 einen kontroversen Post geschrieben hat.

### Drei Ebenen von Erinnerung

**1. Sliding Window (letzte 5 Beobachtungen)**
Immer verfügbar im Prompt. Alte Beobachtungen fallen raus wenn neue dazukommen. Beispiel: "Runde 5: Sah 3 negative Posts über Entlassungen", "Runde 6: Eigener Post bekam 12 Likes".

**2. Wichtige Erinnerungen (max 5)**
Nur Beobachtungen mit Importance-Score ≥ 5.0 werden hier gespeichert. "Mein Post ging viral mit 50 Likes" (Score: 7.0) wird behalten, "Scrollte durch den Feed" (Score: 0.0) nicht.

**3. Periodische Zusammenfassung**
Alle 5 Runden fasst das LLM alle Erinnerungen in 2-3 Sätze zusammen. Das spart Tokens — statt 20 einzelne Beobachtungen im Prompt zu haben, gibt es eine kompakte Zusammenfassung + die letzten 3 aktuellen.

### Importance Scoring (Heuristik)

| Aktion | Basis-Score | + Hohes Engagement | + Kontrovers |
|--------|------------|-------------------|-------------|
| Post erstellen | 4.0 | +3.0 (>10 Likes) | +2.0 |
| Kommentieren | 3.0 | +2.0 | +2.0 |
| Liken | 1.0 | — | — |
| Nichts tun | 0.0 | — | — |

Maximum: 10.0. Nur Scores ≥ 5.0 werden als "wichtig" gespeichert.

### Token-Budget

| Prompt-Abschnitt | Tokens | Cacheable? |
|------------------|--------|-----------|
| Zusammenfassung | ~60 | Nein |
| 3 wichtige Erinnerungen | ~45 | Nein |
| 3 aktuelle Beobachtungen | ~45 | Nein |
| **Total Memory** | **~150** | **Nein** |

---

## Schritt 8: Simulation Engine (Hauptschleife)

**Datei:** `backend/app/simulation/engine.py`
**Tests:** 7 (Mock) + 1 Live-Test mit GPT-4o-mini

### Was wurde gebaut?

Das Herzstück — die Hauptschleife die alle bisherigen Module zusammenführt und eine komplette Simulation orchestriert.

### Der Rundenablauf (6 Phasen)

**Phase 1: AKTIVIERUNG (<5ms)**
WillingnessScorer berechnet welche Agents aktiv sind. Ergebnis: Boolean-Array (True/False pro Agent).

**Phase 2: FEED GENERATION**
Für jeden aktiven Agent wird ein personalisierter Feed generiert (3-5 Posts).

**Phase 3: LLM DECISION (Bottleneck)**
Hier passiert die eigentliche KI-Arbeit. Drei verschiedene Verarbeitungswege je nach Tier:

- **Tier 1 (Power Creator + Active Responder):** Voller LLM-Call. System-Prompt mit kompletter Persona-Beschreibung + User-Prompt mit Memory + Feed + "Was willst du tun?". Das LLM antwortet mit einem Function-Call (z.B. `create_post(content="...")` oder `like_post(post_id="...")`).

- **Tier 2 (Selective Engager):** Vereinfachter LLM-Call. Kürzerer Prompt, nur 3 Posts im Feed, eingeschränkte Aktionen (Like, Comment, oder Nichts). Spart ~40% Tokens.

- **Tier 3 (Observer):** KEIN LLM-Call. Einfache Regel: "Like einen Post wenn das Sentiment zum Agent passt". Spart 100% der LLM-Kosten für diesen Agent.

**Phase 4: ACTION EXECUTION**
Jede Aktion wird auf der Plattform ausgeführt (DB-Updates, Graph-Updates).

**Phase 5: METRICS**
Zählen: Posts, Kommentare, Likes, Reposts, Follows pro Runde. Sentiment-Aggregation.

**Phase 6: EVENT EMISSION**
Sende `round_complete` Event an den WebSocket (für Live-View).

### Parallel Processing

Alle aktiven Agents werden gleichzeitig (parallel) verarbeitet, nicht nacheinander. Das funktioniert über Python's `asyncio`:
- Ein `Semaphore` limitiert die Anzahl gleichzeitiger LLM-Calls (default: 30)
- `asyncio.gather()` startet alle Agent-Tasks parallel
- Wenn ein Agent-Task fehlschlägt, wird er zu "do_nothing" degradiert — die Simulation läuft weiter

### Error Recovery

```
Agent-Fehler → Agent wird zum Observer degradiert → Simulation läuft weiter
>15% Agents fehlgeschlagen → Simulation pausiert
LLM gibt ungültigen Output → Pydantic-Validation → Fallback zu "do_nothing"
```

Die Simulation crasht NIE wegen eines einzelnen Agents.

### Der Live-Test

10 Agents, 5 Runden, Krisen-Szenario "SwissBank Entlassungen":
- **$0.0021** Kosten (2 Zehntel Cent)
- **17.8 Sekunden** Laufzeit
- 3 Posts erstellt, Likes und Kommentare generiert
- Runde 1: 7 aktive Agents, 3 Posts
- Runden 2-5: 3-5 aktive Agents, hauptsächlich Likes/Kommentare

---

## Schritt 9: Quality Metrics & Badge System

**Datei:** `backend/app/simulation/metrics.py`
**Tests:** 18

### Was wurde gebaut?

Automatische Qualitätsmessung für jede Simulation. Statt "95% Accuracy" zu behaupten (wie Wettbewerber), messen wir transparent und zeigen dem Kunden eine Qualitäts-Ampel.

### Die 3 Metriken

**1. Shannon-Entropie (Meinungsdiversität)**

Misst ob die Meinungen in der Simulation divers sind. Wir teilen alle Sentiments in 3 Bins (negativ/neutral/positiv) und berechnen die Informations-Entropie.

- 1.0 = Perfekte Gleichverteilung (je 33% negativ/neutral/positiv)
- 0.0 = Alle gleicher Meinung (Mode Collapse)
- Gesund: 0.5-0.8

Wenn die Entropie unter 0.3 fällt, ist etwas schiefgelaufen — die Agents haben sich zu schnell einander angeglichen (das Sycophancy-Problem von LLMs).

**2. Gini-Koeffizient (Engagement-Verteilung)**

Misst ob das Engagement realistisch verteilt ist. In echten Social Media bekommen wenige Posts viele Likes (Power-Law).

- 0.0 = Alle Posts gleich viel Engagement (unrealistisch)
- 1.0 = Ein Post hat alles (zu extrem)
- Gesund: 0.5-0.8

**3. Content Uniqueness (Trigram-Ratio)**

Misst ob die Posts sich inhaltlich unterscheiden. Wir zählen wie viele 3-Wort-Kombinationen ("Trigrame") unique sind.

- 1.0 = Alle Posts komplett verschieden
- 0.0 = Alle Posts identisch
- Gesund: >0.6

### Quality Badge

| Badge | Bedingung | Bedeutung |
|-------|-----------|-----------|
| GRÜN | Alle Metriken im gesunden Bereich | "Hohe Simulationsqualität" |
| GELB | 1-2 Metriken im Warnbereich | "Simulation nutzbar, eingeschränkte Diversität" |
| ROT | Mindestens eine Metrik kritisch | "Simulation möglicherweise unzuverlässig" |

---

## Schritt 10: Circuit Breaker & Health Monitoring

**Datei:** `backend/app/simulation/resilience.py`
**Tests:** 10

### Was wurde gebaut?

Ein Überwachungssystem das die Simulation vor totalem Ausfall schützt.

### Drei Schutzmechanismen

**1. Agent-Failure-Tracking**
Jeder fehlgeschlagene Agent wird registriert. Wenn derselbe Agent mehrfach fehlschlägt, wird er nur einmal gezählt (weil er sowieso schon degradiert ist).

**2. Circuit Breaker (15%-Schwelle)**
Wenn mehr als 15% aller Agents in einer Runde fehlschlagen, wird die Simulation PAUSIERT (nicht gecrasht). Das deutet auf ein systematisches Problem hin (z.B. OpenAI API ist down).

**3. Budget-Safety**
Optional kann ein maximales Budget pro Simulation gesetzt werden. Wenn die LLM-Kosten das Limit überschreiten, wird die Simulation sauber beendet — nicht mitten in einer Runde abgebrochen.

### Consecutive Error Detection

50 aufeinanderfolgende Fehler → Concurrency automatisch reduzieren (SLOW_DOWN). Das passiert z.B. wenn OpenAI Rate-Limits schickt — dann verlangsamen wir statt zu crashen.

---

## Schritt 11: Checkpoint & Recovery

**Datei:** `backend/app/simulation/checkpoint.py`
**Tests:** 6

### Was wurde gebaut?

Ein Speicherpunkt-System. Alle 5 Runden wird der komplette Zustand der Simulation gespeichert. Bei Crash kann die Simulation ab dem letzten Checkpoint fortgesetzt werden.

### Was wird gespeichert?

- Agent States (Memory, Sentiment, Cooldowns) für JEDEN Agent
- Last-Active-Rounds Array
- Bisherige Kosten und Token-Verbrauch
- Timestamp

### Speicher-Management

Nur die letzten 3 Checkpoints werden behalten. Ältere werden gelöscht. Bei einer 50-Runden-Simulation gibt es Checkpoints bei Runde 5, 10, 15, 20, 25, 30, 35, 40, 45, 50 — aber immer nur die letzten 3 (z.B. 40, 45, 50) existieren gleichzeitig.

### Resume-Logik

```
Start → Gibt es einen Checkpoint?
  → Nein: Starte von Runde 1
  → Ja: Lade Checkpoint, stelle Agent-States wieder her, starte ab nächster Runde
```

---

## Schritt 12: Integration Test

### Was wurde gemacht?

Alle bisherigen Tests nochmal zusammen laufen lassen:

```
136 Tests, ALLE GRÜN
0 Lint-Fehler
Live-Test mit echtem GPT-4o-mini bestanden
```

Dann: Feature-Branch in main gemergt.

### Test-Übersicht

| Test-Datei | Modul | Anzahl Tests |
|-----------|-------|-------------|
| test_models.py | Datenmodelle | 18 |
| test_database.py | SQLite CRUD | 11 |
| test_graph.py | Social Graph | 14 |
| test_llm.py | LLM Adapter | 10 |
| test_willingness.py | Willingness Scoring | 10 |
| test_platform_public.py | Public Network | 13 |
| test_memory.py | Agent Memory | 18 |
| test_engine.py | Simulation Loop | 7 |
| test_metrics.py | Quality Metrics | 18 |
| test_resilience.py | Circuit Breaker | 10 |
| test_checkpoint.py | Checkpoint/Recovery | 6 |
| test_health.py | API Health Check | 1 |
| **Total** | | **136** |

---

## Zusammenfassung: Der Datenfluss

```
Kunde gibt Szenario ein
       ↓
[Prompt Builder analysiert → Strukturiert → Bestätigung]    ← Issue #6
       ↓
[Persona Generator erzeugt 500 Basis-Personas]              ← Issue #5
       ↓
[Parametrische Variation → 1k-50k Agents]
       ↓
[Social Graph generiert (Communities + Hubs + Bridges)]      ← Schritt 3
       ↓
[SQLite DB initialisiert, Agents eingefügt]                  ← Schritt 2
       ↓
┌─────── SIMULATIONS-LOOP (50 Runden) ──────────┐
│                                                 │
│  1. Willingness Scoring (wer ist aktiv?)        │ ← Schritt 5
│  2. Feed generieren (was sieht jeder?)          │ ← Schritt 6
│  3. LLM entscheidet (was tut jeder?)            │ ← Schritt 4 + 8
│  4. Actions ausführen (DB + Graph updates)       │ ← Schritt 6
│  5. Memory updaten (Erinnerungen speichern)      │ ← Schritt 7
│  6. Metrics sammeln + Event emittieren           │ ← Schritt 9
│  7. Optional: Checkpoint speichern               │ ← Schritt 11
│  8. Health Check (Circuit Breaker)               │ ← Schritt 10
│                                                 │
└────────────────────────────────────────────────┘
       ↓
[Quality Metrics berechnen → Badge]                          ← Schritt 9
       ↓
[Ergebnisse in PostgreSQL persistieren]
       ↓
[Report generieren + PDF]                                    ← Issue #9
       ↓
Kunde sieht Dashboard + kann PDF exportieren
```

---

## Issue #5: Persona Generator

**Datei:** `backend/app/simulation/personas.py`
**Tests:** 14

### Was wurde gebaut?

Das Modul das hunderte realistische, DACH-kalibrierte Personas erzeugt — die "Schauspieler" der Simulation.

### Die Pipeline (5 Phasen)

**Phase 1: Stakeholder-Mix bestimmen**

Je nach Szenario-Typ wird automatisch festgelegt welche Stakeholder-Gruppen in welchem Verhältnis vertreten sind. Vordefinierte Templates:

- **Unternehmenskrise:** 15% Mitarbeiter, 25% Kunden, 5% Medien, 35% Öffentlichkeit, etc.
- **Produktlaunch:** 35% Zielkunden, 20% Bestandskunden, 10% Influencer, etc.
- **Employer Branding:** 25% Mitarbeiter, 20% Jobsuchende, 10% HR-Profis, etc.

Das Template bestimmt z.B. bei 500 Personas: 75 Mitarbeiter, 125 Kunden, 25 Medien, usw.

**Phase 2: Batch-Generierung via LLM**

Die Personas werden in Batches von je 10 via GPT-4o-mini generiert. Der Prompt enthält:
- Die Stakeholder-Rolle für diesen Batch
- Das Szenario als Kontext
- Namen der letzten 5 bereits generierten Personas (damit keine Duplikate entstehen)
- Anweisung für DACH-spezifische Namen und kulturelle Vielfalt

Jede Persona kommt als JSON mit ~20 Feldern zurück: Name, Alter, Geschlecht, Land, Region, Beruf, Branche, Big Five, Posting-Stil, Meinungen, Interessen, Bio.

**Kosten:** ~50 Batches × ~2000 Tokens = ~$0.07 für 500 Personas.

**Phase 3: Tier-Zuweisung**

Basierend auf der Kontroversität des Szenarios werden die Tiers zugewiesen:
- Krise: 10% Power Creator, 40% Active Responder, 30% Selective Engager, 20% Observer
- Standard: 5/25/20/50
- Routine: 3/12/15/70

Die Zuweisung ist randomisiert — nicht alle Mitarbeiter werden automatisch Power Creator.

**Phase 4: Spezial-Flags**

7% der Personas werden als "Zealots" markiert (Meinung ändert sich nie), 5% als "Contrarians" (widersprechen der Mehrheit). Diese Flags werden zufällig verteilt, mit der Einschränkung dass keine Persona beides gleichzeitig sein kann.

**Phase 5: Skalierung via Parametrische Variation**

Wenn mehr als 500 Personas gebraucht werden, werden Varianten erstellt:
- Alter: ±5 Jahre
- Big Five: Gaussches Rauschen mit std=0.08
- Meinungen: Gaussches Rauschen mit std=0.10
- 20% Chance: Posting-Frequenz ändert sich
- 15% Chance: Tonalität ändert sich
- Name bleibt gleich (Varianten sind "ähnliche Personen"), aber ID ist einzigartig

So werden aus 500 Basis-Personas z.B. 10'000 oder 50'000 — ohne zusätzliche LLM-Kosten.

### Fallback ohne LLM

Wenn ein LLM-Batch fehlschlägt (API-Error, Rate Limit), werden Fallback-Personas generiert:
- Zufälliges Land (DE/CH/AT) + Region
- Alter nach DACH-Altersverteilung
- Big Five nach realistischer Normalverteilung (basierend auf Forschung)
- Generischer Name ("Agent abc123")

Das verhindert dass die Persona-Generierung die ganze Simulation blockiert.

---

## Issue #6: Prompt Builder

**Datei:** `backend/app/services/prompt_builder.py`, `backend/app/api/simulation.py`
**Tests:** 11

### Was wurde gebaut?

Der "intelligente Eingabeassistent" der den Freitext des Kunden in eine strukturierte Simulation verwandelt.

### Wie es funktioniert

**Schritt 1: Freitext-Analyse**

Der Kunde gibt z.B. ein: *"SwissBank kündigt Entlassung von 200 Mitarbeitern an. Statement: Die Restrukturierung ist notwendig für die Zukunftsfähigkeit."*

Das LLM (GPT-4o-mini, Temperature 0.3 für konsistente Extraktion) analysiert den Text und gibt ein `StructuredScenario` JSON zurück:

```json
{
  "industry": "Finanzwesen",
  "company": "SwissBank",
  "target_audience": "Kunden und Mitarbeiter",
  "market": "CH",
  "statement": "Die Restrukturierung ist notwendig...",
  "scenario_type": "corporate_crisis",
  "controversity_score": 0.8,
  "missing_fields": ["Tonfall des Statements"],
  "suggestions": ["Definiere den gewünschten Tonfall"],
  "seed_posts": [
    "SwissBank: 'Die Restrukturierung ist notwendig...'",
    "@FinanzReporter: SwissBank streicht 200 Stellen.",
    "@BetroffeneMitarbeiterin: Gerade erfahren. Bin schockiert."
  ]
}
```

**Schritt 2: Lücken identifizieren**

Das LLM erkennt was fehlt — z.B. "Welcher Tonfall?", "Gibt es eine Vorgeschichte?", "Wer sind die Hauptkritiker?". Diese werden dem Kunden als Vorschläge angezeigt.

**Schritt 3: Seed-Posts generieren**

Das ist kritisch: Die Simulation braucht "Auslöser-Posts" damit die Agents etwas haben worauf sie reagieren. Das LLM generiert 2-3 realistische Posts:
1. Das offizielle Statement der Firma
2. Eine erste Medien-Reaktion
3. Eine erste persönliche Reaktion

Diese Seed-Posts werden als erste Posts in die Simulation injiziert (in Runde 0).

**Schritt 4: Kontroversitäts-Score**

Das LLM schätzt wie kontrovers das Szenario ist (0.0-1.0):
- 0.0-0.3 = Routine (Thought Leadership, normaler Content)
- 0.3-0.6 = Standard (Produktlaunch, moderate Ankündigung)
- 0.6-1.0 = Krise (Entlassungen, Skandal, politisch brisant)

Dieser Score bestimmt direkt die Tier-Verteilung der Personas und damit wie viele Agents aktiv sind.

### API-Endpoints

- `POST /api/simulation/analyze-input` — Freitext analysieren
- `POST /api/simulation/suggest-improvements` — Verbesserungsvorschläge generieren

Beide Endpoints sind geschützt (JWT-Auth required).

### Schwierigkeit beim Testen

Das Mock-LLM für Tests musste sorgfältig gebaut werden: Der ANALYSIS_PROMPT enthielt das Wort "fehlt noch", was den Mock dazu brachte den falschen Branch (Improvement statt Analysis) zu wählen. Fix: Mock prüft jetzt auf "Kommunikationsexperte" (unique zum Improvement-Prompt) statt auf generische Wörter.

---

## Issue #7: Background Jobs & Simulation Service

**Datei:** `backend/app/services/simulation_service.py`, `backend/app/api/simulation.py` (erweitert)
**Tests:** Keine eigenen (getestet via bestehende + API-Endpoints)

### Was wurde gebaut?

Der "Simulation Service" der alle bisherigen Module zu einem End-to-End-Flow verbindet, plus Background-Job-Ausführung.

### Der SimulationService

`run_simulation_job()` ist die Funktion die den kompletten Ablauf orchestriert:

1. **LLM Provider erstellen** (OpenAI mit API Key aus .env)
2. **Kontroversität bestimmen** (aus dem Prompt Builder Score)
3. **Personas generieren** (PersonaGenerator mit Stakeholder-Mix)
4. **SimulationConfig zusammenbauen** (Agent-Count, Runden, Plattform, etc.)
5. **Simulation starten** (create_and_run_simulation aus engine.py)
6. **Ergebnis zurückgeben**

### Background-Ausführung

Simulationen dauern Minuten bis Stunden — der API-Request kann nicht so lange offen bleiben. Lösung: FastAPI `BackgroundTasks`.

Ablauf:
1. User ruft `POST /api/simulation/start` auf
2. Server erstellt eine Simulation-ID und gibt sie sofort zurück
3. Die eigentliche Simulation läuft als Background-Task
4. User pollt `GET /api/simulation/status/{id}` für Updates

**Aktueller Stand:** In-Memory Job-Tracking (ein Dictionary). In Produktion wird das auf Supabase (PostgreSQL) migriert, damit Jobs Server-Neustarts überleben. Für den MVP reicht die In-Memory-Lösung.

### Neue API-Endpoints

- `POST /api/simulation/start` — Startet Simulation im Hintergrund
- `GET /api/simulation/status/{id}` — Status einer Simulation (pending/running/completed/failed)
- `GET /api/simulation/list` — Alle Simulationen des Users

Alle Endpoints prüfen die User-ID — ein User sieht nur seine eigenen Simulationen.

### Warum noch kein ARQ/Redis?

ARQ (die Redis-basierte Job Queue aus dem Bauplan) hätte eine Redis-Instanz erfordert. Für den MVP nutzen wir FastAPI's eingebaute BackgroundTasks — einfacher, keine zusätzliche Infrastruktur. ARQ wird für Produktion nachgerüstet wenn wir mehrere Worker und Job-Persistenz brauchen.
