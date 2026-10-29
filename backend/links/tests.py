import os
import re
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from links.models import Link, ClickLog
from links import services


class LinkSnipStandardAPITests(TestCase):
    """
    Standard API tests verifying baseline LinkSnip functionality.
    """

    def test_creates_new_short_link_with_auto_generated_slug(self):
        link = services.create_link('https://example.com/unique-test-1')
        self.assertIsNotNone(link)
        self.assertEqual(link.original_url, 'https://example.com/unique-test-1')
        self.assertTrue(bool(link.short_code))
        self.assertEqual(len(link.short_code), 6)
        self.assertFalse(link.is_deleted)

    def test_rejects_duplicate_custom_slugs_on_initial_creation(self):
        slug = 'custom-slug-abc'
        services.create_link('https://example.com/first', custom_slug=slug)

        with self.assertRaises(ValueError, msg="Expected ValueError when reusing an active custom slug"):
            services.create_link('https://example.com/second', custom_slug=slug)

    def test_records_clicks_and_updates_click_count(self):
        link = services.create_link('https://example.com/click-test')
        services.record_click(link.id, 'https://twitter.com', '127.0.0.1')
        services.record_click(link.id, 'https://twitter.com', '127.0.0.1')
        services.record_click(link.id, 'https://google.com', '192.168.1.1')

        updated = services.get_link_by_id(link.id)
        self.assertEqual(updated.clicks, 3)
        self.assertEqual(updated.unique_clicks, 2)

    def test_calculate_conversion_rate_preserves_fractional_percentages(self):
        rate1 = services.calculate_conversion_rate(7, 10)
        self.assertEqual(rate1, 70.0)

        rate2 = services.calculate_conversion_rate(4, 10)
        self.assertEqual(rate2, 40.0)

        rate3 = services.calculate_conversion_rate(1, 3)
        self.assertTrue(33.0 < rate3 < 34.0, f"Expected ~33.33, got {rate3}")

    def test_create_link_rejects_unsupported_url_protocols(self):
        unsupported_urls = [
            'javascript:alert(1)',
            'file:///tmp/linksnip.txt',
            'ftp://example.com/file',
            'data:text/plain,hello',
        ]

        for original_url in unsupported_urls:
            with self.subTest(original_url=original_url):
                with self.assertRaises(ValueError):
                    services.create_link(original_url)

    def test_create_link_accepts_only_well_formed_http_targets(self):
        services.create_link('HTTPS://example.com/secure')

        malformed_urls = [
            'https://',
            'https://user:password@example.com',
            'https://[invalid',
        ]
        for original_url in malformed_urls:
            with self.subTest(original_url=original_url):
                with self.assertRaises(ValueError):
                    services.create_link(original_url)

    def test_page_1_returns_first_batch_of_urls(self):
        for i in range(15):
            services.create_link(f'https://example.com/item-{i}')

        page1 = services.get_links(page=1, limit=10)
        self.assertEqual(len(page1['data']), 10)
        self.assertEqual(page1['pagination']['total'], 15)
        self.assertEqual(page1['pagination']['totalPages'], 2)


