import unittest

import main


class UiCopyTests(unittest.TestCase):
    def test_gemini_chat_copy_separates_chat_from_optional_calculator(self):
        copy = main.get_gemini_chat_copy()

        self.assertEqual(copy["question_label"], "Ask Gemini anything")
        self.assertEqual(copy["optional_section"], "Optional: calculate bulls/cows")
        self.assertEqual(copy["secret_label"], "Your secret number for exact scoring")
        self.assertEqual(copy["submit_label"], "Send to Gemini")


if __name__ == "__main__":
    unittest.main()
