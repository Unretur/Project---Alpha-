import unittest
from datetime import date

from src.ingestion.upstox.options import select_atm_call_put


class OptionSelectionTests(unittest.TestCase):
    def test_selects_closest_strike_from_nearest_weekly_expiry(self):
        contracts = [
            # An already-expired pair must be ignored.
            {"expiry": "2026-10-08", "weekly": True, "strike_price": 25000, "instrument_type": "CE", "trading_symbol": "OLD-C"},
            {"expiry": "2026-10-08", "weekly": True, "strike_price": 25000, "instrument_type": "PE", "trading_symbol": "OLD-P"},
            # Nearest eligible weekly expiry.
            {"expiry": "2026-10-15", "weekly": True, "strike_price": 25000, "instrument_type": "CE", "trading_symbol": "A"},
            {"expiry": "2026-10-15", "weekly": True, "strike_price": 25000, "instrument_type": "PE", "trading_symbol": "B"},
            {"expiry": "2026-10-15", "weekly": True, "strike_price": 25050, "instrument_type": "CE", "trading_symbol": "C"},
            {"expiry": "2026-10-15", "weekly": True, "strike_price": 25050, "instrument_type": "PE", "trading_symbol": "D"},
            # Further-out expiry must not be mixed into the pair.
            {"expiry": "2026-10-29", "weekly": True, "strike_price": 25050, "instrument_type": "CE", "trading_symbol": "FAR-C"},
            {"expiry": "2026-10-29", "weekly": True, "strike_price": 25050, "instrument_type": "PE", "trading_symbol": "FAR-P"},
            # A closer non-weekly pair should not override the weekly expiry.
            {"expiry": "2026-10-12", "weekly": False, "strike_price": 25050, "instrument_type": "CE", "trading_symbol": "MONTHLY-C"},
            {"expiry": "2026-10-12", "weekly": False, "strike_price": 25050, "instrument_type": "PE", "trading_symbol": "MONTHLY-P"},
        ]

        call, put = select_atm_call_put(
            contracts, 25040, as_of_date=date(2026, 10, 9)
        )

        self.assertEqual(call["trading_symbol"], "C")
        self.assertEqual(put["trading_symbol"], "D")
        self.assertEqual(call["expiry"], "2026-10-15")

    def test_rejects_no_complete_call_put_pair(self):
        with self.assertRaisesRegex(ValueError, "No CE/PE pair"):
            select_atm_call_put(
                [
                    {"expiry": "2026-10-15", "weekly": True,
                     "strike_price": 25000, "instrument_type": "CE"}
                ],
                25000,
                as_of_date=date(2026, 10, 9),
            )

    def test_rejects_missing_weekly_metadata(self):
        with self.assertRaisesRegex(ValueError, "lacks a weekly flag"):
            select_atm_call_put(
                [
                    {"expiry": "2026-10-15", "strike_price": 25000, "instrument_type": "CE"},
                    {"expiry": "2026-10-15", "strike_price": 25000, "instrument_type": "PE"},
                ],
                25000,
                as_of_date=date(2026, 10, 9),
            )


if __name__ == "__main__":
    unittest.main()
