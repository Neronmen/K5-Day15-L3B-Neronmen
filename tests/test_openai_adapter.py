"""Provider contract regression; all responses below are synthetic fixtures."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase"))
import ai


class OpenAIAdapterTests(unittest.TestCase):
    def call_with_contract(self, provider, model, modern):
        def provider_stub(url, headers, body):
            if modern:
                if "max_tokens" in body:
                    raise ValueError("Unsupported parameter: 'max_tokens'. Use 'max_completion_tokens' instead.")
                self.assertEqual(body["max_completion_tokens"], ai.MAX_TOKENS)
                self.assertNotIn("temperature", body)
            else:
                self.assertEqual(body["max_tokens"], ai.MAX_TOKENS)
                self.assertEqual(body["temperature"], ai.TEMPERATURE)
            self.assertEqual(body["messages"], [{"role": "system", "content": "system fixture"},
                                                 {"role": "user", "content": "user fixture"}])
            return {"choices": [{"message": {"content": "fixture"}}],
                    "usage": {"prompt_tokens": 17, "completion_tokens": 23,
                              "completion_tokens_details": {"reasoning_tokens": 7}}}

        with patch.object(ai, "MODEL_NAME", model), patch.object(ai, "post_json", provider_stub):
            result = ai.call_openai_compatible("system fixture", "user fixture", provider)
        self.assertEqual(result, {"text": "fixture", "tokens_in": 17, "tokens_out": 23})

    def test_gpt6_accepts_supported_payload_and_uses_total_usage(self):
        for model in ("gpt-6-luna", "gpt-5-mini", "o3-mini"):
            with self.subTest(model=model):
                self.call_with_contract("openai", model, modern=True)

    def test_legacy_openai_payload_stays_compatible(self):
        self.call_with_contract("openai", "gpt-4.1-mini", modern=False)

    def test_deepseek_payload_stays_compatible(self):
        self.call_with_contract("deepseek", "deepseek-chat", modern=False)


if __name__ == "__main__":
    unittest.main()
