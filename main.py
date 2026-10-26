#!/usr/bin/env python3
"""
Interactive Browser Assistant (Powered strictly by Local Gemma)
Single-model architecture to keep VRAM usage low and avoid GPU thrashing.
"""

import os
import sys
import time
import queue
import threading
import requests
from playwright.sync_api import sync_playwright

import config
from browser_agent import BrowserSubagent


def get_cdp_endpoint():
    path = config.CHROME_DEVTOOLS_PORT_FILE
    if not os.path.exists(path):
        print(f"[Error] Chrome DevTools port file not found at: {path}")
        print("Please start Chrome with: google-chrome --remote-debugging-port=9222 &")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return f"ws://127.0.0.1:{lines[0]}{lines[1]}"


def verify_models():
    try:
        res = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=3)
        available = [m.get("name") for m in res.json().get("models", [])]
        status = "✓ Ready" if config.SUBAGENT_MODEL in available else "! Missing"
        print(f"  {status} [Single Local Model]: {config.SUBAGENT_MODEL}")
    except Exception as e:
        print(f"[Ollama Error] Connection failed: {e}")
        print("Start Ollama in a terminal with: ollama serve")
        sys.exit(1)


def browser_worker(platform, target_user, cmd_queue, stop_event):
    cdp_url = get_cdp_endpoint()
    print(f"\n[CDP] Connecting to Chrome via {cdp_url}...")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(cdp_url)
        subagent = BrowserSubagent(browser.contexts[0])
        subagent.setup_session(platform=platform, target_user=target_user)

        print("\n" + "=" * 65)
        print("  PANEL ACTIVE: Type new instructions anytime and press Enter.")
        print("  Commands: '/target <user>', '/status', 'exit'")
        print("=" * 65 + "\n")

        while not stop_event.is_set():
            while not cmd_queue.empty():
                try:
                    cmd = cmd_queue.get_nowait()
                except queue.Empty:
                    break

                if cmd.startswith("/target "):
                    new_user = cmd[8:].strip()
                    print(f"\n[Panel Action] Switching target to: '{new_user}'")
                    subagent.adapter.open_chat(new_user)
                    subagent.trigger_new_directive(reset_memory=True)
                elif cmd == "/status":
                    chat_name = subagent.adapter.get_chat_title() if subagent.adapter else "None"
                    goal = config.get_active_instruction()
                    print(f"\n[Status Report]")
                    print(f"  Active Chat: {chat_name}")
                    print(f"  Active Goal: {goal}")
                    print(f"  Context Memory: {len(subagent.conversation_memory)} messages")
                    print(f"  Last Seen Message: {subagent.last_seen_message}")
                elif cmd.startswith("/instruction "):
                    new_goal = cmd[13:].strip()
                    print(f"\n[Head Agent Updated] New directive active: \"{new_goal}\"")
                    subagent.trigger_new_directive()

            try:
                subagent.run_cycle()
            except Exception as e:
                print(f"\n[Cycle Warning] {e}")

            stop_event.wait(config.CHECK_INTERVAL_SECONDS)

        print("[Detaching] Closing browser session...")
        browser.close()


def main():
    print("=" * 65)
    print("  LOCAL BROWSER PANEL (Gemma 4 Dedicated)")
    print(f"  Model: {config.SUBAGENT_MODEL} (Single VRAM Footprint)")
    print(f"  Focus Mode: Stiff Temperature {config.TEMPERATURE}")
    print("=" * 65)

    verify_models()

    print("\n--- Setup Session ---")
    platform = input("Platform [instagram/whatsapp] (default: instagram): ").strip() or "instagram"
    target_user = input("Target Username/Contact (e.g. akxrv or prashith): ").strip()
    initial_goal = input("Instruction for Head Agent (or Enter for default): ").strip()

    if initial_goal:
        with open(config.INSTRUCTIONS_FILE, "w", encoding="utf-8") as f:
            f.write(initial_goal + "\n")

    cmd_queue = queue.Queue()
    stop_event = threading.Event()

    worker = threading.Thread(
        target=browser_worker,
        args=(platform, target_user, cmd_queue, stop_event),
        daemon=True
    )
    worker.start()

    try:
        while True:
            try:
                line = input("[You -> Head Agent] > ").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not line or len(line) < 2 or line in ["\\", "/", ".", "-"]:
                continue

            if line.lower() in ["exit", "quit", "/exit"]:
                break
            elif line.startswith("/"):
                cmd_queue.put(line)
            else:
                with open(config.INSTRUCTIONS_FILE, "w", encoding="utf-8") as f:
                    f.write(line + "\n")
                cmd_queue.put(f"/instruction {line}")

    finally:
        print("\nStopping panel...")
        stop_event.set()
        worker.join(timeout=3.0)
        print("[Done] Session terminated cleanly.")


if __name__ == "__main__":
    main()
