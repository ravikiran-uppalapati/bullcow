import os
import unittest

from bulls_cows.runtime_config import apply_runtime_config


class RuntimeConfigTests(unittest.TestCase):
    def setUp(self):
        self.original = {
            key: os.environ.get(key)
            for key in [
                "GOOGLE_API_KEY",
                "LANGSMITH_API_KEY",
                "LANGSMITH_TRACING",
                "LANGSMITH_PROJECT",
                "LANGSMITH_ENDPOINT",
            ]
        }

    def tearDown(self):
        for key, value in self.original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_apply_runtime_config_sets_only_provided_values(self):
        apply_runtime_config(
            {
                "google_api_key": "gemini-key",
                "langsmith_api_key": "smith-key",
                "langsmith_project": "demo-project",
                "langsmith_endpoint": "https://eu.api.smith.langchain.com",
            }
        )

        self.assertEqual(os.environ["GOOGLE_API_KEY"], "gemini-key")
        self.assertEqual(os.environ["LANGSMITH_API_KEY"], "smith-key")
        self.assertEqual(os.environ["LANGSMITH_TRACING"], "true")
        self.assertEqual(os.environ["LANGSMITH_PROJECT"], "demo-project")
        self.assertEqual(os.environ["LANGSMITH_ENDPOINT"], "https://eu.api.smith.langchain.com")

    def test_apply_runtime_config_ignores_blank_values(self):
        os.environ["GOOGLE_API_KEY"] = "existing"

        apply_runtime_config({"google_api_key": "   "})

        self.assertEqual(os.environ["GOOGLE_API_KEY"], "existing")


if __name__ == "__main__":
    unittest.main()
