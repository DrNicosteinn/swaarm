# Swaarm Simulation Engine — Der Bauplan einfach erklärt

---

## Was bauen wir eigentlich?

Stell dir vor, du bist Kommunikationschefin einer grossen Schweizer Versicherung. Morgen müsst ihr 200 Stellen streichen und ein öffentliches Statement dazu veröffentlichen. Die Frage: **Wie wird die Öffentlichkeit reagieren?**

Heute hast du zwei Optionen: Bauchgefühl oder eine teure Marktforschungsstudie (CHF 20'000-65'000, 4-6 Wochen). Beides unbefriedigend.

**Swaarm gibt dir eine dritte Option:** Du gibst dein Statement in die Plattform ein, und innerhalb von Minuten simulieren tausende KI-gesteuerte "Personen" auf einem virtuellen Twitter und LinkedIn, wie sie darauf reagieren würden. Du siehst live, wie sich Diskussionen entwickeln, welche Narrative entstehen, wo Shitstorm-Risiken lauern — und bekommst am Ende einen detaillierten Report.

Das ist wie ein Flugsimulator für Unternehmenskommunikation.

---

## Die grosse Übersicht: Was passiert Schritt für Schritt?

Wenn ein Kunde Swaarm nutzt, durchläuft das System diese Pipeline:

```
SCHRITT 1: Input          → Kunde gibt Statement/Kampagne ein
SCHRITT 2: Verstehen      → KI analysiert den Input und fragt nach
SCHRITT 3: Personen       → System erzeugt tausende realistische Personas
SCHRITT 4: Netzwerk       → System vernetzt die Personas wie in echten Social Media
SCHRITT 5: Simulation     → Personas diskutieren über 50 Runden miteinander
SCHRITT 6: Live-Ansicht   → Kunde sieht die Diskussion in Echtzeit
SCHRITT 7: Report         → System analysiert alles und erstellt Bericht
```

Lass uns jeden Schritt im Detail anschauen.

---

## Schritt 1 & 2: Der Prompt Builder — Wie der Kunde seinen Input gibt

### Das Problem mit Freitext

Wenn ein Kunde einfach schreibt "Teste mal unser neues Statement", weiss das System nicht genug. Welche Branche? Welcher Markt? Wer ist die Zielgruppe? Was ist der Kontext?

### Unsere Lösung: Der intelligente Prompt Builder

Der Kunde gibt seinen Text frei ein, z.B.:

> "Die KPT Krankenkasse will auf TikTok eine junge Zielgruppe (18-30) in der Deutschschweiz erreichen. Wir überlegen drei Strategien: A) Edutainment über Gesundheitsthemen, B) Behind-the-Scenes aus dem Büroalltag, C) Provokante Vergleiche mit Konkurrenten."

Das System analysiert diesen Text automatisch mit KI und extrahiert die wichtigen Informationen:

| Feld | Erkannt |
|------|---------|
| Branche | Krankenversicherung |
| Unternehmen | KPT |
| Zielgruppe | 18-30 Jahre |
| Markt | Deutschschweiz |
| Plattform | TikTok (→ wir simulieren "Öffentliches Netzwerk") |
| Strategien | 3 Varianten (A, B, C) |

Dann prüft das System: **Was fehlt noch?** Und macht Vorschläge:

- "Gibt es eine Vorgeschichte? (z.B. frühere Social-Media-Präsenz der KPT?)"
- "Wer sind die Hauptkritiker? (z.B. Konsumentenschutz, Konkurrenten?)"
- "Welcher Tonfall soll getestet werden?"

Der Kunde ergänzt, bestätigt den finalen Prompt, und die Simulation startet.

**Warum das wichtig ist:** Je besser der Input, desto realistischer die Simulation. Der Prompt Builder stellt sicher, dass nichts Wichtiges vergessen wird.

---

## Schritt 3: Persona-Generierung — Wie die virtuellen Menschen entstehen

### Das Grundprinzip

Wir erzeugen 500 detaillierte "Basis-Personen" mit KI und skalieren sie dann auf tausende.

