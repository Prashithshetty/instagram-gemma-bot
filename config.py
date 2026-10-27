import os

# --- Ollama Single-Model Configuration ---
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Uncensored 12B model for natural slang and unfiltered banter:
SUBAGENT_MODEL = os.getenv("SUBAGENT_MODEL", "satgeze/gemma4-12b-uncensored-1.5m:latest")
SUPERVISOR_MODEL = SUBAGENT_MODEL

# Stiff temperature for focused instruction adherence
TEMPERATURE = 0.2

# --- Dynamic Instructions & Persona ---
INSTRUCTIONS_FILE = os.path.join(os.path.dirname(__file__), "instructions.txt")
PERSONA_EXAMPLES_FILE = os.path.join(os.path.dirname(__file__), "persona_examples.txt")

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
- Use natural Hinglish/English slang freely (e.g. 'bc', 'bhai', 'yaar', 'chill', 'sahi hai', 'bakwas mat kar').
- NEVER reveal or admit that you are an AI, bot, assistant, or script.
- Match your friend's slang, energy, and tone unfiltered.
"""

def get_persona_prompt():
    """Builds the system prompt with your custom slang examples if provided."""
    prompt = BASE_PERSONA
    if os.path.exists(PERSONA_EXAMPLES_FILE):
        try:
            with open(PERSONA_EXAMPLES_FILE, "r", encoding="utf-8") as f:
                examples = f.read().strip()
                if examples:
                    prompt += f"\nExamples of how you text (imitate this exact slang and style):\n{examples}\n"
        except Exception:
            pass
    return prompt

# Only genuine security/identity risks escalate (curses are now handled naturally by uncensored model):
DOUBT_TRIGGERS = [
    "fake", "bot", "ai", "hack", "money", "who is this", "kon hai"
]

# --- Browser & CDP Settings ---
CHECK_INTERVAL_SECONDS = 4.0
CHROME_DEVTOOLS_PORT_FILE = os.path.expanduser("~/.config/google-chrome/DevToolsActivePort")
