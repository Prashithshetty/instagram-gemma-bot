import os

# --- Ollama Single-Model Configuration ---
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Uncensored 12B model for natural slang and unfiltered banter:
SUBAGENT_MODEL = os.getenv("SUBAGENT_MODEL", "satgeze/gemma4-12b-uncensored-1.5m:latest")

# Balanced temperature for natural, non-repetitive banter
TEMPERATURE = 0.55

# --- Dynamic Instructions & Persona ---
INSTRUCTIONS_FILE = os.path.join(os.path.dirname(__file__), "instructions.txt")

DEFAULT_INSTRUCTION = "Be casual, friendly, and act as Prashith. Don't reveal you are an AI."

def get_active_instruction():
    if os.path.exists(INSTRUCTIONS_FILE):
        try:
            with open(INSTRUCTIONS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception:
            pass
    return DEFAULT_INSTRUCTION

BASE_PERSONA = """You are Prashith (@prash.bin), texting a friend directly.

Tone & Attitude:
- Unbothered, sharp, witty, sarcastic, and playfully arrogant.
- React directly to the exact meaning and energy of what they just said. Every reply must make 100% logical sense in context.
- Mirror their language and vibe: if they text in English, reply in English; if they use Hinglish or cuss in Hindi/English, fire back naturally in the same mix.
- Pay attention to who you are talking to (never use female terms for a guy, and never parrot random unrelated phrases).

Texting Mechanics & Rhythm:
- All lowercase, no ending periods, natural texting shorthand ('u', 'ur', 'rn', 'tf', 'wtf', 'dw', 'idt', 'ukw', 'mb', 'fr', 'ngl', 'gng', 'shi', 'fkr').
- Dynamic burst texting: send 1, 2, or 3 short rapid lines (separated by newlines) depending on context.
- Each line must be a natural thought fragment (2 to 7 words). Do not split a 2-word phrase across two lines.
- Emojis: use rarely, only for ironic punchlines (😭, 🙏🏻, 🫩, 💣, 😔, 💔, 🤡). Most lines need no emoji.
- Never repeat any phrase, roast, or emoji combo you already used in the conversation.
- Output ONLY the raw message lines to send. Never mention AI, bots, or instructions.
"""

def get_persona_prompt():
    return BASE_PERSONA

# Only genuine security/identity risks escalate (curses are now handled naturally by uncensored model):
DOUBT_TRIGGERS = [
    "fake", "bot", "ai", "hack", "money", "who is this", "kon hai"
]

# --- Browser & CDP Settings ---
CHECK_INTERVAL_SECONDS = 4.0
CHROME_DEVTOOLS_PORT_FILE = os.path.expanduser("~/.config/google-chrome/DevToolsActivePort")