### Was ist eine Persona?

Jede Persona ist ein vollständiger virtueller Mensch mit:

- **Demografie:** Name, Alter, Geschlecht, Wohnort, Beruf, Bildung
- **Persönlichkeit:** Die "Big Five" Persönlichkeitsmerkmale (mehr dazu gleich)
- **Meinungen:** Was denkt die Person über relevante Themen?
- **Verhalten:** Wie oft postet sie? Welchen Stil hat sie? Benutzt sie Emojis?
- **Professionell (LinkedIn):** Job-Titel, Seniority, Branche

### Die Big Five — Warum Persönlichkeitspsychologie?

Die "Big Five" sind das am besten erforschte Modell der Persönlichkeitspsychologie. Jeder Mensch lässt sich auf 5 Skalen einordnen:

| Eigenschaft | Niedrig | Hoch | Auswirkung auf Social Media |
|-------------|---------|------|----------------------------|
| **Offenheit** | Traditionell, vorsichtig | Neugierig, kreativ | Hohe Offenheit → mehr Bereitschaft, neue Themen zu diskutieren |
| **Gewissenhaftigkeit** | Spontan, flexibel | Organisiert, pflichtbewusst | Hohe Gewissenhaftigkeit → durchdachtere, längere Posts |
| **Extraversion** | Introvertiert, ruhig | Gesellig, energiegeladen | Hohe Extraversion → postet öfter, interagiert mehr |
| **Verträglichkeit** | Kompetitiv, direkt | Kooperativ, empathisch | Niedrige Verträglichkeit → eher kontroverse Kommentare |
| **Neurotizismus** | Emotional stabil | Ängstlich, sensibel | Hoher Neurotizismus → reagiert stärker auf negative Nachrichten |

Jede Persona bekommt Werte zwischen 0 und 1 für jede dieser 5 Eigenschaften. Ein introvertierter Buchhalterin aus Bern verhält sich auf Social Media komplett anders als ein extrovertierter Startup-Gründer aus Berlin.

### Sinus-Milieus — Warum das wichtig ist

Die **Sinus-Milieus** sind ein Modell das die deutschsprachige Gesellschaft in 10 Gruppen einteilt, basierend auf Werten und Lebensstil. Das Sinus-Institut (Heidelberg) entwickelt dieses Modell seit den 1980ern, und es wird von fast allen grossen Unternehmen in DACH für Marketing genutzt.

Die 10 Milieus:

| Milieu | Anteil | Typische Merkmale |
|--------|--------|------------------|
| **Konservativ-Gehobenes** | 11% | Etabliert, bildungsbürgerlich, Tradition + Status |
| **Postmaterielles** | 12% | Kritisch, nachhaltig, links-liberal, Bildungselite |
| **Performer** | 10% | Leistungsorientiert, global, technikaffin, karrierebewusst |
| **Expeditives** | 10% | Urban, kreativ, digital native, individualistisch |
| **Neo-Ökologisches** | 8% | Umweltbewusst, progressiv, Konsum-kritisch |
| **Adaptiv-Pragmatische Mitte** | 12% | Anpassungsfähig, pragmatisch, sicherheitsorientiert |
| **Konsum-Hedonistisches** | 8% | Spass-orientiert, konsumorientiert, untere Mitte |
| **Prekäres** | 9% | Sozial benachteiligt, zukunftsängstlich, abgehängt |
| **Nostalgisch-Bürgerliches** | 11% | Ordnung, Sicherheit, "früher war alles besser" |
| **Traditionelles** | 9% | Ältere Generation, sparsam, pflichtbewusst, bescheiden |

**Warum nutzen wir das?** Wenn wir eine realistische Simulation der Schweizer Öffentlichkeit wollen, müssen unsere virtuellen Personen die tatsächliche Gesellschaftsstruktur abbilden. Wir können nicht 500 "Durchschnitts-Schweizer" generieren — die gibt es nicht. Stattdessen generieren wir z.B. 55 Konservativ-Gehobene, 60 Postmaterielle, 50 Performer, usw. — genau wie in der echten Gesellschaft.

