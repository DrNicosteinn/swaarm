import asyncio
import json
import os
import time

from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME, OASIS_TWITTER_ACTIONS
from app.utils.logger import get_logger

logger = get_logger(__name__)


def run_simulation(sim):
    """Run an OASIS Twitter simulation. Called from a background thread."""
    logger.info(
        f"Starting simulation {sim.id}: {sim.num_agents} agents, {sim.num_rounds} rounds"
    )
    asyncio.run(_run_async(sim))


async def _run_async(sim):
    """Async OASIS simulation loop."""
    try:
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType, ModelType
        import oasis
        from oasis import ActionType, LLMAction, ManualAction, generate_twitter_agent_graph
    except ImportError as e:
        raise RuntimeError(f"OASIS not installed: {e}")

    # Set OpenAI key for OASIS agents
    os.environ["OPENAI_API_KEY"] = LLM_API_KEY
    if LLM_BASE_URL and "openai.com" not in LLM_BASE_URL:
        os.environ["OPENAI_API_BASE_URL"] = LLM_BASE_URL

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

    # Generate agent graph from profiles CSV
    logger.info(f"Generating agent graph from {sim.profiles_path}")
    agent_graph = await generate_twitter_agent_graph(
        profile_path=sim.profiles_path,
        model=model,
        available_actions=available_actions,
    )
    num_agents = len(agent_graph.get_agents())
    logger.info(f"Agent graph created: {num_agents} agents")

    # Clean old DB
    db_path = os.path.join(sim.data_dir, "simulation.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    # Create environment
    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.TWITTER,
        database_path=db_path,
        semaphore=min(num_agents, 30),
    )

    try:
        await env.reset()
        logger.info("Environment reset, agents signed up")

        # Seed post from agent 0 with the scenario
        seed_content = (
            f"{sim.scenario}\n\n"
            f"Was denkt ihr darueber? #Diskussion"
        )
        seed_actions = {
            env.agent_graph.get_agent(0): ManualAction(
                action_type=ActionType.CREATE_POST,
                action_args={"content": seed_content[:500]},
            )
        }
        await env.step(seed_actions)
        logger.info("Seed post created")

        # Run simulation rounds
        for round_num in range(1, sim.num_rounds + 1):
            # Check if stopped
            if sim.status.value in ("stopped", "failed"):
                logger.info(f"Simulation stopped at round {round_num}")
                break

            start = time.time()
            logger.info(f"Round {round_num}/{sim.num_rounds}")

            # All agents act via LLM
            actions = {
                agent: LLMAction()
                for _, agent in agent_graph.get_agents()
            }
            await env.step(actions)

            sim.current_round = round_num
            elapsed = time.time() - start
            logger.info(f"Round {round_num} completed in {elapsed:.1f}s")

            # Save progress
            sim.save()

    finally:
        await env.close()

    # Export actions from SQLite trace table to actions.jsonl
    _export_actions(db_path, sim)

    logger.info(
        f"Simulation {sim.id} completed: {sim.num_rounds} rounds, "
        f"{sim.total_actions} actions"
    )


def _export_actions(db_path: str, sim):
    """Read trace table from OASIS SQLite DB and write actions.jsonl."""
    import sqlite3

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT user_id, action, info, created_at FROM trace ORDER BY created_at"
    ).fetchall()
    conn.close()

    # Load persona names from CSV for display
    agent_names = _load_agent_names(sim.profiles_path)

    with open(sim.actions_path, "w", encoding="utf-8") as f:
        for user_id, action, info_json, created_at in rows:
            # Skip internal actions
            if action in ("sign_up", "refresh", "update_rec_table"):
                continue

            info = json.loads(info_json) if info_json else {}
            action_data = {
                "round": created_at,
                "agent_id": user_id,
                "agent_name": agent_names.get(user_id, f"Agent_{user_id}"),
                "action_type": action,
                "content": info.get("content", ""),
                "post_id": info.get("post_id"),
                "timestamp": time.time(),
            }
            f.write(json.dumps(action_data, ensure_ascii=False) + "\n")
            sim.total_actions += 1

    sim.save()


def _load_agent_names(csv_path: str) -> dict[int, str]:
    """Load username mapping from profiles CSV."""
    import csv

    names = {}
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                names[i] = row.get("username", f"Agent_{i}")
    except Exception:
        pass
    return names
