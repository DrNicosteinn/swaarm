import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

# LLM Configuration
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini")

# OASIS Simulation
OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get("OASIS_DEFAULT_MAX_ROUNDS", "50"))
OASIS_DEFAULT_NUM_AGENTS = int(os.environ.get("OASIS_DEFAULT_NUM_AGENTS", "200"))
OASIS_SIMULATION_DATA_DIR = os.path.join(
    os.path.dirname(__file__), "../uploads/simulations"
)

# Twitter actions available in OASIS
OASIS_TWITTER_ACTIONS = [
    "CREATE_POST",
    "LIKE_POST",
    "REPOST",
    "FOLLOW",
    "DO_NOTHING",
    "QUOTE_POST",
]