Jedes Milieu hat andere Werte, andere Mediennutzung, andere Reaktionsmuster. Ein "Performer" reagiert auf eine Firmen-Krise anders als jemand aus dem "Prekären" Milieu.

### Stakeholder-Rollen — Wer diskutiert mit?

Nicht alle Personas sind "allgemeine Öffentlichkeit". Je nach Szenario gibt es spezifische Stakeholder:

**Beispiel: Bankenkrise**
- 15% betroffene Mitarbeiter (wütend, persönlich betroffen)
- 25% Kunden (besorgt um ihr Geld)
- 5% Journalisten (recherchieren, fragen kritisch nach)
- 5% Investoren (sorgen sich um Aktienkurs)
- 5% Politiker (fordern Regulierung)
- 35% allgemeine Öffentlichkeit (kommentieren, teilen Meinungen)
- 5% Aktivisten (nutzen die Krise für ihre Agenda)
- 5% Konkurrenz-Mitarbeiter (schadenfroh oder solidarisch)

Das System erkennt automatisch aus dem Input, welche Stakeholder relevant sind, und erzeugt die Personas entsprechend.

### Wie entstehen 50'000 aus 500?

500 Basis-Personas reichen nicht für eine grosse Simulation. Deshalb skalieren wir:

1. **500 Basis-Personas** werden einzeln mit KI erzeugt (detailliert, einzigartig)
2. **Parametrische Variation:** Jede Basis-Persona wird mehrfach kopiert und leicht verändert:
   - Alter um ±5 Jahre verschieben
   - Persönlichkeitswerte leicht variieren
   - Posting-Frequenz anpassen
   - Neuen Namen generieren
3. So entstehen aus 500 Basis-Personas z.B. 10'000 oder 50'000 Varianten

Das ist wie in der Biologie: gleiche "DNA" (Archetyp), aber individuelle Ausprägung.

### DACH-Spezifisch: Sprache

Ein wichtiges Detail: Unsere Personas "sprechen" Hochdeutsch mit regionalen Eigenheiten:

- **Schweiz:** "Velo" statt "Fahrrad", "parkieren" statt "parken", Referenzen auf NZZ, SRF, FINMA
- **Österreich:** "Jänner" statt "Januar", "heuer" statt "dieses Jahr", Referenzen auf ORF, AK, WKO
- **Deutschland:** Je nach Region — "Moin" im Norden, Referenzen auf Tagesschau, t3n, Handelsblatt

Wir versuchen NICHT Schweizerdeutsch zu simulieren — das kann keine KI zuverlässig. Und: Echte Schweizer schreiben auf LinkedIn und Twitter sowieso Hochdeutsch.

---

## Schritt 4: Das Soziale Netzwerk — Wie die Personas vernetzt werden

### Warum ein Netzwerk?

In der echten Welt sieht nicht jeder jeden Post. Du siehst Posts von Leuten denen du folgst, von Trending-Themen, und gelegentlich etwas Zufälliges. Dieses Verhalten müssen wir nachbilden.

### Der Social Graph

Wir bauen ein virtuelles Netzwerk mit einem Algorithmus namens **LFR** (Lancichinetti-Fortunato-Radicchi). Dieser Algorithmus erzeugt Netzwerke die realen Social-Media-Netzwerken verblüffend ähnlich sehen:

**Eigenschaft 1: Power-Law (Wenige Stars, viele Normalos)**
Genau wie auf echtem Twitter: 1% der User produzieren 90% des Contents. Einige wenige "Hub"-Nodes (Journalisten, Influencer) haben tausende Follower, die meisten haben wenige.

**Eigenschaft 2: Communities (Grüppchen)**
Menschen vernetzen sich mit Gleichgesinnten. IT-Leute folgen IT-Leuten, HR-Leute folgen HR-Leuten. Der Algorithmus erzeugt automatisch solche "Grüppchen" (Communities) mit vielen internen Verbindungen und wenigen Brücken nach aussen.

