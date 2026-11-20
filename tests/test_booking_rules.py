import unittest
from datetime import date

from app.services.booking_rules import (
    ROOM_CAPACITY,
    normalize_room_type,
    parse_iso_date,
    stays_overlap,
)


class BookingRulesTest(unittest.TestCase):
    def test_room_type_aliases(self):
        self.assertEqual(normalize_room_type("Deluxe Room"), "deluxe")
        self.assertEqual(normalize_room_type("suite"), "suite")
        self.assertIsNone(normalize_room_type("villa"))

    def test_iso_dates(self):
        self.assertEqual(parse_iso_date("2026-12-15"), date(2026, 12, 15))
        self.assertIsNone(parse_iso_date("15 Dec"))

    def test_overlap(self):
        self.assertTrue(
            stays_overlap(date(2026, 12, 12), date(2026, 12, 15), date(2026, 12, 14), date(2026, 12, 18))
        )
        self.assertFalse(
            stays_overlap(date(2026, 12, 12), date(2026, 12, 15), date(2026, 12, 15), date(2026, 12, 18))
        )

    def test_capacity_matches_the_published_rooms(self):
        self.assertEqual(ROOM_CAPACITY["standard"], 2)
        self.assertEqual(ROOM_CAPACITY["suite"], 4)


if __name__ == "__main__":
    unittest.main()
