# Swaarm — AI System Card

**Version:** 1.0
**Letzte Aktualisierung:** 2026-04-06
**Verantwortlicher:** Swaarm GmbH, Zürich, Schweiz

---

## 1. Systemzweck

Swaarm ist eine SaaS-Plattform zur Simulation öffentlicher Reaktionen auf Unternehmenskommunikation. Die Plattform verwendet KI-gesteuerte synthetische Personas, die auf simulierten Social-Media-Plattformen interagieren.

**Bestimmungsgemässer Gebrauch:**
- Pre-Testing von Kommunikationsstrategien, Krisenstatements, Kampagnen
- Vergleichende Szenario-Analyse (nicht quantitative Vorhersagen)
- Identifikation von Risiken und Narrativen

**Nicht bestimmungsgemässer Gebrauch (verboten laut AGB):**
- Entwicklung manipulativer Kommunikationsstrategien
- Social Scoring oder Bewertung echter Personen
- Nutzung zur gezielten Täuschung der Öffentlichkeit

---

## 2. EU AI Act Klassifizierung

**Risikoklasse:** Limited Risk (Art. 50 Transparenzpflichten)

**Begründung:**
- Kein High-Risk-Anwendungsfall gemäss Annex III
- Keine verbotene Praxis gemäss Art. 5 (keine Manipulation echter Personen, kein Social Scoring)
- Rein synthetische Personas ohne Bezug zu identifizierbaren natürlichen Personen

---

## 3. KI-Modelle

| Modell | Anbieter | Zweck | Version |
|--------|----------|-------|---------|
| GPT-4o-mini | OpenAI | Agent-Entscheidungen, Persona-Generierung, Report-Erstellung | Aktuell zum Zeitpunkt der Nutzung |

**Provider-Agnostizität:** Das System ist so gebaut, dass der KI-Anbieter jederzeit gewechselt werden kann (Abstract Interface Pattern).

---

## 4. Datenquellen

| Datenquelle | Verwendung | Personenbezug |
|-------------|------------|---------------|
| User-Input (Szenario-Text) | Basis für Simulation | Möglicherweise (Firmennamen, öffentliche Personen) |
| BFS/Destatis Demografie-Daten | Persona-Kalibrierung | Nein (aggregierte Statistiken) |
| Sinus-Milieus | Persona-Verteilung | Nein (Modell, keine Individualdaten) |

**Keine verwendeten Datenquellen:**
- Keine echten Social-Media-Daten (kein Scraping, keine API-Zugriffe)
- Keine echten Personen-Profile
- Kein Fine-Tuning auf personenbezogenen Daten

---

## 5. Limitationen

- Simulationsergebnisse sind **vergleichende Szenario-Analysen**, keine statistischen Vorhersagen
- KI-generierte Inhalte können Verzerrungen der Trainings-Daten widerspiegeln
- Synthetische Personas bilden die reale Gesellschaft nur approximativ ab
- Quantitative Aussagen ("X% werden positiv reagieren") sind nicht zuverlässig
- Die Simulation ist DACH-optimiert; andere Märkte erfordern Anpassung

---

## 6. Transparenz-Massnahmen

- Alle simulierten Inhalte sind im UI als "KI-generiert" gekennzeichnet
- Synthetische Personas tragen den Hinweis "Fiktive Person"
- Reports enthalten den Vermerk "Erstellt durch KI-Simulation"
- Machine-readable Metadata in API-Responses und PDF-Exporten
- Quality Badge System (Grün/Gelb/Rot) zur Qualitäts-Transparenz

---

## 7. Menschliche Aufsicht

- Jede Simulation wird von einem menschlichen Nutzer initiiert und konfiguriert
- Simulationsergebnisse erfordern menschliche Interpretation
- Kein automatischer Export oder Veröffentlichung von Ergebnissen
- Reports dienen als Entscheidungsgrundlage, nicht als automatisierte Entscheidung