**Eigenschaft 3: Weak Ties (Brücken zwischen Gruppen)**
In echten Netzwerken gibt es "Brücken-Personen" die zwei Gruppen verbinden. Ein Journalist der sowohl in der Finance- als auch in der Tech-Community vernetzt ist, kann ein Thema von einer Gruppe in die andere tragen. Das simulieren wir mit 5-10% "schwachen Verbindungen" zwischen Communities.

### Unterschied Twitter vs. LinkedIn

| | Twitter-Simulation | LinkedIn-Simulation |
|---|---|---|
| Verbindung | Einseitig (ich folge dir, du nicht unbedingt mir) | Beidseitig (wir sind connected) |
| Netzwerk-Dichte | Lose, viele Follower bei Stars | Dichter, mehr gegenseitige Verbindungen |
| Communities | Themenbasiert | Branchen- und firmenbasiert |

---

## Schritt 5: Die Simulation — Wie die Personas diskutieren

Das ist das Herzstück. Hier passiert die "Magie".

### Der Rundenablauf

Eine Simulation läuft über 50 Runden. Jede Runde stellt einen Zeitabschnitt dar (z.B. eine Stunde oder einen Tag — je nach Szenario). In jeder Runde passiert folgendes:

```
Phase 1: WER ist aktiv?        (Willingness Scoring)
Phase 2: WAS sehen die?        (Feed-Generierung)
Phase 3: WAS tun die?          (KI-Entscheidung)
Phase 4: Aktionen ausführen     (Datenbank-Updates)
Phase 5: Metriken sammeln       (Analyse)
Phase 6: Live-Update senden     (an den Kunden)
```

### Phase 1: Willingness Scoring — Wer postet und wer nicht?

**Das Problem:** Wenn alle 10'000 Personas jede Runde posten, ist das unrealistisch. In der echten Welt posten die meisten Leute selten.

**Die Lösung:** Jede Runde berechnet das System für JEDE Persona einen "Willingness Score" — eine Wahrscheinlichkeit, dass diese Person gerade aktiv wird. Dieser Score basiert auf:

**Persönlichkeits-Faktoren (stabil):**
- Extraversion: Extrovertierte posten häufiger
- Posting-Frequenz: "Power User" sind öfter aktiv als "Gelegenheits-Poster"
- Meinungsstärke: Wer starke Meinungen hat, reagiert eher

**Kontext-Faktoren (dynamisch, ändern sich jede Runde):**
- Themen-Relevanz: Ist das aktuelle Thema für diese Person interessant?
- Netzwerk-Aktivität: Hat jemand dem sie folgt gerade gepostet?
- Emotionale Valenz: Ist das Thema kontrovers? (Kontroverse = mehr Aktivität)
- Neuheit: Neues Thema = mehr Interesse als Wiederholung

**Cooldown:** Wer gerade gepostet hat, pausiert ein paar Runden. Damit nicht dieselben Leute ständig posten.

### Dynamische Verteilung je nach Szenario

Hier kommt eine wichtige Design-Entscheidung: **Die Aktivitätsrate hängt vom Szenario ab.**

| Szenario-Typ | Aktive Personas | Warum? |
|------|---------|--------|
| **Krise** (Entlassungen, Skandal) | 70-80% | Alle sind betroffen, alle reden |
| **Standard** (Produktlaunch, Kampagne) | 40-50% | Moderate Beteiligung |
| **Routine** (Thought-Leadership-Post) | 20-30% | Die meisten scrollen weiter |

Das System erkennt automatisch anhand des Inputs, wie kontrovers das Thema ist, und passt die Verteilung an.

### Die vier Persona-Typen

| Typ | Anteil (bei Krise) | Was sie tun | KI-Aufwand |
|-----|-------------------|-------------|------------|
| **Power Creator** | 10% | Schreiben eigene Posts, lange Kommentare, starten Diskussionen | Voller KI-Aufruf |
| **Active Responder** | 40% | Kommentieren, reagieren, teilen, folgen | Voller KI-Aufruf |
| **Selective Engager** | 30% | Reagieren nur wenn Thema sie direkt betrifft | Vereinfachter KI-Aufruf |
| **Observer** | 20% | Lesen mit, liken gelegentlich | Minimal/automatisch |

