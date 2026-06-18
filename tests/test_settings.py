import os
import unittest
from unittest.mock import patch

import main


class SettingsTests(unittest.TestCase):
    def test_get_setting_prefers_environment_value(self):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "env-key"}, clear=False):
            self.assertEqual(main.get_setting("GOOGLE_API_KEY"), "env-key")

    def test_get_setting_returns_default_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(main.get_setting("MISSING_KEY", "fallback"), "fallback")

    def test_apply_settings_to_environment_copies_known_secret_values(self):
        with patch.dict(os.environ, {}, clear=True):
            main.apply_settings_to_environment(
                {
                    "LANGSMITH_TRACING": "true",
                    "LANGSMITH_API_KEY": "smith-key",
                    "LANGSMITH_PROJECT": "bulls-and-cows-agent",
                    "LANGSMITH_ENDPOINT": "https://eu.api.smith.langchain.com",
                    "GOOGLE_API_KEY": "gemini-key",
                    "NEBIUS_API_KEY": "nebius-key",
                    "NEBIUS_MODEL": "meta-llama/Meta-Llama-3.1-70B-Instruct",
                }
            )

            self.assertEqual(os.environ["LANGSMITH_TRACING"], "true")
            self.assertEqual(os.environ["LANGSMITH_API_KEY"], "smith-key")
            self.assertEqual(os.environ["LANGSMITH_ENDPOINT"], "https://eu.api.smith.langchain.com")
            self.assertEqual(os.environ["GOOGLE_API_KEY"], "gemini-key")
            self.assertEqual(os.environ["NEBIUS_API_KEY"], "nebius-key")
            self.assertEqual(os.environ["NEBIUS_MODEL"], "meta-llama/Meta-Llama-3.1-70B-Instruct")

    def test_llm_settings_prefer_nebius_over_gemini(self):
        with patch.dict(
            os.environ,
            {
                "NEBIUS_API_KEY": "nebius-key",
                "NEBIUS_MODEL": "nebius-model",
                "GOOGLE_API_KEY": "gemini-key",
            },
            clear=True,
        ):
            settings = main.get_llm_settings()

            self.assertEqual(settings["provider"], "nebius")
            self.assertEqual(settings["api_key"], "nebius-key")
            self.assertEqual(settings["model"], "nebius-model")

    def test_apply_settings_to_environment_keeps_existing_environment_value(self):
        with patch.dict(os.environ, {"LANGSMITH_PROJECT": "from-env"}, clear=True):
            main.apply_settings_to_environment({"LANGSMITH_PROJECT": "from-secrets"})

            self.assertEqual(os.environ["LANGSMITH_PROJECT"], "from-env")


if __name__ == "__main__":
    unittest.main()
