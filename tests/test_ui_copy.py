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

    def test_clue_board_html_is_not_indented_as_code_block(self):
        html = main.build_clue_board_html(
            [
                {"turn": 1, "guess": "102", "response": "0 bulls, 1 cow"},
                {"turn": 2, "guess": "103", "response": "0 bulls, 0 cows"},
            ]
        )

        self.assertIn('<div class="clue-row">', html)
        self.assertIn("102", html)
        self.assertNotIn("\n        <div", html)

    def test_llm_status_copy_explains_missing_streamlit_secret(self):
        message = main.format_llm_status_message(
            configured=False,
            result={"source": "deterministic"},
        )

        self.assertIn("local Ollama", message)
        self.assertIn("NEBIUS_API_KEY", message)

    def test_llm_status_copy_surfaces_runtime_errors(self):
        message = main.format_llm_status_message(
            configured=True,
            result={"source": "fallback", "error": "invalid api key"},
        )

        self.assertIn("LLM error", message)
        self.assertIn("invalid api key", message)


if __name__ == "__main__":
    unittest.main()
