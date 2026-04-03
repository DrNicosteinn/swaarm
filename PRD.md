# PRD: Swaarm — Pre-Testing Platform for Strategic Communications

## Problem Statement

PR-Agenturen, Corporate-Communications-Teams und Brand-Strategen im DACH-Raum stehen vor einem fundamentalen Problem: Sie entwickeln Kommunikationsstrategien, Krisenstatements und Kampagnen im Blindflug. Erst nach der Veröffentlichung erfahren sie, wie die Öffentlichkeit reagiert.

Die heutigen Alternativen sind unzureichend:
- **Traditionelle Marktforschung** (Fokusgruppen, Surveys) kostet CHF 20'000-65'000 pro Studie und dauert 4-6 Wochen
- **Social Listening Tools** (Brandwatch, Meltwater) analysieren nur was **bereits passiert** ist — sie sind retrospektiv, nicht prädiktiv
- **Bauchgefühl und Erfahrung** sind die Standardmethode — unzuverlässig, nicht skalierbar, nicht belegbar gegenüber Kunden
- **Enterprise-Simulationsplattformen** (Simile, Aaru) kosten $100'000+/Jahr und sind für den Mittelstand unzugänglich
- **Kein Tool weltweit** bietet KI-basierte Simulation auf professionellen Netzwerken (LinkedIn-ähnlich)

Eine missglückte Krisenkommunikation kostet Unternehmen durchschnittlich 15% ihres Börsenwerts. Ein einziger Shitstorm kann Millionen an Reputationsschaden verursachen. Es gibt keine bezahlbare Möglichkeit, Kommunikation vorher zu testen.

## Solution

**Swaarm** ist eine SaaS-Plattform, die mit tausenden KI-gesteuerten Agenten simuliert, wie die Öffentlichkeit auf Unternehmenskommunikation reagiert — bevor sie veröffentlicht wird.

Der Kunde gibt ein Statement, eine Kampagne oder eine Strategie ein. Swaarm erzeugt bis zu 50'000 realistische Personas (kalibriert auf den DACH-Markt) und lässt sie auf simulierten sozialen Netzwerken über 50-100 Runden miteinander interagieren. Das Ergebnis: ein detaillierter Report mit Sentiment-Verlauf, entstehenden Narrativen, Risiken und Empfehlungen.

**Zwei simulierte Plattformen:**
- **Öffentliches Netzwerk** (Twitter-ähnlich): Für Krisen, öffentliche Meinung, virale Dynamiken
- **Professionelles Netzwerk** (LinkedIn-ähnlich): Für B2B-Kommunikation, Employer Branding, Executive Positioning

**Kern-Use-Cases:**
1. Krisenkommunikation Pre-Testing (Shitstorm-Vorhersage)
2. M&A / IPO / Earnings-Announcement-Vorbereitung
3. Pharma / Regulierte-Industrie-Kommunikation
4. CEO / Executive Positioning auf professionellen Netzwerken
5. Employer Branding / Recruitment-Kampagnen
6. Brand Strategy / Content-Testing

Der Kunde kann die Simulation in Echtzeit beobachten — ein Live-Netzwerk-Graph zeigt wie sich Diskussionen, Cluster und Narrative organisch entwickeln.

## User Stories

### Onboarding & Account

1. Als neuer Nutzer möchte ich mich mit Email und Passwort registrieren, damit ich schnell Zugang zur Plattform bekomme
2. Als registrierter Nutzer möchte ich mich einloggen und mein Dashboard sehen, damit ich sofort mit meiner Arbeit beginnen kann
3. Als Nutzer möchte ich mein Abonnement (Starter/Professional/Enterprise) auswählen, damit ich das passende Kontingent für meine Bedürfnisse habe
4. Als Nutzer möchte ich meine Zahlungsdaten über Stripe hinterlegen, damit mein Abo automatisch abgerechnet wird
5. Als Nutzer möchte ich meinen aktuellen Verbrauch sehen (verbleibende Simulationen, genutzter Agent-Count), damit ich mein Budget planen kann

### Simulation erstellen (Prompt Builder)