**Warum diese Aufteilung?** Kosten-Effizienz. Jeder "volle KI-Aufruf" kostet Geld (ein API-Call an OpenAI). Observer brauchen keinen KI-Call — sie verhalten sich nach einfachen Regeln ("Like wenn Sentiment passt"). So sparen wir 80% der KI-Kosten, ohne die Qualität zu verlieren.

### Phase 2: Feed-Generierung — Was sieht jede Persona?

Jede aktive Persona bekommt einen "Feed" — 3-5 Posts die sie in dieser Runde sieht. Nicht jeder sieht das Gleiche. Der Feed wird nach einem Algorithmus zusammengestellt der echte Social-Media-Algorithmen nachahmt:

**Twitter-Feed (Öffentliches Netzwerk):**
- Posts von Leuten denen du folgst (gewichtet nach Engagement)
- Trending-Posts (viele Likes/Retweets)
- Etwas Zufälliges (damit nicht nur die eigene Bubble sichtbar ist)
- **Schneller Decay:** Alte Posts verlieren schnell an Sichtbarkeit (Halbwertszeit: 3 Runden)

**LinkedIn-Feed (Professionelles Netzwerk):**
- Posts von Connections und Branchen-Experten
- **Dwell-Time** ist der stärkste Faktor (wie lange jemand einen Post liest)
- Kommentare zählen 15x mehr als Likes (LinkedIn belohnt Diskussion)
- **Langsamer Decay:** Professionelle Inhalte bleiben länger sichtbar (Halbwertszeit: 8 Runden)
- Externe Links werden bestraft (LinkedIn will dich auf der Plattform halten)
- Carousel-Posts bekommen 2.4x Boost, Videos 3x

**Warum 15% "Zufall" im Feed?** Um Echo-Kammern zu verhindern. In einer reinen Relevanz-Bubble sehen alle nur Meinungen die ihre eigene bestätigen. Der Zufall sorgt dafür, dass auch gegenteilige Perspektiven durchkommen — genau wie in der Realität.

### Phase 3: KI-Entscheidung — Was tut die Persona?

Jetzt kommt der eigentliche KI-Moment. Jede aktive Persona bekommt einen "Prompt" (eine Anweisung an GPT-4o-mini) der so aussieht:

**Teil 1 (statisch, wird gecached):** "Du bist Claudia Meier, 38, Produktmanagerin bei einer Versicherung in Zürich. Du bist sachlich, kompetent, zurückhaltend. Du schreibst Hochdeutsch mit Helvetismen..."

**Teil 2 (dynamisch, ändert sich jede Runde):** "Hier ist dein Feed: [Post 1: Jemand kritisiert die Entlassungen bei SwissBank... 12 Likes] [Post 2: Ein Artikel über Employer Branding...] Was willst du tun?"

Die KI antwortet mit einer **strukturierten Aktion**, z.B.:
- "Ich kommentiere Post 1: 'Die Kommunikation hätte transparenter sein können. Als jemand in der Branche finde ich...'"
- Oder: "Ich like Post 2"
- Oder: "Ich tue nichts (nicht relevant für mich)"

**Verfügbare Aktionen auf Twitter:** Post erstellen, Liken, Retweeten, Kommentieren, Folgen, Nichts tun

**Verfügbare Aktionen auf LinkedIn:** Post, Artikel, 6 Reaktionstypen (Like/Feiern/Aufschlussreich/Witzig/Liebe/Unterstützung), Kommentar, Antwort, Teilen, Verbinden, Folgen, Empfehlung, Nichts tun

### Das Memory-System — Wie Personas sich erinnern

Ein wichtiges Detail: Personas vergessen nicht. Jede Persona hat ein Gedächtnis:

