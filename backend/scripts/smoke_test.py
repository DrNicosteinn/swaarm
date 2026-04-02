"""
SwarmSight AI - Smoke Test
Minimale OASIS Twitter-Simulation: 5 Agents, 3 Runden, gpt-4o-mini
"""
import asyncio
import csv
import json
import os
import sqlite3
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

# Set OPENAI_API_KEY for OASIS
os.environ["OPENAI_API_KEY"] = os.environ.get("LLM_API_KEY", "")

DATA_DIR = os.path.join(os.path.dirname(__file__), "../uploads/simulations/smoke_test")
PROFILE_PATH = os.path.join(DATA_DIR, "profiles.csv")
DB_PATH = os.path.join(DATA_DIR, "simulation.db")

print("=" * 60)
print("SwarmSight AI - Smoke Test")
print("=" * 60)


# Step 1: Test OpenAI
print("\n[1/5] Teste OpenAI Verbindung...")
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Sage nur 'OK'"}],
    max_tokens=5,
)
print(f"  OK: {resp.choices[0].message.content}")


# Step 2: Generate personas via LLM
print("\n[2/5] Generiere 5 Personas via LLM...")
persona_resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "Du erstellst Social-Media-Personas. Antworte als JSON.",
        },
        {
            "role": "user",
            "content": """Erstelle 5 Social-Media-Personas fuer dieses Szenario:
"Nestle kuendigt an, Cailler-Schokolade in Plastik statt Karton zu verpacken"

JSON: {"personas": [{"username": "...", "description": "kurze Bio", "user_char": "Ausfuehrliche Persona-Beschreibung mit Meinung zum Thema (2-3 Saetze)"}]}
Genau 5, verschiedene Meinungen.""",
        },
    ],
    max_tokens=1500,
    temperature=0.8,
    response_format={"type": "json_object"},
)
personas = json.loads(persona_resp.choices[0].message.content)["personas"]
print(f"  {len(personas)} Personas generiert:")
for p in personas:
    print(f"    @{p['username']}: {p['description'][:60]}")


# Step 3: Write CSV
print("\n[3/5] Schreibe OASIS-kompatible CSV...")
os.makedirs(DATA_DIR, exist_ok=True)
with open(PROFILE_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["username", "description", "user_char"])
    writer.writeheader()
    writer.writerows(personas)
print(f"  CSV: {PROFILE_PATH}")


# Step 4: Run OASIS Simulation
print("\n[4/5] Starte OASIS Simulation (5 Agents, 3 Runden)...")
print("  Dies kann 1-3 Minuten dauern...\n")

from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

import oasis
from oasis import ActionType, LLMAction, ManualAction, generate_twitter_agent_graph


async def run_simulation():
    # Create model
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )

    # Available actions
    available_actions = [
        ActionType.CREATE_POST,
        ActionType.LIKE_POST,
        ActionType.REPOST,
        ActionType.DO_NOTHING,
    ]

    # Generate agent graph
    print("  Generiere Agent-Graph...")
    agent_graph = await generate_twitter_agent_graph(
        profile_path=PROFILE_PATH,
        model=model,
        available_actions=available_actions,
    )
    agents = agent_graph.get_agents()
    print(f"  Agent-Graph: {len(agents)} Agents erstellt")

    # Clean old DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    # Create environment
    print("  Erstelle Environment...")
    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.TWITTER,
        database_path=DB_PATH,
        semaphore=5,
    )

    # Reset
    await env.reset()
    print("  Environment bereit.\n")

    # Seed post (Agent 0 erstellt einen ersten Post zum Thema)
    print("  Runde 0: Seed-Post...")
    seed_actions = {
        env.agent_graph.get_agent(0): ManualAction(
            action_type=ActionType.CREATE_POST,
            action_args={
                "content": (
                    "Nestle hat angekuendigt, Cailler-Schokolade neu in Plastik "
                    "statt Karton zu verpacken. Sie sagen es sei besser recycelbar. "
                    "Was denkt ihr darueber? #Nestle #Nachhaltigkeit #Cailler"
                )
            },
        )
    }
    await env.step(seed_actions)
    print("  Seed-Post erstellt.\n")

    # Run 3 rounds with LLM actions
    for round_num in range(1, 4):
        start = time.time()
        print(f"  Runde {round_num}/3...", end=" ", flush=True)
        actions = {agent: LLMAction() for _, agent in agent_graph.get_agents()}
        await env.step(actions)
        elapsed = time.time() - start
        print(f"fertig ({elapsed:.1f}s)")

    # Close
    await env.close()
    print("\n  Simulation abgeschlossen!")


try:
    asyncio.run(run_simulation())
except Exception as e:
    print(f"\n  FEHLER: {e}")
    import traceback

    traceback.print_exc()


# Step 5: Read results
print(f"\n[5/5] Lese Ergebnisse aus DB...")
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)

    tables = [
        t[0]
        for t in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    ]
    print(f"  Tabellen: {tables}")

    if "trace" in tables:
        cols = [
            d[0]
            for d in conn.execute("SELECT * FROM trace LIMIT 1").description
        ]
        total = conn.execute("SELECT COUNT(*) FROM trace").fetchone()[0]
        print(f"  Spalten: {cols}")
        print(f"  Total Aktionen: {total}")

        print("\n  Alle Aktionen:")
        rows = conn.execute(
            "SELECT user_id, action, info, created_at FROM trace ORDER BY created_at"
        ).fetchall()
        for user_id, action, info_json, ts in rows:
            info = json.loads(info_json) if info_json else {}
            content = str(info.get("content", info.get("response", "")))[:100]
            print(f"    Agent {user_id} | {action} | {content}")
    else:
        for t in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
            if count > 0:
                cols = [
                    d[0]
                    for d in conn.execute(f"SELECT * FROM [{t}] LIMIT 1").description
                ]
                print(f"\n  {t} ({count} rows): {cols}")
                rows = conn.execute(f"SELECT * FROM [{t}] LIMIT 5").fetchall()
                for row in rows:
                    print(f"    {dict(zip(cols, row))}")

    conn.close()
else:
    print("  Keine DB gefunden.")

print("\n" + "=" * 60)
print("Smoke Test abgeschlossen!")
print("=" * 60)
