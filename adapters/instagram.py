import os
import json
import time
from adapters.base import BasePlatformAdapter

CACHE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "instagram_chats.json"))


class InstagramAdapter(BasePlatformAdapter):
    """Adapter for Instagram Direct messages with robust New Message search & geometric message alignment."""

    def __init__(self, page):
        super().__init__(page)
        self.target_user = None

    def load_cache(self) -> dict:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            except Exception:
                pass
        return {}

    def save_cache(self, cache: dict):
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"[Instagram Warning] Could not save cache: {e}")

    def is_chat_open(self) -> bool:
        return "/direct/t/" in self.page.url or self.page.locator('div[role="textbox"][contenteditable="true"]').is_visible()

    def open_chat(self, target_user: str) -> bool:
        """
        Navigates to the direct chat thread:
        1. Checks local URL cache (instant direct navigation).
        2. If first time or not cached, searches in Direct inbox via New Message modal.
        3. Clicks the closest matching contact, opens the thread, and caches the URL for future use.
        """
        clean_target = target_user.strip().lower().lstrip("@")
        self.target_user = clean_target
        cache = self.load_cache()

        # 1. Fast Path: Cached Direct Chat URL
        if clean_target in cache:
            cached_url = cache[clean_target]
            if cached_url in self.page.url:
                print(f"[Instagram] Already in target chat: {cached_url}")
                return True
            print(f"[Instagram] Navigating to cached thread for '{clean_target}': {cached_url}")
            self.page.goto(cached_url, wait_until="domcontentloaded")
            time.sleep(2.0)
            return True

        # 2. Discovery Path: Open inbox and search
        print(f"[Instagram] Locating '{clean_target}' in Direct inbox...")
        if "instagram.com/direct/inbox" not in self.page.url:
            self.page.goto("https://www.instagram.com/direct/inbox/", wait_until="domcontentloaded")
            time.sleep(2.5)

        # Check existing list in sidebar first
        try:
            buttons = self.page.locator('div[role="listitem"] button, div[role="listitem"] [role="button"]')
            count = buttons.count()
            for i in range(count):
                btn = buttons.nth(i)
                text = btn.inner_text().lower()
                if clean_target in text:
                    print(f"[Instagram] Found matching conversation in list. Opening...")
                    btn.click()
                    time.sleep(2.0)
                    if "/direct/t/" in self.page.url:
                        cache[clean_target] = self.page.url
                        self.save_cache(cache)
                        print(f"[Instagram] Cached thread URL: {self.page.url}")
                        return True
        except Exception as e:
            print(f"[Instagram List Warning] {e}")

        # 3. New Message search modal
        try:
            print(f"[Instagram] Searching via 'New message'...")
            new_msg_btn = self.page.locator('svg[aria-label="New message"]').first
            if new_msg_btn.is_visible():
                new_msg_btn.click()
                time.sleep(1.5)

                dialog = self.page.locator('div[role="dialog"]').first
                search_input = dialog.locator('input[type="text"]').first
                if search_input.is_visible():
                    search_input.fill(clean_target)
                    time.sleep(2.0)

                    checkbox = dialog.locator('input[type="checkbox"]').first
                    if checkbox.is_visible():
                        checkbox.click()
                        time.sleep(1.0)

                        chat_btn = dialog.locator('div[role="button"]:has-text("Chat"), button:has-text("Chat")').first
                        if chat_btn.is_visible():
                            chat_btn.click()
                            time.sleep(2.5)

                            if "/direct/t/" in self.page.url:
                                cache[clean_target] = self.page.url
                                self.save_cache(cache)
                                print(f"[Instagram] Successfully opened and cached thread URL: {self.page.url}")
                                return True
        except Exception as e:
            print(f"[Instagram Modal Search Error] {e}")

        print(f"[Instagram Error] Could not open chat for '{clean_target}'. Please click the chat in Chrome.")
        return False

    def get_chat_title(self) -> str:
        try:
            title = self.page.evaluate("""() => {
                const header = document.querySelector('header h2, div[role="main"] h1, div[role="main"] span[dir="auto"]');
                return header ? header.innerText.trim() : document.title;
            }""")
            return title or "Instagram Chat"
        except Exception:
            return "Instagram Chat"

    def get_messages(self):
        """
        Uses geometric screen alignment:
        Articles on the right side of the chat window are sent by Me.
        Articles on the left side are incoming from the contact.
        Immune to Instagram HTML changes.
        """
        script = """() => {
            const main = document.querySelector("div[role=\\"main\\"]") || document.body;
            const mainRect = main.getBoundingClientRect();
            const articles = Array.from(document.querySelectorAll("[role=\\"article\\"]"));

            return articles.map(a => {
                const rect = a.getBoundingClientRect();
                const isRightAligned = (rect.left + rect.width / 2) > (mainRect.left + mainRect.width / 2);
                return {
                    text: a.innerText.trim(),
                    is_me: isRightAligned
                };
            }).filter(m => m.text.length > 0);
        }"""
        try:
            return self.page.evaluate(script)
        except Exception:
            return []

    def send_message(self, text: str) -> bool:
        try:
            textbox = self.page.locator('div[role="textbox"][contenteditable="true"]').first
            if not textbox.is_visible():
                textbox = self.page.locator('div[aria-label="Message..."][contenteditable="true"]').first

            textbox.click(timeout=3000)
            time.sleep(0.2)
            textbox.fill(text)
            time.sleep(0.2)
            self.page.keyboard.press("Enter")
            return True
        except Exception as e:
            print(f"[Instagram Send Error] {e}")
            return False