class LinkSnipCoreOperationsAndAnalyticsTests(TestCase):
    """
    Core operations, analytics, and lifecycle test suite.
    """

    def setUp(self):
        self.client = Client()

    def test_archives_active_link_on_delete(self):
        """Verifies link archiving lifecycle on deletion."""
        link = services.create_link('https://example.com/delete-test-op')
        success = services.delete_link(link.id)
        self.assertTrue(success, "delete_link should return True")

        updated = Link.objects.get(id=link.id)
        self.assertTrue(updated.is_deleted, "Active link should be archived after delete")

        active_check = services.get_link_by_short_code(link.short_code)
        self.assertIsNone(active_check, "Archived link should not be active via short code lookup")

    def test_restores_archived_link_back_to_active_state(self):
        """Verifies restoring an archived link back to active state."""
        link = services.create_link('https://example.com/restore-test-op')
        Link.objects.filter(id=link.id).update(is_deleted=True)

        restored = services.restore_link(link.id)
        self.assertFalse(restored.is_deleted, "Archived link should be restored to active status")

        active_check = services.get_link_by_short_code(link.short_code)
        self.assertIsNotNone(active_check, "Expected link to be active after restore")

    def test_aggregates_active_links_and_visitor_metrics_in_stats(self):
        """Verifies aggregate telemetry metrics from /links/stats."""
        services.create_link('https://example.com/stats-test-1')
        services.create_link('https://example.com/stats-test-2')

        response = self.client.get('/links/stats')
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIsInstance(data.get('totalClicks'), int, "Expected totalClicks to be an int")
        self.assertIsInstance(data.get('totalUniqueClicks'), int, "Expected totalUniqueClicks to be an int")
        self.assertIsInstance(data.get('totalLinks'), int, "Expected totalLinks metric to be present in telemetry response")
        self.assertGreater(data.get('totalLinks', 0), 0, "Expected active links count to be positive")

    def test_generates_qr_code_url_for_created_links(self):
        """Verifies that QR code URL is generated with proper parameter encoding."""
        test_url = 'https://linksnip.dev/test123'
        qr_url = services.get_qr_code_url(test_url)

        self.assertTrue(bool(qr_url), "Expected valid non-empty QR code URL")
        self.assertTrue(
            'qrserver.com' in qr_url or 'api.qr' in qr_url or 'chart.googleapis' in qr_url or qr_url.startswith('data:image'),
            f"Expected a recognized QR generator URL or data URI, got: {qr_url}"
        )
        self.assertTrue(
            test_url in qr_url or 'test123' in qr_url,
            "Expected QR URL to target destination URL"
        )

    def test_isolates_pagination_total_and_total_pages_between_active_and_archived_views(self):
        """Verifies that active and archived views isolate pagination counts."""
        for i in range(3):
            services.create_link(f'https://example.com/active-{i}')
        for i in range(2):
            l = services.create_link(f'https://example.com/archived-{i}')
            Link.objects.filter(id=l.id).update(is_deleted=True)

        active_res = services.get_links(page=1, limit=10, include_deleted=False)
        self.assertEqual(len(active_res['data']), 3)
        self.assertEqual(active_res['pagination']['total'], 3, "Active view total should only count active links")
        self.assertEqual(active_res['pagination']['totalPages'], 1)

        archived_res = services.get_links(page=1, limit=10, include_deleted=True)
        self.assertEqual(len(archived_res['data']), 2)
        self.assertEqual(archived_res['pagination']['total'], 2, "Archived view total should only count archived links")

    def test_rejects_restoring_archived_link_if_slug_claimed_by_active_link(self):
        """Verifies that restoring an archived link fails if its slug is already claimed by an active link."""
        slug = 'claimed-collision-slug'
        link1 = services.create_link('https://example.com/first-owner', custom_slug=slug)
        Link.objects.filter(id=link1.id).update(is_deleted=True)

        link2 = services.create_link('https://example.com/second-owner', custom_slug=slug)
        self.assertFalse(link2.is_deleted)

        with self.assertRaises(ValueError, msg="Restoring archived link with claimed slug must fail"):
            services.restore_link(link1.id)


class LinkSnipFrontendServiceContractsTests(TestCase):
    """
    Frontend service contract tests (verifying client-side contracts).
    """

    def test_frontend_qr_generator_contract(self):
        """Verifies client-side QR generator helper contract in frontend static assets."""
        js_path = os.path.join(settings.BASE_DIR, '..', 'frontend', 'static', 'js', 'app.js')
        with open(js_path, 'r', encoding='utf-8') as f:
            content = f.read()

        match = re.search(r'function\s+getQrCodeUrl\s*\([^)]*\)\s*\{([\s\S]*?)\n\s*\}', content)
        self.assertIsNotNone(match, "Could not find getQrCodeUrl function in frontend/static/js/app.js")
        fn_body = match.group(1).strip()

        self.assertFalse(
            bool(re.search(r"return\s+['\"]['\"];?\s*$", fn_body)),
            "Frontend getQrCodeUrl must return a functional QR generator endpoint URL"
        )
        self.assertTrue(
            'qrserver.com' in fn_body or 'encodeURIComponent' in fn_body,
            "Expected getQrCodeUrl to return valid QR API endpoint"
        )

    def test_frontend_tab_state_requests_and_renders_correct_lifecycle_actions(self):
        js_path = os.path.join(settings.BASE_DIR, '..', 'frontend', 'static', 'js', 'app.js')
        with open(js_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("const isArchived = activeTab === 'archived';", content)
        self.assertIn('class="btn-secondary restore-link-btn"', content)
        self.assertIn('class="btn-danger-ghost archive-link-btn"', content)
        self.assertIn('function escapeHtml(value)', content)

    def test_create_link_rejects_unsafe_custom_slugs(self):
        unsafe_slugs = ['"><img src=x onerror=alert(1)>', 'spaces not allowed', '../admin', 'slash/route']

        for slug in unsafe_slugs:
            with self.subTest(slug=slug):
                with self.assertRaises(ValueError):
                    services.create_link('https://example.com', custom_slug=slug)
