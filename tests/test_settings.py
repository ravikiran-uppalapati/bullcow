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


if __name__ == "__main__":
    unittest.main()