6. Als PR-Berater möchte ich mein Szenario als Freitext eingeben, damit ich nicht durch starre Formulare eingeschränkt bin
7. Als Nutzer möchte ich, dass die KI meinen Freitext analysiert und strukturierte Felder extrahiert (Branche, Zielgruppe, Markt, Statement), damit ich sehe ob mein Input vollständig ist
8. Als Nutzer möchte ich Vorschläge erhalten was in meinem Prompt fehlt (z.B. Tonfall, Vorgeschichte, Hauptkritiker), damit die Simulation möglichst realistische Ergebnisse liefert
9. Als Nutzer möchte ich die extrahierten Felder korrigieren und ergänzen können, damit die Simulation genau meinem Szenario entspricht
10. Als Nutzer möchte ich den finalen strukturierten Prompt zur Bestätigung sehen, damit ich weiss was genau simuliert wird
11. Als Nutzer möchte ich wählen ob ich auf dem Öffentlichen Netzwerk, dem Professionellen Netzwerk oder beiden simulieren will, damit ich die richtige Plattform für meinen Use Case nutze
12. Als Nutzer möchte ich die Simulationsparameter anpassen können (Anzahl Agents, Anzahl Runden), damit ich Tiefe vs. Kosten/Geschwindigkeit abwägen kann

### Simulation beobachten (Live-View)

13. Als Nutzer möchte ich die laufende Simulation in Echtzeit beobachten, damit ich den Diskussionsverlauf live verfolgen kann
14. Als Nutzer möchte ich einen Netzwerk-Graph sehen der live wächst (Nodes = Agents, Edges = Interaktionen, Farbe = Sentiment), damit ich Cluster und Echo-Chambers visuell erkennen kann
15. Als Nutzer möchte ich einen Live-Feed sehen wo Posts und Kommentare in Echtzeit einlaufen, damit ich die Inhalte der Diskussion mitlesen kann
16. Als Nutzer möchte ich den aktuellen Fortschritt sehen (Runde X von Y, geschätzte Restzeit), damit ich weiss wann die Simulation fertig ist
17. Als Nutzer möchte ich die Simulation im Hintergrund laufen lassen und später zurückkehren, damit ich nicht die ganze Zeit zuschauen muss

### Report & Analyse

18. Als Nutzer möchte ich nach Abschluss der Simulation ein interaktives Dashboard mit den Ergebnissen sehen, damit ich die Resultate im Detail analysieren kann
19. Als Nutzer möchte ich den Sentiment-Verlauf über die Zeit als Chart sehen, damit ich erkenne wann und warum die Stimmung kippt
20. Als Nutzer möchte ich die Top-Narrative sehen die in der Simulation entstanden sind, damit ich weiss welche Themen die Diskussion dominieren
21. Als Nutzer möchte ich identifizierte Risiken und Warnungen sehen, damit ich kritische Punkte in meiner Kommunikation erkennen kann
22. Als Nutzer möchte ich die Engagement-Metriken sehen (Posts, Likes, Shares, Comments pro Runde), damit ich die Dynamik quantitativ bewerten kann
23. Als Nutzer möchte ich einen LLM-generierten Summary-Report lesen, damit ich die Ergebnisse schnell verstehen kann ohne alles selbst zu analysieren
24. Als Nutzer möchte ich den Report als PDF exportieren, damit ich ihn an Kunden oder Stakeholder weiterleiten kann
25. Als Nutzer möchte ich einzelne Agent-Posts und Kommentare durchsuchen und filtern, damit ich Details der Diskussion nachvollziehen kann

### Dashboard & History

26. Als Nutzer möchte ich alle meine bisherigen Simulationen auf dem Dashboard sehen, damit ich einen Überblick über meine Arbeit habe
27. Als Nutzer möchte ich den Status jeder Simulation sehen (laufend, abgeschlossen, fehlgeschlagen), damit ich den Fortschritt verfolgen kann
28. Als Nutzer möchte ich vergangene Simulationen erneut öffnen und die Reports ansehen, damit ich auf frühere Ergebnisse zurückgreifen kann
29. Als Nutzer möchte ich zwei Simulationen nebeneinander vergleichen, damit ich verschiedene Kommunikationsstrategien gegenüberstellen kann

### Landing Page & Marketing

30. Als Besucher möchte ich auf der Startseite verstehen was Swaarm macht, damit ich entscheiden kann ob es für mich relevant ist
31. Als Besucher möchte ich die Pricing-Tiers sehen, damit ich weiss was es kostet
32. Als Besucher möchte ich Use-Case-Beschreibungen sehen, damit ich verstehe wie Swaarm für meinen spezifischen Bedarf hilft
33. Als Besucher möchte ich mich direkt registrieren können, damit der Einstieg möglichst einfach ist