- **Sliding Window:** Die letzten 3-5 Beobachtungen ("Runde 5: Sah 3 negative Posts über Entlassungen")
- **Wichtige Erinnerungen:** Wenn ein eigener Post 50 Likes bekommt oder eine kontroverse Diskussion stattfand, wird das gespeichert
- **Zusammenfassung:** Alle 5 Runden fasst das System die Erinnerungen in 2-3 Sätze zusammen

**Warum das wichtig ist:** Ohne Gedächtnis würde Persona "Claudia" in Runde 20 vergessen, dass sie in Runde 5 einen Post gegen die Entlassungen geschrieben hat, und plötzlich das Gegenteil behaupten. Das Memory-System sorgt für **Konsistenz über die gesamte Simulation**.

### Anti-Sycophancy — Warum nicht alle einer Meinung sein dürfen

KI-Modelle haben ein bekanntes Problem: Sie neigen dazu, zuzustimmen statt zu widersprechen ("Sycophancy"). Ohne Gegenmassnahmen würden nach 50 Runden alle Personas derselben Meinung sein. Das wäre nutzlos.

Unsere Gegenmassnahmen:

1. **Meinungs-Trägheit:** Meinungen ändern sich nur langsam (80% alte Meinung + 20% neuer Einfluss). Wie im echten Leben — ein einzelner Post ändert selten die Grundhaltung.

2. **Zealots (5-10%):** Personas deren Meinung sich NIE ändert. Der überzeugte Umweltaktivist bleibt Umweltaktivist, egal was passiert. Diese "Anker" sorgen dafür, dass die Meinungsdiversität erhalten bleibt.

3. **Contrarians (5%):** Personas die grundsätzlich der Mehrheitsmeinung widersprechen. Es gibt sie auch in der echten Welt — und sie sind wichtig für realistische Dynamiken.

4. **Bounded Confidence:** Personas ignorieren Posts die zu weit von ihrer eigenen Meinung entfernt sind. Ein überzeugter Verfechter der Firma liest keine extremen Hass-Posts — wie im echten Leben.

5. **Verteilungs-Vorgabe:** Bei der Persona-Generierung stellen wir sicher: 30% positiv, 40% neutral, 30% negativ zum Thema. So starten wir mit echter Meinungsvielfalt.

---

## Schritt 6: Live-Ansicht — Was der Kunde in Echtzeit sieht

Während die Simulation läuft, sieht der Kunde zwei Dinge im Browser:

### Der Netzwerk-Graph

Ein interaktives Diagramm wo:
- Jeder **Punkt** eine Persona ist
- Jede **Linie** eine Interaktion (Follow, Kommentar, Like)
- Die **Farbe** das Sentiment zeigt (Grün = positiv, Rot = negativ, Grau = neutral)
- **Cluster** sichtbar werden — Gruppen von Personas die ähnlich denken

Man kann live beobachten wie sich Cluster bilden, wie Meinungen von einer Gruppe zur nächsten wandern, und wo "Brücken-Personen" Themen zwischen Gruppen übertragen.

### Der Live-Feed

Daneben läuft ein Feed — wie echtes Twitter/LinkedIn. Posts und Kommentare scrollen in Echtzeit rein. Der Kunde kann mitlesen was die Personas schreiben.

### Fortschrittsanzeige

- Aktuelle Runde (z.B. "Runde 23 von 50")
- Geschätzte Restzeit
- Bisherige Kosten der Simulation

---

## Schritt 7: Der Report — Was am Ende rauskommt

### Interaktives Dashboard

Nach Abschluss der Simulation bekommt der Kunde ein Dashboard mit:

**Sentiment-Verlauf:** Ein Chart das zeigt wie sich die Stimmung über die 50 Runden entwickelt hat. Z.B.: "In den ersten 5 Runden neutral, dann kippt die Stimmung, ab Runde 15 stark negativ."

**Top-Narrative:** Die wichtigsten Themen die in der Diskussion aufgetaucht sind:
- "Kritik an der Kommunikationsstrategie" (42% der Posts)
- "Solidarität mit den Betroffenen" (28%)
- "Forderung nach politischem Eingriff" (15%)
- "Verteidigung der Unternehmens-Entscheidung" (15%)

