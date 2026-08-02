import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(ROOT))

from llm_providers import (  # noqa: E402
    PROVIDERS,
    DEFAULTS,
    build_claude_payload,
    build_gemini_payload,
    extract_claude_text,
    extract_gemini_text,
    extract_openai_text,
    claude_url,
    gemini_url,
    openai_chat_url,
)


class TestProvidersMeta(unittest.TestCase):
    def test_providers_set(self):
        self.assertEqual(
            PROVIDERS,
            frozenset({"ollama", "openai", "claude", "gemini", "openai_compat"}),
        )

    def test_defaults_have_models(self):
        for p in PROVIDERS:
            self.assertIn(p, DEFAULTS)
            self.assertIn("model", DEFAULTS[p])


class TestClaudeMap(unittest.TestCase):
    def test_build_claude_payload_splits_system(self):
        messages = [
            {"role": "system", "content": "SYS"},
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": "T:ok"},
            {"role": "user", "content": "miro"},
        ]
        payload = build_claude_payload(
            model="claude-haiku-4-5",
            system="SYS",
            messages=messages,
            temperature=0.5,
            max_tokens=220,
        )
        self.assertEqual(payload["model"], "claude-haiku-4-5")
        self.assertEqual(payload["system"], "SYS")
        self.assertEqual(payload["max_tokens"], 220)
        roles = [m["role"] for m in payload["messages"]]
        self.assertNotIn("system", roles)
        self.assertEqual(roles, ["user", "assistant", "user"])

    def test_extract_claude_text(self):
        data = {"content": [{"type": "text", "text": "T:hola|mundo\nS:0\nE:0"}]}
        self.assertIn("T:hola", extract_claude_text(data))


class TestGeminiMap(unittest.TestCase):
    def test_build_gemini_contents(self):
        messages = [
            {"role": "system", "content": "SYS"},
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": "resp"},
            {"role": "user", "content": "miro"},
        ]
        payload = build_gemini_payload(
            system="SYS",
            messages=messages,
            temperature=0.7,
            max_tokens=220,
        )
        self.assertEqual(payload["systemInstruction"]["parts"][0]["text"], "SYS")
        roles = [c["role"] for c in payload["contents"]]
        self.assertEqual(roles, ["user", "model", "user"])
        self.assertEqual(payload["contents"][1]["parts"][0]["text"], "resp")

    def test_extract_gemini_text(self):
        data = {
            "candidates": [
                {"content": {"parts": [{"text": "T:linea\nS:1\nE:0"}]}}
            ]
        }
        self.assertIn("T:linea", extract_gemini_text(data))


class TestUrls(unittest.TestCase):
    def test_urls(self):
        self.assertTrue(openai_chat_url("https://api.openai.com/v1").endswith("/chat/completions"))
        self.assertTrue(claude_url("https://api.anthropic.com/v1").endswith("/messages"))
        g = gemini_url("https://generativelanguage.googleapis.com/v1beta", "gemini-2.0-flash")
        self.assertIn("models/gemini-2.0-flash:generateContent", g)

    def test_extract_openai(self):
        data = {"choices": [{"message": {"content": "hola"}}]}
        self.assertEqual(extract_openai_text(data), "hola")


from ai_adventure import AdventureAI  # noqa: E402


class TestApplyConfig(unittest.TestCase):
    def test_accepts_all_providers(self):
        ai = AdventureAI()
        for p in PROVIDERS:
            ai.apply_config({"provider": p})
            self.assertEqual(ai.provider, p)

    def test_rejects_unknown_provider(self):
        ai = AdventureAI(provider="ollama")
        ai.apply_config({"provider": "nope"})
        self.assertEqual(ai.provider, "ollama")

    def test_api_base_alias(self):
        ai = AdventureAI()
        ai.apply_config({"openai_base": "http://x/v1"})
        self.assertEqual(ai.api_base, "http://x/v1")
        cfg = ai.config_dict()
        self.assertEqual(cfg["api_base"], "http://x/v1")
        self.assertEqual(cfg["openai_base"], "http://x/v1")


if __name__ == "__main__":
    unittest.main()