### Plattform-spezifisch: Öffentliches Netzwerk (Twitter-ähnlich)

34. Als Nutzer möchte ich Agenten sehen die Posts erstellen, liken, retweeten, kommentieren und sich gegenseitig folgen, damit die Simulation realistisches Twitter-Verhalten abbildet
35. Als Nutzer möchte ich sehen wie Hashtags und virale Posts entstehen, damit ich die Verbreitungsdynamik meiner Botschaft verstehe
36. Als Nutzer möchte ich verschiedene Agent-Typen sehen (Journalisten, Influencer, Konsumenten, Aktivisten, Trolle), damit die Simulation ein realistisches Ökosystem darstellt

### Plattform-spezifisch: Professionelles Netzwerk (LinkedIn-ähnlich)

37. Als Nutzer möchte ich Agenten mit professionellen Profilen sehen (Job-Titel, Unternehmen, Seniority, Branche), damit die LinkedIn-Simulation realistisch ist
38. Als Nutzer möchte ich sehen wie professionelle Diskussionen verlaufen (substantielle Kommentare, verschiedene Reaktionstypen wie Insightful/Celebrate/Like), damit ich die B2B-Dynamik verstehe
39. Als Nutzer möchte ich sehen wie Thought-Leadership-Posts sich im professionellen Netzwerk verbreiten, damit ich meine Content-Strategie optimieren kann
40. Als Nutzer möchte ich die Reaktionen verschiedener Stakeholder-Gruppen getrennt analysieren (C-Level, HR, Analysten, Mitarbeiter), damit ich zielgruppenspezifische Insights gewinne

### Billing & Subscription

41. Als Starter-Nutzer möchte ich bis zu 1'000 Agents und 5 Simulationen pro Monat nutzen, damit ich Swaarm kostengünstig kennenlernen kann
42. Als Professional-Nutzer möchte ich bis zu 10'000 Agents und 20 Simulationen pro Monat nutzen, damit ich ernsthafte Analysen durchführen kann
43. Als Enterprise-Nutzer möchte ich 50'000+ Agents und unbegrenzte Simulationen nutzen, damit ich auch grosse Ökosysteme simulieren kann
44. Als Nutzer möchte ich bei Überschreitung meines Kontingents einzelne Simulationen zusätzlich kaufen können (Pay-per-Simulation), damit ich flexibel bleibe
45. Als Nutzer möchte ich mein Abo jederzeit upgraden oder downgraden können, damit ich mein Paket an meinen Bedarf anpassen kann

## Implementation Decisions

### Architektur & Tech-Stack

- **Backend:** Python + FastAPI + Pydantic. FastAPI liefert REST-Endpoints und WebSocket-Support in einem Service
- **Frontend:** React + Vite + Tailwind CSS + shadcn/ui. Single-Page-Application, kein Next.js/SSR
- **Datenbank:** Supabase (PostgreSQL) für App-Daten (Users, Subscriptions, Simulation-Metadata, Reports). SQLite pro Simulation für Speed und Isolation während der Simulation
- **Auth:** Supabase Auth mit Email + Passwort
- **Billing:** Stripe (CHF, Subscriptions + Metered Billing für Pay-per-Simulation)
- **Deployment:** Railway (Backend + Redis + Worker) + Vercel (Frontend)
- **Monitoring:** Sentry (Error-Tracking) + Loguru (Logging) + LLM-Token-Usage-Tracking pro Simulation

### Simulation Engine (Custom, OASIS-inspiriert)

- Eigene Engine, inspiriert von OASIS (MIT-lizenziert), keine OASIS-Dependency
- Architektur auf 50'000+ Agents ausgelegt
- Agent State Management mit Pydantic Models (Persona, Memory, Beliefs)
- Social Graph via networkx (Follower/Connection-Beziehungen)
- Action System: LLM Function-Calling (GPT-4o-mini als Standard, provider-agnostisch)
- Async Execution: asyncio + Semaphore-basierte Concurrency für LLM-Calls
- Willingness Scoring: Eigenes Aktivierungsmodell (persona-basiert + Kontext-Relevanz + Random Noise) — bestimmt welche Agents pro Runde aktiv werden
- Persistent Agent Memory: Agents erinnern sich an vorherige Interaktionen
- Platform Abstraction Layer: Austauschbares Modul pro simulierter Plattform

