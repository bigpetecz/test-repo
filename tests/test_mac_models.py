import unittest


class NormalizeMacTypeTests(unittest.TestCase):
    def test_normalize_mac_type_returns_canonical_name_for_supported_models(self):
        from modules.scrap.mac_models import normalize_mac_type

        cases = {
            "MacBook Air": "MacBook Air",
            "MacBook Pro": "MacBook Pro",
            "Mac mini": "Mac mini",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalize_mac_type(raw), expected)

    def test_normalize_mac_type_trims_whitespace_and_ignores_case(self):
        from modules.scrap.mac_models import normalize_mac_type

        cases = {
            "  macbook air  ": "MacBook Air",
            "MACBOOK PRO": "MacBook Pro",
            "\tmac MINI\n": "Mac mini",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalize_mac_type(raw), expected)

    def test_normalize_mac_type_raises_value_error_for_unsupported_models(self):
        from modules.scrap.mac_models import normalize_mac_type

        for raw in ["iMac", "MacBook", "Mac Pro", "Mac studio", "", "   "]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                normalize_mac_type(raw)


if __name__ == "__main__":
    unittest.main()
