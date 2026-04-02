import json
import os

from app.services.llm_client import chat
from app.utils.logger import get_logger

logger = get_logger(__name__)

REPORT_SYSTEM_PROMPT = """Du bist ein erfahrener PR- und Kommunikationsberater, spezialisiert auf Social-Media-Analyse im DACH-Raum.

Du analysierst die Ergebnisse einer Multi-Agent-Social-Media-Simulation und erstellst einen strukturierten Bericht.

Dein Bericht soll:
- Praxisnah und actionable sein
- Risiken klar benennen
- Konkrete Empfehlungen geben
- In professionellem aber verstaendlichem Deutsch geschrieben sein
"""

REPORT_USER_PROMPT = """Analysiere die folgende Social-Media-Simulation und erstelle einen strukturierten Bericht.

**Szenario:** {scenario}
**Kontext:** {context}
**Zielgruppe:** {target_audience}
**Simulationsdetails:** {num_agents} Agenten, {num_rounds} Runden

**Zusammenfassung der Aktionen:**
{actions_summary}

**Beispiel-Posts aus der Simulation:**
{sample_posts}

Erstelle den Bericht mit folgender Struktur:

# Simulationsbericht: [Titel]

## 1. Executive Summary
(3-5 Saetze, wichtigste Erkenntnisse)

## 2. Sentiment-Analyse
(Wie verteilt sich die Stimmung? Wie entwickelt sie sich ueber die Runden?)

## 3. Dominante Narrative
(Top 5 Argumente/Themen die in der Diskussion aufkamen)

## 4. Risiko-Assessment
(Was koennte eskalieren? Welche Narrative sind gefaehrlich?)

## 5. Zielgruppen-Analyse
(Welche Gruppen reagieren wie? Wer sind die lautesten Stimmen?)

## 6. Empfehlungen
(Konkrete Handlungsempfehlungen fuer die Kommunikationsstrategie)

## 7. Fazit
"""


def generate_report(sim) -> str:
    """Generate a structured analysis report from simulation results."""
    logger.info(f"Generating report for simulation {sim.id}")

    actions_summary, sample_posts = _parse_actions(sim)

    messages = [
        {"role": "system", "content": REPORT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": REPORT_USER_PROMPT.format(
                scenario=sim.scenario,
                context=sim.context,
                target_audience=sim.target_audience,
                num_agents=sim.num_agents,
                num_rounds=sim.num_rounds,
                actions_summary=actions_summary,
                sample_posts=sample_posts,
            ),
        },
    ]

    report = chat(messages, temperature=0.5, max_tokens=4096)

    # Save report
    with open(sim.report_path, "w", encoding="utf-8") as f:
        f.write(report)

    logger.info(f"Report saved to {sim.report_path}")
    return report


def chat_with_report(sim, message: str, history: list[dict]) -> str:
    """Chat with the report agent about simulation results."""
    report_text = ""
    if os.path.exists(sim.report_path):
        with open(sim.report_path) as f:
            report_text = f.read()

    system_msg = (
        f"{REPORT_SYSTEM_PROMPT}\n\n"
        f"Du hast folgende Simulation analysiert:\n"
        f"Szenario: {sim.scenario}\n"
        f"Kontext: {sim.context}\n\n"
        f"Dein Bericht:\n{report_text[:3000]}"
    )

    messages = [{"role": "system", "content": system_msg}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    return chat(messages, temperature=0.7, max_tokens=2048)


def _parse_actions(sim) -> tuple[str, str]:
    """Parse actions.jsonl into summary and sample posts."""
    actions = []
    if os.path.exists(sim.actions_path):
        with open(sim.actions_path) as f:
            for line in f:
                try:
                    actions.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue

    if not actions:
        return "Keine Aktionen aufgezeichnet.", "Keine Posts vorhanden."

    # Summary stats
    action_types = {}
    for a in actions:
        t = a.get("action_type", "unknown")
        action_types[t] = action_types.get(t, 0) + 1

    summary_lines = [f"Total Aktionen: {len(actions)}"]
    for t, count in sorted(action_types.items(), key=lambda x: -x[1]):
        summary_lines.append(f"- {t}: {count}")
    summary = "\n".join(summary_lines)

    # Sample posts (first 20 CREATE_POST actions)
    posts = [
        a for a in actions if a.get("action_type") in ("CREATE_POST", "create_post")
    ][:20]
    if posts:
        sample_lines = []
        for p in posts:
            name = p.get("agent_name", "Unbekannt")
            content = p.get("content", "")[:200]
            rnd = p.get("round", "?")
            sample_lines.append(f"[Runde {rnd}] @{name}: {content}")
        sample_posts = "\n".join(sample_lines)
    else:
        sample_posts = "Keine Posts in der Simulation gefunden."

    return summary, sample_posts