**Risiko-Analyse:** Automatisch identifizierte Gefahren:
- "Hohes Risiko: Hashtag #SwissBankSkandal entsteht in Runde 8"
- "Mittel: Journalistin @MaxReporter schreibt Thread der viral geht"

**Engagement-Metriken:** Posts, Likes, Kommentare, Shares pro Runde als Charts.

### Narrative-Erkennung — Wie funktioniert das technisch?

Das System erkennt automatisch Themen/Narrative in den tausenden Posts. So funktioniert es:

1. Jeder Post wird in einen **mathematischen Vektor** umgewandelt (ein "Embedding"). Posts die inhaltlich ähnlich sind, haben ähnliche Vektoren.
2. Ähnliche Posts werden automatisch **gruppiert** (Clustering). Z.B.: alle Posts die über "Entlassungen sind unfair" reden, landen in einem Cluster.
3. Für jede Gruppe fragt das System die KI: **"Fasse dieses Thema in 3-5 Wörtern zusammen."** → "Kritik an Sozialplan"
4. Über die Runden hinweg verfolgt das System wie jedes Narrativ wächst, schrumpft oder stirbt.

### PDF-Export

Der Kunde kann den gesamten Report als PDF exportieren — professionell formatiert, mit Charts und Zusammenfassung. Ideal um es an Kunden oder den Vorstand weiterzuleiten.

### Quality Badge — Wie gut war die Simulation?

Jeder Report bekommt ein Qualitäts-Badge:

- **GRÜN:** "Hohe Simulationsqualität" — Diverse Meinungen, realistische Engagement-Muster, gute Persona-Konsistenz
- **GELB:** "Eingeschränkte Diversität" — Einige Metriken im Warnbereich
- **ROT:** "Möglicherweise unzuverlässig" — Simulation hat Qualitätsprobleme

Das macht uns transparent und unterscheidet uns von Wettbewerbern die unbewiesene "95% Accuracy" behaupten.

---

## Die Zwei Plattformen

### Öffentliches Netzwerk (Twitter-ähnlich)

Simuliert öffentliche, schnelle, emotionale Diskussionen:
- Kurze Posts (280 Zeichen)
- Virale Verbreitung möglich (ein einzelner Tweet kann explodieren)
- Anonymere Tonalität (mehr Trolle, mehr extreme Meinungen)
- Schnelllebig (Themen kommen und gehen innerhalb von Stunden)

**Beste Use Cases:** Shitstorm-Vorhersage, Hashtag-Kampagnen, öffentliche Krisen

### Professionelles Netzwerk (LinkedIn-ähnlich)

Simuliert professionelle, langsamere, sachlichere Diskussionen:
- Längere Posts (bis 3000 Zeichen)
- Keine Viralität (LinkedIn unterdrückt das bewusst)
- Reale Identität (Job-Titel, Firma — alle wissen wer spricht)
- Langlebiger (ein guter Post ist 2-3 Tage relevant)

**Beste Use Cases:** CEO-Kommunikation, Employer Branding, M&A-Ankündigungen, B2B-Kampagnen

---

## Technische Infrastruktur — Was unter der Haube passiert

### Die KI (GPT-4o-mini)

Wir nutzen OpenAI's GPT-4o-mini — ein schnelles, günstiges KI-Modell. Warum dieses?
- Gutes Deutsch
- Schnell genug für tausende Aufrufe
- Günstig: ~$0.15 pro Million Input-Tokens
- "Function Calling": Das Modell kann strukturierte Aktionen zurückgeben (nicht nur Text)

**Provider-agnostisch:** Unsere Architektur ist so gebaut, dass wir jederzeit auf ein anderes Modell wechseln können (z.B. Claude, Gemini). Wir sind nicht an OpenAI gebunden.

### Kosten pro Simulation

| Grösse | Personas | Runden | KI-Aufrufe | Kosten |
|--------|----------|--------|-----------|--------|
| Klein | 1'000 | 50 | ~2'500 | **~$0.72** |
| Mittel | 10'000 | 50 | ~15'000 | **~$3.67** |
| Gross | 50'000 | 50 | ~50'000 | **~$12.27** |

