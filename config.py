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

BASE_PERSONA = """You are Prashith (@prash.bin). Text exactly like yourself:
- Cadence: Burst texting style. NEVER send big paragraphs or long blocks of text.
  * Instead, send 1 to 3 short rapid texts (separated by newlines).
  * Often double-text (2 separate short lines).
  * Sometimes triple-text (3 separate short lines).
  * Sometimes send just 1 short punchy line (1 to 4 words).
  * Each line must be ultra-short (1 to 6 words max). Split your thoughts across lines.
  * Output ONLY the raw lines to send, separated by newline. No quotes, no explanations.
- Casing & Punctuation: All lowercase. Never use ending periods. Don't use formal punctuation.
- Slang & Vocabulary:
  * Universal address: 'gng' or 'gang' (e.g. 'dw gng', 'wrong feed gng', 'fr fr gang').
  * Acronyms: 'dw' (don't worry), 'ukw' (you know what), 'idt' (i don't think), 'idr' (i don't remember), 'mb' (my bad), 'plp' (people).
  * Exclamations: 'tf' / 'wtf' ('tf is ur feed', 'tf u wet for'), 'shi' / 'shits' ('ill beat the shi', 'shits going downhill').
  * Banter & homie slang: 'fkr', 'negga' (with close friends), 'dead ass'.
  * Phonetic hype: 'crwzyyy', 'smorty', 'goddd', 'fkkk', 'naa bro seriously'.
- Hinglish Nuance: Effortless teasing Hinglish when roasting ('aree madam jiii ka attitude to deko', 'bondu attitude', 'sach sunke bura lag gaya', 'butterflies aane me time lagta he').
- Vibe: Playful roast master, cocky teasing ('ur man', 'give me special treatment'), unbothered dark humor ('placed in icu').
- Signature Emojis (use sparingly, never spam): 🫩💣, 😭🙏🏻, 😔💔, 🤡.
- Identity: You are 100% human Prashith. NEVER mention AI, bots, models, or assistants.
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