### Plattform-Module

- **Öffentliches Netzwerk (Twitter-ähnlich):** 6 Action Types (CREATE_POST, LIKE, REPOST, COMMENT, FOLLOW, DO_NOTHING). Feed-Algorithmus basiert auf Follower-Graph + Engagement-Score + Recency
- **Professionelles Netzwerk (LinkedIn-ähnlich):** 15 Action Types (Post, Article, Newsletter, 6 Reaktionstypen, Comment, Reply, Share, Connect, Follow, Endorse, Do Nothing). Feed-Algorithmus 360Brew-inspiriert: Relevanz + Expertise + Dwell-Time, Comments wiegen 15x mehr als Reactions, keine Viralität (24-48h Distribution Window)
- Plattform-Interface abstrakt gehalten, damit neue Plattformen in 2-3 Tagen integrierbar sind

### Persona Generator

- ~500 LLM-generierte Basis-Personas pro Simulation (demografisch, psychografisch, beruflich)
- Parametrische Variation für Skalierung auf 1'000-50'000 Agents
- DACH-Kalibrierung via BFS (Schweiz), Destatis (Deutschland), LinkedIn Workforce Reports
- Persona-Attribute: Demografie, Big Five Persönlichkeit, Meinungen, Posting-Stil, Beruf/Seniority/Branche (LinkedIn)
- Prompt-Engineering only — kein Fine-Tuning, keine echten LinkedIn/Twitter-Daten nötig

### Input-Pipeline (Prompt Builder)

- User gibt Freitext ein
- LLM analysiert und extrahiert: Branche, Zielgruppe, Markt, Statement/Kampagne, Kontext
- LLM identifiziert Lücken und generiert Verbesserungsvorschläge
- User ergänzt/korrigiert interaktiv
- Finaler strukturierter Prompt zur Bestätigung
- Simulation startet nach Bestätigung

### Report Generator

- Aggregation der Simulationsdaten: Sentiment-Verlauf, Top-Narrative (Clustering), Engagement-Metriken, Risiko-Identifikation
- LLM-generierter Summary-Report (strukturiert: Executive Summary, Sentiment-Analyse, Narrative, Risiken, Empfehlungen)
- PDF-Export für Weitergabe an Kunden
- Ergebnisse werden in PostgreSQL persistiert für Dashboard-Zugriff und Vergleichsfunktionen

### Realtime Streaming

- FastAPI WebSocket-Server
- Pro Runde werden neue Events an das Frontend gepusht (Posts, Likes, Follows, Sentiment-Updates, Graph-Änderungen)
- Frontend rendert: D3.js Force-directed Graph (Nodes = Agents, Edges = Interaktionen, Farbe = Sentiment) + Live-Feed (Posts/Kommentare)

### Background Job Processing

- ARQ (async Redis queue) für Simulation-Jobs
- Simulation läuft als Background Worker, nicht im API-Request
- Status-Updates via WebSocket an Frontend

### Sprache & Lokalisierung

- App-UI auf Deutsch (DACH-first)
- i18n-ready bauen für spätere Expansion (Englisch, Französisch)
- Simulationsinhalte in der Sprache des User-Inputs

### Pricing-Tiers

| Tier | Preis | Agents | Simulationen/Monat |
|------|-------|--------|-------------------|
| Starter | CHF 199/Mo | 1'000 | 5 |
| Professional | CHF 999/Mo | 10'000 | 20 |
| Enterprise | CHF 2'999/Mo | 50'000+ | Unbegrenzt |
| Per-Simulation | CHF 2'000-15'000 | Custom | Einmalig |

## Testing Decisions

### Testing-Philosophie

Gute Tests verifizieren **externes Verhalten über öffentliche Schnittstellen**, nicht Implementierungsdetails. Tests sollen wie Spezifikationen des Systems lesbar sein. Sie dürfen bei internen Refactorings nicht brechen, solange das Verhalten gleich bleibt.

### Getestete Module

1. **Simulation Engine:** Testen ob eine Simulation mit gegebener Konfiguration korrekt durchläuft, die richtigen Aktionen produziert, Agents konsistentes Verhalten zeigen, und der Willingness Score die Aktivierung korrekt steuert. Interface: `run_simulation(config) -> SimulationResult`

