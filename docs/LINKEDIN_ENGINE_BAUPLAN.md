# Issue #11: LinkedIn Engine — Bauplan

## Kern-Erkenntnisse aus der Recherche

### 1. LinkedIn-Agents verhalten sich fundamental anders als Twitter-Agents
- **Selbstzensur:** Chef, Kunden, Recruiter sehen alles → viel vorsichtiger
- **do_nothing ist 80% der Zeit die klügste Aktion** (vs. ~60% bei Twitter)
- **Seniority bestimmt Verhalten:** C-Level postet strategisch, Junior vorsichtig, HR/Sales sehr aktiv
- **Längere Cooldowns:** Creator 3 Runden (vs. 2), Responder 5 (vs. 3), Observer 20 (vs. 12)

### 2. Feed funktioniert über 2nd-Degree Engagement
- Twitter: Du siehst Posts von Leuten denen du folgst
- **LinkedIn: Du siehst Posts mit denen deine Connections interagiert haben**
- 3-Stufen-Pipeline: Quality Filter → Early Test (12% Connections) → Expansion → Broad
- Dwell-Time ist stärkster Signal (nicht Likes)
- Comments zählen 4-8x mehr als Likes

### 3. 6 Reaktionstypen statt 1
- Like (Standard), Celebrate (Erfolge), Insightful (Fachlich), Support (Empathie), Love (Herz), Funny (selten professionell)
- Reaction-Wahl hängt von Content-Typ + Persona-Persönlichkeit ab

### 4. Bilaterale Connections ändern die Graph-Dynamik
- Undirected Graph (schon implementiert in SocialGraph)
- Höherer Clustering-Koeffizient (0.3-0.6 vs. 0.05-0.2 bei Twitter)
- Connection-Wahrscheinlichkeit basiert auf: Branche, Seniority, Stakeholder-Rolle, Region

## Dateien erstellen

| Datei | Was |
|-------|-----|
| `backend/app/simulation/platforms/professional.py` | ProfessionalNetworkPlatform (~400 Zeilen) |
| `backend/app/models/professional.py` | ProfessionalProfile Pydantic Model |
| `backend/tests/test_platform_professional.py` | Tests |

## Dateien modifizieren

| Datei | Änderung |
|-------|----------|
| `backend/app/models/persona.py` | `professional_profile: ProfessionalProfile \| None` hinzufügen |
| `backend/app/models/actions.py` | `reaction_type`, `via_connection_id` auf FeedItem |
| `backend/app/simulation/engine.py` | Platform-Factory statt hardcoded PublicNetwork |
| `backend/app/simulation/database.py` | `get_second_degree_posts()` Methode |
| `backend/app/simulation/graph.py` | `_connection_probability()` für professionelle Graphen |

## Dateien NICHT ändern

- `willingness.py` — bleibt platform-agnostisch (Tier-Config kommt von der Platform)
- `memory.py` — funktioniert für beide Plattformen
- `metrics.py` — funktioniert für beide
- `checkpoint.py`, `resilience.py` — platform-unabhängig

## Implementierungs-Schritte

### Schritt 1: ProfessionalProfile Model
- Neues Pydantic Model mit: job_title, company_name, company_size, seniority_level, expertise_topics, connection_count, compliance_awareness
- Optional auf Persona: `professional_profile: ProfessionalProfile | None = None`

### Schritt 2: FeedItem + AgentAction erweitern
- FeedItem: `reaction_type`, `via_connection_id`, `via_connection_name`, `content_type`
- AgentAction: `reaction_type` für LinkedIn-Reactions

### Schritt 3: Database erweitern
- `get_second_degree_posts(agent_id, connections, current_round)` — 2-Hop SQL Join
- `get_posts_by_connections(connection_ids, current_round)` — direkte Connection-Posts

### Schritt 4: Graph erweitern
- `_connection_probability(persona_a, persona_b)` — Wahrscheinlichkeit basierend auf Branche, Seniority, Region

### Schritt 5: ProfessionalNetworkPlatform
- 15 Action Types als OpenAI Function Calling Tools
- Feed: 60% direkte Connections + 30% 2nd-Degree Engagement + 10% Discovery
- Scoring: Engagement × Recency (half-life 5) × Proximity × Expertise-Alignment × Dwell-Prediction × Virality-Suppression × Format-Modifier
- execute_action für alle 15 Action Types
- Platform Rules Prompt (professioneller Ton, Chef liest mit)

### Schritt 6: Engine Platform-Factory
- `create_and_run_simulation()`: Platform basierend auf `config.platform` wählen

### Schritt 7: Tests
- Alle Action Types testen
- Feed mit 2nd-Degree Visibility testen
- Scoring-Formel testen
- Graph mit Connection-Probability testen

## Geschätzter Aufwand: ~2-3 Tage
