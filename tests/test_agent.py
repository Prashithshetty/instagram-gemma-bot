import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from browser_agent import BrowserSubagent
import config


def test_doubt_detection():
    class DummySubagent:
        has_doubt = BrowserSubagent.has_doubt

    sub = DummySubagent()

    # Must flag real triggers
    assert sub.has_doubt("madarchod") is not None
    assert sub.has_doubt("are you an AI bot?") is not None
    assert sub.has_doubt("who is this?") is not None

    # Must NOT flag words with 'ai' inside them like 'kaafi', 'bhai', 'sahi'
    assert sub.has_doubt("Haan yaar, kaafi sahi chal raha hai.") is None
    assert sub.has_doubt("bhai kaisa hai") is None
    assert sub.has_doubt("Reboot into Cosmic login screen") is None

    print("✓ Doubt regex boundary tests passed!")


def test_geometric_alignment():
    # Simulation of screen alignment: right side = Me, left side = Contact
    main_width = 800
    main_left = 100
    main_center = main_left + main_width / 2  # 500

    # Contact message bubble on the left
    contact_rect_left = 120
    contact_rect_width = 200
    contact_center = contact_rect_left + contact_rect_width / 2  # 220 < 500
    assert (contact_center > main_center) is False

    # My outgoing message bubble on the right
    my_rect_left = 550
    my_rect_width = 200
    my_center = my_rect_left + my_rect_width / 2  # 650 > 500
    assert (my_center > main_center) is True

    print("✓ Geometric screen alignment math passed!")


def test_url_cache_serialization():
    from adapters.instagram import InstagramAdapter
    
    # Fake adapter using a temporary cache file
    class DummyAdapter(InstagramAdapter):
        def __init__(self, tmp_path):
            self.cache_file = tmp_path

        def load_cache(self):
            if os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, "r") as f:
                        content = f.read().strip()
                        if content:
                            return json.loads(content)
                except Exception:
                    pass
            return {}

        def save_cache(self, cache):
            with open(self.cache_file, "w") as f:
                json.dump(cache, f)

    with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
        ad = DummyAdapter(tmp.name)
        assert ad.load_cache() == {}

        ad.save_cache({"pickle_rick": "https://instagram.com/direct/t/123"})
        loaded = ad.load_cache()
        assert loaded.get("pickle_rick") == "https://instagram.com/direct/t/123"

    print("✓ URL cache serialization passed!")


def test_directive_retrigger():
    class FakeAdapter:
        def __init__(self, msgs):
            self.msgs = msgs
        def get_messages(self):
            return self.msgs

    class DummySubagent(BrowserSubagent):
        def __init__(self, msgs):
            self.adapter = FakeAdapter(msgs)
            self.last_seen_message = "old"
            self.has_initiated = True

    # Case 1: Last message is from contact -> should clear last_seen_message to reply immediately
    sub1 = DummySubagent([{"text": "Bore hua hai", "is_me": False}])
    sub1.trigger_new_directive()
    assert sub1.last_seen_message is None
    assert sub1.has_initiated is True

    # Case 2: Last message is from us -> should set has_initiated=False to send follow-up
    sub2 = DummySubagent([{"text": "Hey", "is_me": True}])
    sub2.trigger_new_directive()
    assert sub2.has_initiated is False

    print("✓ Live directive re-trigger tests passed!")


if __name__ == "__main__":
    test_doubt_detection()
    test_geometric_alignment()
    test_url_cache_serialization()
    test_directive_retrigger()
    print("\nAll unit tests passed successfully!")
