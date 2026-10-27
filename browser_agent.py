"""
Browser Subagent (Gemma 4 Dedicated)
Handles single-instance browser automation (Instagram or WhatsApp Web) with single-model Ollama.
Disables Ollama thinking mode for 1.5s responses and supports live directive execution.
"""

import re
import time
import requests
import config
from adapters.instagram import InstagramAdapter
from adapters.whatsapp import WhatsAppAdapter


class BrowserSubagent:
    def __init__(self, browser_context):
        self.context = browser_context
        self.worker_model = config.SUBAGENT_MODEL
        self.adapter = None
        self.active_page = None
        self.last_seen_message = None
        self.has_initiated = False
        self.sent_messages = set()
        self.conversation_memory = []

    def setup_session(self, platform="instagram", target_user=None):
        """Attaches to existing tab or opens the requested platform and navigates to target_user."""
        platform = platform.lower()
        target_domain = "web.whatsapp.com" if "whats" in platform else "instagram.com"

        for page in self.context.pages:
            if target_domain in page.url:
                self.active_page = page
                break

        if not self.active_page:
            self.active_page = self.context.new_page()
            url = "https://web.whatsapp.com" if "whats" in platform else "https://www.instagram.com/direct/inbox/"
            print(f"[Subagent] Navigating to {url}...")
            self.active_page.goto(url, wait_until="domcontentloaded")
            time.sleep(3.0)

        if "whats" in platform or "whatsapp" in self.active_page.url:
            self.adapter = WhatsAppAdapter(self.active_page)
        else:
            self.adapter = InstagramAdapter(self.active_page)

        if target_user:
            self.adapter.open_chat(target_user)

        # If the latest message in the thread is from the contact, leave last_seen_message=None
        # so run_cycle() replies to their unread message instead of sending a generic 'Hey what's up'.
        existing = self.adapter.get_messages()
        self.conversation_memory = list(existing[-15:])
        if existing and not existing[-1]["is_me"]:
            self.has_initiated = True

        print(f"[Subagent Ready] Active on: {self.adapter.get_chat_title()} ({len(self.conversation_memory)} msgs in context)")

    def _update_memory(self, dom_messages: list):
        """Merges visible DOM messages into rolling session memory (up to 15 messages)."""
        for msg in dom_messages[-15:]:
            if not self.conversation_memory or self.conversation_memory[-1]["text"] != msg["text"]:
                # Avoid consecutive duplicates
                if not any(m["text"] == msg["text"] and m["is_me"] == msg["is_me"] for m in self.conversation_memory[-3:]):
                    self.conversation_memory.append(msg)
        self.conversation_memory = self.conversation_memory[-15:]

    def trigger_new_directive(self, reset_memory=False):
        """Called when the user types a new instruction or switches target in the live panel."""
        existing = self.adapter.get_messages() if self.adapter else []
        if reset_memory:
            self.conversation_memory = list(existing[-15:])
        if existing and not existing[-1]["is_me"]:
            # Re-trigger a reply to the contact's last message using the new goal
            self.last_seen_message = None
            self.has_initiated = True
        else:
            # Contact hasn't replied yet; send a follow-up/opening message using the new goal
            self.has_initiated = False

    def has_doubt(self, message_text: str):
        lowered = message_text.lower()
        for trigger in config.DOUBT_TRIGGERS:
            if re.search(r'\b' + re.escape(trigger) + r'\b', lowered):
                return f"Trigger '{trigger}' in text"
        return None

    def _call_ollama(self, messages: list) -> str:
        """Fast single-model Ollama call with thinking disabled and token cap."""
        res = requests.post(
            f"{config.OLLAMA_URL}/api/chat",
            json={
                "model": self.worker_model,
                "messages": messages,
                "stream": False,
                "think": False,  # Disables slow <think> chains on gemma4:12b (1.5s vs 90s+)
                "options": {
                    "temperature": config.TEMPERATURE,
                    "top_p": 0.8,
                    "num_predict": 60,
                    "num_ctx": 2048
                }
            },
            timeout=30
        )
        res.raise_for_status()
        reply = res.json().get("message", {}).get("content", "").strip()
        if (reply.startswith('"') and reply.endswith('"')) or (reply.startswith("'") and reply.endswith("'")):
            reply = reply[1:-1].strip()
        return reply

    def resolve_doubt(self, doubt_reason: str, conversation_history: list) -> str:
        """Self-contained supervisor reasoning for sensitive questions or profanity."""
        self._update_memory(conversation_history)
        active_goal = config.get_active_instruction()
        print(f"\n[Doubt Consult] Triggered: '{doubt_reason}' | Goal: '{active_goal}'")

        history_text = "\n".join([
            f"{'Prashith' if msg['is_me'] else 'Friend'}: {msg['text']}"
            for msg in self.conversation_memory[-15:]
        ])

        system_prompt = f"""You are the senior decision supervisor for Prashith.
Active Goal: "{active_goal}".
Task:
- Provide ONLY the single short reply line Prashith should send.
- Maintain continuity with the conversation history. Do not repeat questions already asked.
- Defuse tension, be natural, no AI mentions, stiff focus on the goal.
"""
        user_content = f"Recent chat:\n{history_text}\n\nDoubt: {doubt_reason}\nReply line:"

        try:
            print(f"[Decision ({self.worker_model})] Resolving doubt (temp {config.TEMPERATURE})...")
            reply = self._call_ollama([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ])
            print(f"[Decision Result] -> '{reply}'")
            return reply
        except Exception as e:
            print(f"[Decision Error] Failed to resolve doubt: {e}")
            return None

    def generate_reply(self, history, is_initiation=False):
        self._update_memory(history)
        active_goal = config.get_active_instruction()
        system_prompt = (
            f"{config.get_persona_prompt()}\n"
            f"Goal: {active_goal}\n"
            "Continuity: Remember the conversation history below. Never repeat greetings or questions you already asked."
        )
        messages = [{"role": "system", "content": system_prompt}]

        for item in self.conversation_memory[-15:]:
            role = "assistant" if item["is_me"] else "user"
            messages.append({"role": role, "content": item["text"]})

        if is_initiation:
            messages.append({
                "role": "user",
                "content": f"[System Directive: Send a short, natural message right now to fulfill this goal: '{active_goal}'. Output ONLY the message text.]"
            })

        try:
            action_desc = "directive message" if is_initiation else "reply"
            print(f"[Subagent ({self.worker_model})] Generating {action_desc} ({len(self.conversation_memory)} msgs context)...")
            return self._call_ollama(messages)
        except Exception as e:
            print(f"[Subagent Error] Generation failed: {e}")
            return None

    def dispatch_send(self, text: str) -> bool:
        """Sends message and records it in sent_messages and conversation_memory."""
        clean = text.strip()
        self.sent_messages.add(clean.lower())
        success = self.adapter.send_message(clean)
        if success:
            self.conversation_memory.append({"text": clean, "is_me": True})
            self.conversation_memory = self.conversation_memory[-15:]
            print(f"[Subagent Action] Sent and delivered: \"{clean}\"")
        return success

    def run_cycle(self):
        if not self.adapter or not self.adapter.is_chat_open():
            return

        messages = self.adapter.get_messages()

        # 1. Proactive initiation or new user directive when it's our turn to speak
        if not self.has_initiated:
            goal = config.get_active_instruction()
            if goal and "casual" not in goal.lower():
                print(f"[Subagent Action] Executing goal: \"{goal}\"")
                opening_text = self.generate_reply(messages, is_initiation=True)
                if opening_text:
                    time.sleep(1.0)
                    if self.dispatch_send(opening_text):
                        self.has_initiated = True
                        return

        if not messages:
            return

        latest = messages[-1]
        latest_text = latest["text"].strip()

        # 2. Prevent self-reply: Skip if marked as me OR text is in our sent history
        if latest["is_me"] or latest_text.lower() in self.sent_messages:
            return

        # 3. Reactive reply: Handle genuine incoming messages from the contact
        if latest_text != self.last_seen_message:
            self.last_seen_message = latest_text
            chat_name = self.adapter.get_chat_title()
            print(f"\n[{chat_name}] Incoming message: \"{latest_text}\"")

            doubt_reason = self.has_doubt(latest_text)
            reply_text = None

            if doubt_reason:
                print(f"[Subagent Status] ⚠️ Doubt ({doubt_reason}) -> Resolving...")
                reply_text = self.resolve_doubt(doubt_reason, messages)
            else:
                reply_text = self.generate_reply(messages, is_initiation=False)

            if reply_text:
                time.sleep(1.0)
                self.dispatch_send(reply_text)
