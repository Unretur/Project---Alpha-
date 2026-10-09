import unittest

from src.ingestion.upstox.options import select_atm_call_put


class OptionSelectionTests(unittest.TestCase):
    def test_selects_closest_strike_with_both_option_types(self):
        contracts = [
            {"strike_price": 25000, "instrument_type": "CE", "trading_symbol": "A"},
            {"strike_price": 25000, "instrument_type": "PE", "trading_symbol": "B"},
            {"strike_price": 25050, "instrument_type": "CE", "trading_symbol": "C"},
            {"strike_price": 25050, "instrument_type": "PE", "trading_symbol": "D"},
            {"strike_price": 25100, "instrument_type": "CE", "trading_symbol": "E"},
        ]

        call, put = select_atm_call_put(contracts, 25040)

        self.assertEqual(call["trading_symbol"], "C")
        self.assertEqual(put["trading_symbol"], "D")

    def test_rejects_no_complete_call_put_pair(self):
        with self.assertRaisesRegex(ValueError, "both a CE and a PE"):
            select_atm_call_put(
                [{"strike_price": 25000, "instrument_type": "CE"}],
                25000,
            )


if __name__ == "__main__":
    unittest.main()
