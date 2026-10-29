import os
import re
from io import StringIO
from django.conf import settings
from django.db import IntegrityError, transaction
from django.core.management import call_command
from django.test import TestCase, Client
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

    def test_database_rejects_duplicate_active_short_codes(self):
        link = services.create_link(
            'https://example.com/first-active-owner',
            custom_slug='unique-active-slug'
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Link.objects.create(
                    original_url='https://example.com/second-active-owner',
                    short_code=link.short_code
                )

    def test_create_link_rejects_non_http_target_urls(self):
        for url in ('javascript:alert(1)', 'https:///missing-host'):
            with self.subTest(url=url):
                with self.assertRaises(services.InvalidTargetUrl):
                    services.create_link(url)

    def test_create_link_accepts_uppercase_https_scheme(self):
        link = services.create_link('HTTPS://example.com/path')
        self.assertEqual(link.original_url, 'HTTPS://example.com/path')

    def test_create_link_rejects_invalid_custom_slugs(self):
        for slug in ('Uppercase', 'contains space', 'slash/character', 'a' * 65, 123):
            with self.subTest(slug=slug):
                with self.assertRaises(services.InvalidSlug):
                    services.create_link('https://example.com/target', custom_slug=slug)

    def test_create_link_accepts_custom_slugs_using_supported_characters(self):
        link = services.create_link(
            'https://example.com/target',
            custom_slug='valid-slug_123'
        )
        self.assertEqual(link.short_code, 'valid-slug_123')

    def test_records_clicks_and_updates_click_count(self):
        link = services.create_link('https://example.com/click-test')
        services.record_click(link.id, 'https://twitter.com', '127.0.0.1')
        services.record_click(link.id, 'https://twitter.com', '127.0.0.1')
        services.record_click(link.id, 'https://google.com', '192.168.1.1')

        updated = services.get_link_by_id(link.id)
        self.assertEqual(updated.clicks, 3)
        self.assertEqual(updated.unique_clicks, 2)

    def test_clicks_without_ip_are_counted_as_unique(self):
        link = services.create_link('https://example.com/click-without-ip')
        services.record_click(link.id)
        services.record_click(link.id)

        updated = services.get_link_by_id(link.id)
        self.assertEqual(updated.clicks, 2)
        self.assertEqual(updated.unique_clicks, 2)

    def test_calculate_conversion_rate_preserves_fractional_percentages(self):
        rate1 = services.calculate_conversion_rate(7, 10)
        self.assertEqual(rate1, 70.0)

        rate2 = services.calculate_conversion_rate(4, 10)
        self.assertEqual(rate2, 40.0)

        rate3 = services.calculate_conversion_rate(1, 3)
        self.assertTrue(33.0 < rate3 < 34.0, f"Expected ~33.33, got {rate3}")

    def test_page_1_returns_first_batch_of_urls(self):
        for i in range(15):
            services.create_link(f'https://example.com/item-{i}')

        page1 = services.get_links(page=1, limit=10)
        self.assertEqual(len(page1['data']), 10)
        self.assertEqual(page1['pagination']['total'], 15)
        self.assertEqual(page1['pagination']['totalPages'], 2)

    def test_search_filters_before_pagination_by_slug_and_destination(self):
        for i in range(12):
            services.create_link(f'https://example.com/item-{i}')
        target = services.create_link(
            'https://destination.example/search-target',
            custom_slug='search-target'
        )

        slug_results = services.get_links(page=1, limit=1, search='search')
        destination_results = services.get_links(
            page=1,
            limit=1,
            search='destination.example'
        )
        self.assertEqual(slug_results['pagination']['total'], 1)
        self.assertEqual(slug_results['data'][0]['id'], target.id)
        self.assertEqual(destination_results['data'][0]['id'], target.id)

    def test_links_api_returns_bad_request_for_invalid_pagination(self):
        response = Client().get('/links?page=not-a-number')
        self.assertEqual(response.status_code, 400)

    def test_links_api_returns_bad_request_for_invalid_custom_slug(self):
        response = Client().post(
            '/links',
            data={
                'originalUrl': 'https://example.com/target',
                'customSlug': 'Uppercase'
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_links_api_rejects_json_values_that_are_not_objects(self):
        for body in ('null', '[]', '"not an object"'):
            with self.subTest(body=body):
                response = Client().post(
                    '/links',
                    data=body,
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 400)

    def test_links_api_requires_csrf_for_link_creation(self):
        response = Client(enforce_csrf_checks=True).post(
            '/links',
            data={'originalUrl': 'https://example.com/target'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_link_detail_rejects_unsupported_post_method(self):
        link = services.create_link('https://example.com/detail-method')
        response = Client().post(f'/links/{link.id}')
        self.assertEqual(response.status_code, 405)

    def test_pagination_rejects_non_positive_values(self):
        for page, limit in ((0, 10), (1, 0), (1, -1)):
            with self.subTest(page=page, limit=limit):
                with self.assertRaises(ValueError):
                    services.get_links(page=page, limit=limit)


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

    def test_global_referrers_exclude_archived_links(self):
        active = services.create_link('https://example.com/active-referrer')
        archived = services.create_link('https://example.com/archived-referrer')
        Link.objects.filter(id=archived.id).update(is_deleted=True)
        ClickLog.objects.create(link=active, referrer='active.example')
        ClickLog.objects.create(link=archived, referrer='archived.example')

        stats = services.get_global_stats()
        self.assertEqual(
            stats['topReferrers'],
            [{'referrer': 'active.example', 'count': 1}]
        )

    def test_record_click_truncates_long_referrers_to_model_limit(self):
        link = services.create_link('https://example.com/long-referrer')
        referrer = 'https://' + ('a' * 300) + '.example/path'
        services.record_click(link.id, referrer=referrer)
        click = ClickLog.objects.get(link=link)
        self.assertLessEqual(len(click.referrer), 255)

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

    def test_seed_command_preserves_existing_user_data(self):
        link = services.create_link(
            'https://example.com/user-data',
            custom_slug='user-data'
        )
        click = ClickLog.objects.create(link=link, referrer='user.example')

        call_command('seed', stdout=StringIO())

        self.assertTrue(Link.objects.filter(id=link.id).exists())
        self.assertTrue(ClickLog.objects.filter(id=click.id).exists())


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