Bei Preisen von CHF 199-2'999/Monat ergibt das Margen von 85-95%.

### Prompt Caching — Warum 73% der KI-Kosten gespart werden

Der "Persona-Teil" des KI-Prompts (wer ist diese Person, welche Regeln gelten) ist für jede Persona über alle 50 Runden gleich. OpenAI cached automatisch wiederkehrende Prompt-Teile und gibt 50% Rabatt darauf.

Unsere Prompts sind so strukturiert, dass der statische Teil (Persona + Regeln) zuerst kommt und der dynamische Teil (Feed + Memory) zuletzt. So maximieren wir den Cache-Hit.

### Fehlerbehandlung — Was wenn etwas schiefgeht?

Bei 50'000 KI-Aufrufen pro Simulation gehen Dinge schief. Unsere Strategie:

1. **Retry mit Backoff:** Wenn ein KI-Aufruf fehlschlägt, warten wir kurz und versuchen es nochmal (bis zu 5 Mal, mit steigender Wartezeit)
2. **Circuit Breaker:** Wenn >15% der Personas in einer Runde fehlschlagen, pausiert die Simulation und wartet auf manuelle Prüfung
3. **Degradation:** Wenn eine einzelne Persona fehlschlägt, wird sie zum "Observer" degradiert (liest nur noch mit, postet nicht mehr). Die Simulation läuft weiter.
4. **Checkpoint:** Alle 5 Runden speichert das System den kompletten Zustand. Wenn die Simulation crasht, kann sie ab dem letzten Checkpoint fortgesetzt werden — nicht von vorne.
5. **Teilergebnisse:** Selbst wenn die Simulation nur 35 von 50 Runden schafft, sind die Ergebnisse nutzbar und werden dem Kunden gezeigt.

---

## Warum das besser ist als die Konkurrenz

| | Swaarm | Artificial Societies ($40/Mo) | Simile ($100k+/Jahr) |
|---|---|---|---|
| Echte Simulation | Ja (50 Runden Agent-Interaktion) | Nein (einmaliger Durchlauf) | Ja |
| LinkedIn-Simulation | Ja | Nein | Nein |
| Live-Ansicht | Ja (Netzwerk-Graph + Feed) | Nein | Nein |
| DACH-Personas | Ja (Sinus-Milieus, regional) | Nein | Nein |
| Preis | CHF 199-2'999/Mo | $40/Mo | $100'000+/Jahr |
| Transparenz | Quality Badge | "95% Accuracy" (unbewiesen) | Undurchsichtig |

---

## Zusammenfassung: Der Bauplan auf einen Blick

```
INPUT
  └── Kunde gibt Statement/Kampagne ein
       └── KI analysiert, strukturiert, fragt nach

VORBEREITUNG (einmal pro Simulation)
  ├── 500 Basis-Personas generieren (KI, $0.07)
  ├── Auf 1k-50k skalieren (parametrische Variation, gratis)
  └── Soziales Netzwerk generieren (LFR-Algorithmus)

SIMULATION (50 Runden)
  ├── Willingness Scoring (wer ist aktiv? <5ms, keine KI nötig)
  ├── Feed generieren (was sieht jeder? <50ms)
  ├── KI-Entscheidung (was tun aktive Personas? async, parallel)
  ├── Aktionen ausführen (DB-Updates, <20ms)
  ├── Metriken sammeln (Sentiment, Narrative, Engagement)
  └── Live-Update an Kunden senden (WebSocket)

OUTPUT
  ├── Interaktives Dashboard (Sentiment-Charts, Narrative, Risiken)
  ├── PDF-Report (für Weitergabe an Kunden/Vorstand)
  └── Quality Badge (Grün/Gelb/Rot)
```

**Geschätzte Simulationsdauer:**
- 1'000 Personas: ~5-10 Minuten
- 10'000 Personas: ~20-45 Minuten
- 50'000 Personas: ~1-3 Stunden
