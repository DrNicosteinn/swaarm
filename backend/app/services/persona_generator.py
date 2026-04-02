import csv
import json

from app.services.llm_client import chat_json
from app.utils.logger import get_logger

logger = get_logger(__name__)

PERSONA_SYSTEM_PROMPT = """Du bist ein Experte fuer Social-Media-Verhalten und Demografie im DACH-Raum.

Deine Aufgabe: Erstelle realistische Social-Media-Persona-Profile fuer eine Simulation.

Regeln:
- Verwende realistische deutschsprachige Namen
- Jede Persona braucht eine klare Meinung zum Szenario (positiv/negativ/neutral)
- Variiere Alter, Geschlecht, Beruf, Persoenlichkeit
- Manche Personas sind sehr aktiv (Influencer), die meisten eher passiv
- Beruecksichtige verschiedene Stakeholder-Gruppen
"""

PERSONA_USER_PROMPT = """Erstelle {num_agents} Social-Media-Personas fuer folgendes Szenario:

**Szenario:** {scenario}
**Kontext:** {context}
**Zielgruppe:** {target_audience}

Antworte als JSON:
{{
  "personas": [
    {{
      "username": "anna_mueller",
      "description": "Mutter von 2, Lehrerin, interessiert an Nachhaltigkeit",
      "user_char": "Anna ist eine 32-jaehrige umweltbewusste Lehrerin aus Zuerich. Sie reagiert kritisch auf Greenwashing und teilt ihre Meinung aktiv auf Social Media. Sie steht dem Szenario negativ gegenueber."
    }}
  ]
}}

Genau {num_agents} Personas. Verteile Meinungen: ~40% negativ, ~30% neutral, ~30% positiv.
user_char muss 2-3 Saetze lang sein und die Meinung zum Szenario enthalten."""


def generate_personas(sim) -> str:
    """Generate OASIS-compatible agent profiles from a simulation scenario."""
    logger.info(f"Generating {sim.num_agents} personas for simulation {sim.id}")

    messages = [
        {"role": "system", "content": PERSONA_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": PERSONA_USER_PROMPT.format(
                num_agents=sim.num_agents,
                scenario=sim.scenario,
                context=sim.context or "Kein zusaetzlicher Kontext",
                target_audience=sim.target_audience or "Allgemeines Publikum, DACH-Raum",
            ),
        },
    ]

    result = chat_json(messages, temperature=0.8)
    personas = result.get("personas", [])

    if not personas:
        raise ValueError("LLM returned no personas")

    logger.info(f"Generated {len(personas)} personas")

    # Save as JSON (for reference / frontend display)
    json_path = sim.data_dir + "/personas.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(personas, f, indent=2, ensure_ascii=False)

    # Save as OASIS-compatible CSV (columns: username, description, user_char)
    with open(sim.profiles_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["username", "description", "user_char"]
        )
        writer.writeheader()
        for p in personas:
            writer.writerow({
                "username": p.get("username", "user"),
                "description": p.get("description", ""),
                "user_char": p.get("user_char", "A social media user."),
            })

    logger.info(f"Profiles saved to {sim.profiles_path}")
    return sim.profiles_path
