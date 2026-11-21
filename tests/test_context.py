import unittest

from app.services.context import format_context


class ContextTests(unittest.TestCase):
    def test_labels_and_dedupes_citations(self):
        text, citations = format_context(
            [
                {"document_id": 1, "filename": "notes.txt", "chunk_index": 0, "text": "Alpha"},
                {"document_id": 1, "filename": "notes.txt", "chunk_index": 0, "text": "Alpha again"},
                {"document_id": 2, "filename": "rates.pdf", "chunk_index": 3, "text": "Beta"},
            ]
        )
        self.assertIn("[notes.txt #0]", text)
        self.assertIn("Beta", text)
        self.assertEqual(len(citations), 2)
        self.assertEqual(citations[1]["filename"], "rates.pdf")

    def test_empty_hits(self):
        text, citations = format_context([])
        self.assertEqual(text, "")
        self.assertEqual(citations, [])


if __name__ == "__main__":
    unittest.main()
