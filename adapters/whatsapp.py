import time
from adapters.base import BasePlatformAdapter


class WhatsAppAdapter(BasePlatformAdapter):
    """Adapter for WhatsApp Web (web.whatsapp.com)."""

    def is_chat_open(self) -> bool:
        """Checks if a conversation pane (#main) is currently active."""
        try:
            return self.page.locator('#main').is_visible()
        except Exception:
            return False

    def wait_for_ready(self, timeout=30):
        """Waits for WhatsApp Web to finish initial chat loading."""
        print("[WhatsApp] Waiting for chat list to load...")
        try:
            self.page.wait_for_selector('#side', timeout=timeout * 1000)
            time.sleep(1.0)
            return True
        except Exception:
            print("[WhatsApp Warning] WhatsApp loading took longer than expected.")
            return False

    def open_chat(self, target_user: str) -> bool:
        """Finds and opens a chat by search name or phone number."""
        self.wait_for_ready()
        clean_target = target_user.strip()
        print(f"[WhatsApp] Searching for contact: '{clean_target}'...")

        try:
            search_box = self.page.locator('#side div[contenteditable="true"]').first
            if not search_box.is_visible():
                search_box = self.page.locator('div[data-tab="3"], #side [role="textbox"]').first

            search_box.click(timeout=5000)
            time.sleep(0.3)

            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            time.sleep(0.2)

            self.page.keyboard.type(clean_target, delay=40)
            time.sleep(1.5)

            matched_contact = self.page.locator(f'#pane-side span[title*="{clean_target}" i]').first
            if matched_contact.is_visible():
                matched_contact.click(timeout=3000)
                time.sleep(1.0)
            else:
                self.page.keyboard.press("Enter")
                time.sleep(1.5)

            try:
                self.page.wait_for_selector('#main', timeout=5000)
                print(f"[WhatsApp] Successfully opened chat: {self.get_chat_title()}")
                return True
            except Exception:
                pass

        except Exception as e:
            print(f"[WhatsApp Search Error] {e}")

        print(f"[WhatsApp Error] Could not open chat for '{clean_target}'.")
        return False

    def get_chat_title(self) -> str:
        try:
            title = self.page.evaluate("""() => {
                const header = document.querySelector('#main header span[dir="auto"], #main header');
                if (header) {
                    const firstSpan = header.querySelector('span[dir="auto"]');
                    return (firstSpan || header).innerText.split('\\n')[0].trim();
                }
                return document.title;
            }""")
            return title or "WhatsApp Chat"
        except Exception:
            return "WhatsApp Chat"

    def get_messages(self):
        if not self.is_chat_open():
            return []

        # Uses geometry: Outgoing messages on WhatsApp are strictly on the right side of #main.
        # Broad selector catches messages with or without timestamp data-pre-plain-text attributes.
        script = """() => {
            const messages = [];
            const main = document.querySelector('#main');
            if (!main) return [];

            const mainRect = main.getBoundingClientRect();
            const bubbles = Array.from(main.querySelectorAll('.copyable-text, [data-testid="msg-container"]'));
            const seenTexts = new Set();

            bubbles.forEach(el => {
                const textSpan = el.querySelector('span.selectable-text');
                if (!textSpan) return;
                const text = textSpan.innerText.trim();
                if (!text || seenTexts.has(text) || /^\\d{1,2}:\\d{2}\\s?(AM|PM)?$/i.test(text)) return;

                const rect = el.getBoundingClientRect();
                const isRightAligned = (rect.left + rect.width / 2) > (mainRect.left + mainRect.width / 2);

                seenTexts.add(text);
                messages.push({
                    text: text,
                    is_me: isRightAligned
                });
            });

            return messages;
        }"""
        try:
            return self.page.evaluate(script)
        except Exception:
            return []

    def send_message(self, text: str) -> bool:
        if not self.is_chat_open():
            print("[WhatsApp Send Error] No active chat is open in #main.")
            return False

        try:
            textbox = self.page.locator('#main footer div[contenteditable="true"]').first
            textbox.click(timeout=3000)
            time.sleep(0.2)
            self.page.keyboard.insert_text(text)
            time.sleep(0.2)
            self.page.keyboard.press("Enter")
            return True
        except Exception as e:
            print(f"[WhatsApp Send Error] {e}")
            return False
