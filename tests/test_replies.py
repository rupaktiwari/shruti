import unittest

from app.services.replies import empty_notebook_reply, language_rule, missing_source_reply


class ReplyTests(unittest.TestCase):
    def test_language_follows_script(self):
        self.assertIn("Nepali", language_rule("नमस्ते"))
        self.assertIn("English", language_rule("hello"))

    def test_empty_notebook_is_specific(self):
        self.assertIn("कागजात", empty_notebook_reply("यो के हो"))
        self.assertIn("no documents", empty_notebook_reply("what is here").lower())

    def test_missing_source_does_not_invent(self):
        self.assertIn("this notebook", missing_source_reply("price").lower())
        self.assertIn("भेटिएन", missing_source_reply("मूल्य कति"))


if __name__ == "__main__":
    unittest.main()
