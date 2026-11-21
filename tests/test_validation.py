import unittest

from fastapi import HTTPException

from app.api.validation import require_message, require_session_id
from app.services.chunking import chunk_text
from app.schemas.document import ChunkingStrategy


class ValidationTests(unittest.TestCase):
    def test_session_id(self):
        self.assertEqual(require_session_id("shruti-abc_1"), "shruti-abc_1")
        with self.assertRaises(HTTPException):
            require_session_id("has space")

    def test_message_bounds(self):
        self.assertEqual(require_message("  hello "), "hello")
        with self.assertRaises(HTTPException):
            require_message("   ")
        with self.assertRaises(HTTPException):
            require_message("x" * 8001)

    def test_chunking_keeps_text(self):
        chunks = chunk_text("Alpha. " * 40, ChunkingStrategy.recursive, chunk_size=80, chunk_overlap=10)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.strip() for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
