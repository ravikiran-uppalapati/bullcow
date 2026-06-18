import unittest

import main


class UiCopyTests(unittest.TestCase):
    def test_coach_chat_copy_uses_one_clear_coach_entry_point(self):
        copy = main.get_gemini_chat_copy()

        self.assertEqual(copy["title"], "Ask Coach")
        self.assertEqual(copy["question_label"], "Ask Coach")
        self.assertEqual(copy["submit_label"], "Ask Coach")
        self.assertNotIn("Gemini", copy["title"])
        self.assertNotIn("secret_label", copy)

    def test_main_screen_hides_advanced_agent_details_by_default(self):
        self.assertFalse(main.should_show_agent_toolbelt_on_main_screen())

    def test_gemini_status_copy_explains_missing_streamlit_secret(self):
        message = main.format_gemini_status_message(
            configured=False,
            result={"source": "deterministic"},
        )

        self.assertIn("Streamlit secrets", message)
        self.assertIn("GOOGLE_API_KEY", message)

    def test_gemini_status_copy_surfaces_runtime_errors(self):
        message = main.format_gemini_status_message(
            configured=True,
            result={"source": "fallback", "error": "invalid api key"},
        )

        self.assertIn("Gemini error", message)
        self.assertIn("invalid api key", message)


if __name__ == "__main__":
    unittest.main()