2. **Persona Generator:** Testen ob die korrekte Anzahl Personas generiert wird, demografische Verteilungen den Vorgaben entsprechen, Basis-Personas und Variationen sich unterscheiden, und DACH-spezifische Attribute korrekt kalibriert sind. Interface: `generate_personas(scenario, count) -> List[Persona]`

3. **Prompt Builder:** Testen ob Freitext korrekt in strukturierte Felder extrahiert wird, fehlende Felder identifiziert werden, und Vorschläge sinnvoll sind. Interface: `analyze_input(raw_text) -> StructuredScenario`

4. **Report Generator:** Testen ob Simulationsdaten korrekt aggregiert werden, Sentiment-Verläufe korrekt berechnet werden, Narrative-Clustering funktioniert, und PDF-Export valide Dateien produziert. Interface: `generate_report(simulation_id) -> Report`

### Nicht getestet im MVP

- Frontend (manuelles Testing)
- Billing/Stripe-Integration (manuelles Testing + Stripe Test-Mode)
- Landing Page (visuelles Review)

## Out of Scope

Die folgenden Features sind explizit NICHT Teil des MVP:

- **Agent-Chat:** Nach der Simulation mit einzelnen Agenten chatten ("Warum hast du negativ reagiert?") — v2 Feature
- **A/B/C-Testing:** Mehrere Strategien parallel simulieren und automatisch vergleichen — v2 Feature (manueller Vergleich via Dashboard ist möglich)
- **Mid-Simulation Intervention:** Neue Variablen während der Simulation injizieren (z.B. zweites Statement nach Runde 25) — v2 Feature
- **Reddit/TikTok/Instagram-Simulation:** Weitere Plattformen — nach MVP
- **OAuth Login:** Google/Microsoft SSO — nach MVP
- **Waitlist/Invite-Only:** Kontrollierter Zugang — nach MVP
- **Multi-Language UI:** Englisch/Französisch — nach MVP (i18n-ready gebaut)
- **API für Drittanbieter:** Externe API für Integrationen — nach MVP
- **Custom Persona Packs:** Vorgefertigte branchenspezifische Personas (Pharma, Finance, etc.) — nach MVP
- **Premium-LLM-Upgrade:** Claude/GPT-4o statt GPT-4o-mini als Simulations-Modell — nach MVP

## Further Notes

### Positioning

Swaarm positioniert sich als "Pre-Testing Platform for Strategic Communications" — nicht als "Social Media Simulation Tool". Diese Positionierung erlaubt höhere Preispunkte und spricht direkt den Pain Point der Zielgruppe an.

### Wettbewerbsvorteil

- **Einziges Tool mit LinkedIn-ähnlicher Simulation** (kein Wettbewerber hat das)
- **Einziges Mid-Market-Tool mit echter Multi-Runden-Simulation** ($199-$2'999/Mo statt $100k+/Jahr)
- **DACH-spezifische Personas** (kein Wettbewerber hat das)
- **Live-Visualisierung** (kein vergleichbares Tool zeigt die Simulation in Echtzeit)

### Wichtige Limitationen (transparent kommunizieren)

- Simulationsergebnisse sind **vergleichende Szenario-Analysen**, keine statistischen Vorhersagen
- Outputs als "Strategie A erzeugt 3x mehr Engagement als B" positionieren, nicht als "34.7% werden positiv reagieren"
- Multiple Runs pro Szenario empfohlen für robustere Ergebnisse

### Regulatorisch

- EU AI Act: "Limited Risk" Kategorie — Transparenzpflichten ab August 2026
- Alle KI-generierten Inhalte müssen als solche gekennzeichnet werden
- Rein synthetische Personas — wahrscheinlich ausserhalb DSGVO-Scope
- Simulierte Plattformen heissen "Öffentliches Netzwerk" und "Professionelles Netzwerk" (keine Trademark-Issues)

### Kosten pro Simulation (geschätzt)

| Scale | LLM-Calls | Kosten (GPT-4o-mini) | Mit Caching |
|-------|-----------|---------------------|-------------|
| 1'000 Agents × 50 Runden | 50'000 | ~$10 | ~$4-6 |
| 10'000 Agents × 50 Runden | 500'000 | ~$97 | ~$40-58 |
| 50'000 Agents × 50 Runden | 2'500'000 | ~$487 | ~$195-290 |
