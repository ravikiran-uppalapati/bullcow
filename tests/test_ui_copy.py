import unittest

import main


class UiCopyTests(unittest.TestCase):
    def test_coach_chat_copy_uses_one_clear_coach_entry_point(self):
        copy = main.get_gemini_chat_copy()

        self.assertEqual(copy["title"], "Ask Coach")
        self.assertEqual(copy["question_label"], "Ask Coach")
        self.assertEqual(copy["secret_label"], "Optional secret number")
        self.assertEqual(copy["submit_label"], "Ask Coach")
        self.assertNotIn("Gemini", copy["title"])

    def test_main_screen_hides_advanced_agent_details_by_default(self):
        self.assertFalse(main.should_show_agent_toolbelt_on_main_screen())


if __name__ == "__main__":
    unittest.main()
