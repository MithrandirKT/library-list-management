"""
Regression tests for end-to-end scenarios.
Tests the full policy-driven flow: field_policy + quality_gates + wikidata + router + status/checkpoint.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from kitap_bilgisi_cekici import KitapBilgisiCekici
from field_registry import ensure_row_schema
from provenance import set_row_status


class TestWarAndPeaceScenario(unittest.TestCase):
    """Test War and Peace scenario - classic book with common issues"""

    def setUp(self):
        """Set up test fixtures"""
        self.cekici = KitapBilgisiCekici()
        self.kitap_adi = "Savaş ve Barış"
        self.yazar = "Lev Tolstoy"

    def test_war_and_peace_quality_gates_integration(self):
        """Test quality gates integration for War and Peace scenario"""
        # This test verifies that quality gates work correctly
        # without making actual API calls
        from quality_gates import gate_publication_year, gate_original_title

        # Test 1: TR Wikipedia with translation context - should reject
        context = {
            "source": "trwiki",
            "extract": "turkceye cevrildi",
        }
        ok, reason = gate_publication_year("2000", context)
        self.assertFalse(ok, f"Should reject translation context, but got: {reason}")

        # Test 2: Volume marker in original title - should reject
        context = {"localized_title": "Savaş ve Barış"}
        ok, reason = gate_original_title("Savaş ve Barış 1. Cilt", context)
        self.assertFalse(ok, f"Should reject volume marker, but got: {reason}")

        # Test 3: Google Books edition date for classic - should reject
        context = {
            "source": "gbooks",
            "localized_title": "War and Peace",
            "author": "Leo Tolstoy",
        }
        ok, reason = gate_publication_year("2010", context)
        self.assertFalse(ok, f"Should reject edition date for classic, but got: {reason}")

        # Test 4: Valid original title (Cyrillic) - should accept
        context = {"localized_title": "Savaş ve Barış"}
        ok, reason = gate_original_title("Война и мир", context)
        self.assertTrue(ok, f"Should accept Cyrillic original title, but got: {reason}")

        # Test 5: Valid publication year from EN Wikipedia - should accept
        context = {
            "source": "enwiki",
            "extract": "First published in 1869",
        }
        ok, reason = gate_publication_year("1869", context)
        self.assertTrue(ok, f"Should accept valid publication year, but got: {reason}")



class TestCommonProblems(unittest.TestCase):
    """Test common problems and edge cases"""

    def setUp(self):
        """Set up test fixtures"""
        self.cekici = KitapBilgisiCekici()

    def test_empty_input(self):
        """Test handling of empty input"""
        mevcut = ensure_row_schema({})
        result = self.cekici.kitap_bilgisi_cek_policy("", "", mevcut)
        
        self.assertIn('status', result)
        # Empty input should result in FAIL or PARTIAL status
        self.assertIn(result['status'], ['FAIL', 'PARTIAL'])

    def test_partial_data_scenario(self):
        """Test scenario where only some fields are found"""
        mevcut = ensure_row_schema({
            "Kitap Adı": "Test Book",
            "Yazar": "Test Author",
            "Orijinal Adı": "",  # Missing
            "Tür": "Roman",  # Found
            "İlk Yayınlanma Tarihi": "",  # Missing
        })
        
        # Status should reflect partial data
        set_row_status(
            mevcut,
            status="PARTIAL",
            missing_fields=["Orijinal Adı", "İlk Yayınlanma Tarihi"],
            best_source="test"
        )
        
        self.assertEqual(mevcut['status'], 'PARTIAL')
        self.assertIn('Orijinal Adı', mevcut['missing_fields'])
        self.assertIn('İlk Yayınlanma Tarihi', mevcut['missing_fields'])

    def test_complete_data_scenario(self):
        """Test scenario where all fields are found"""
        mevcut = ensure_row_schema({
            "Kitap Adı": "Test Book",
            "Yazar": "Test Author",
            "Orijinal Adı": "Test Original",
            "Tür": "Roman",
            "İlk Yayınlanma Tarihi": "2020",
        })
        
        set_row_status(
            mevcut,
            status="OK",
            missing_fields=[],
            best_source="test"
        )
        
        self.assertEqual(mevcut['status'], 'OK')
        self.assertEqual(mevcut['missing_fields'], '')

    def test_status_written(self):
        """Test that status is written correctly"""
        mevcut = ensure_row_schema({})
        set_row_status(
            mevcut,
            status="OK",
            missing_fields=[],
            best_source="test",
            retry_count=0
        )
        
        self.assertEqual(mevcut['status'], 'OK')
        self.assertEqual(mevcut['missing_fields'], '')
        self.assertEqual(mevcut['best_source'], 'test')
        self.assertEqual(mevcut['retry_count'], '0')
        self.assertIn('last_attempt_at', mevcut)

    def test_retry_logic(self):
        """Test retry logic with next_retry_at"""
        from datetime import datetime, timedelta
        
        mevcut = ensure_row_schema({})
        set_row_status(
            mevcut,
            status="FAIL",
            missing_fields=["Orijinal Adı"],
            best_source="error",
            retry_count=1,
            next_retry_hours=6
        )
        
        self.assertEqual(mevcut['status'], 'FAIL')
        self.assertIn('next_retry_at', mevcut)
        
        # Check that next_retry_at is in the future
        next_retry = datetime.fromisoformat(mevcut['next_retry_at'].replace('Z', '+00:00'))
        now = datetime.utcnow()
        self.assertGreater(next_retry, now)

    def test_ensure_row_schema(self):
        """Test that ensure_row_schema adds all required columns"""
        row = {"Kitap Adı": "Test", "Yazar": "Test Author"}
        result = ensure_row_schema(row)
        
        # Check that all standard columns exist
        from field_registry import standard_columns
        for col in standard_columns():
            self.assertIn(col, result, f"Column {col} missing")

    def test_provenance_tracking(self):
        """Test that provenance is tracked correctly"""
        from provenance import set_field
        
        row = ensure_row_schema({})
        set_field(row, "Orijinal Adı", "Test Title", "enwiki", 0.9)
        
        self.assertEqual(row['Orijinal Adı'], 'Test Title')
        self.assertEqual(row['src_orijinal_adi'], 'enwiki')
        self.assertEqual(row['conf_orijinal_adi'], '0.90')


class TestRouterIntegration(unittest.TestCase):
    """Test router integration with quota management"""

    def setUp(self):
        """Set up test fixtures"""
        self.cekici = KitapBilgisiCekici()

    def test_router_state_management(self):
        """Test that router manages provider states correctly"""
        from router import QuotaRouter, ProviderState
        
        router = QuotaRouter()
        state = router._state("test_provider")
        
        self.assertIsInstance(state, ProviderState)
        self.assertTrue(state.available())
        
        # Test cooldown
        state.cooldown(10)
        self.assertFalse(state.available())
        
        # Test mark_dead
        state.mark_dead()
        self.assertFalse(state.available())

    def test_router_rate_limit_handling(self):
        """Test that router handles rate limits correctly"""
        from router import QuotaRouter
        
        router = QuotaRouter()
        
        # Simulate rate limit (429)
        def rate_limited_call():
            return None, 429
        
        result = router.call("test", rate_limited_call)
        self.assertIsNone(result)
        
        # Provider should be in cooldown
        state = router._state("test")
        self.assertFalse(state.available())


class TestFieldPolicyIntegration(unittest.TestCase):
    """Test field policy integration"""

    def test_field_policy_build_rules(self):
        """Test that field policy builds rules correctly"""
        from field_policy import build_rules
        
        rules = build_rules()
        
        # Check that rules exist for expected fields
        expected_fields = [
            "Orijinal Adı",
            "Tür",
            "Ülke/Edebi Gelenek",
            "İlk Yayınlanma Tarihi",
            "Anlatı Yılı",
            "Konusu"
        ]
        
        for field in expected_fields:
            self.assertIn(field, rules, f"Rule missing for {field}")
            self.assertIsNotNone(rules[field].sources, f"Sources missing for {field}")

    def test_field_policy_source_priority(self):
        """Test that field policy has correct source priority"""
        from field_policy import build_rules
        
        rules = build_rules()
        
        # Check İlk Yayınlanma Tarihi source priority (should be: openlibrary -> wikidata -> enwiki -> gbooks -> trwiki -> AI)
        cikis_yili_rule = rules.get("İlk Yayınlanma Tarihi")
        self.assertIsNotNone(cikis_yili_rule)
        
        # Open Library should be first
        if len(cikis_yili_rule.sources) > 0:
            self.assertEqual(cikis_yili_rule.sources[0], "openlibrary")


class TestWikidataIntegration(unittest.TestCase):
    """Test Wikidata integration"""

    def test_wikidata_qid_format(self):
        """Test that Wikidata QID format is correct"""
        # QID should start with 'Q' followed by digits
        valid_qids = ["Q12345", "Q1", "Q999999"]
        invalid_qids = ["12345", "Q", "ABC123", ""]
        
        import re
        qid_pattern = re.compile(r'^Q\d+$')
        
        for qid in valid_qids:
            self.assertTrue(qid_pattern.match(qid), f"Valid QID {qid} should match pattern")
        
        for qid in invalid_qids:
            self.assertFalse(qid_pattern.match(qid), f"Invalid QID {qid} should not match pattern")


if __name__ == "__main__":
    unittest.main()
