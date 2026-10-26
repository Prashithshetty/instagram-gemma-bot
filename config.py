import os

# --- Ollama Single-Model Configuration ---
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Using ONLY Gemma to prevent GPU VRAM thrashing/swapping
SUBAGENT_MODEL = os.getenv("SUBAGENT_MODEL", "gemma4:12b")
SUPERVISOR_MODEL = SUBAGENT_MODEL

# Stiff temperature for focused instruction adherence
TEMPERATURE = 0.15

# --- Dynamic Instructions & Persona ---
INSTRUCTIONS_FILE = os.path.join(os.path.dirname(__file__), "instructions.txt")

def get_active_instruction():
    if os.path.exists(INSTRUCTIONS_FILE):
        try:
            with open(INSTRUCTIONS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception:
            pass
    return "Be casual, friendly, and act as Prashith. Don't reveal you are an AI."

BASE_PERSONA = """You are Prashith.
Rules:
- 1 short sentence max. Casual texting style.
- Natural Hinglish/English banter when appropriate.
- NEVER reveal or admit that you are an AI, bot, assistant, or script.
- Follow the user's active goal strictly.
"""

# Specific high-risk keywords that require senior supervisor guidance
DOUBT_TRIGGERS = [
    "madarchod", "bhenchod", "chutiya", "fake", "bot", "ai", "hack",
    "money", "who is this", "kon hai"
]

# --- Browser & CDP Settings ---
CHECK_INTERVAL_SECONDS = 4.0
CHROME_DEVTOOLS_PORT_FILE = os.path.expanduser("~/.config/google-chrome/DevToolsActivePort")
