import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from links.models import Link, ClickLog


class Command(BaseCommand):
    help = 'Seeds sample short links and click telemetry logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing links and click logs before seeding.',
        )

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample LinkSnip data...")

        now = timezone.now()

        sample_links = [
            {
                'url': 'https://github.com/trending',
                'code': 'gh-trend',
                'clicks': 24,
                'unique': 18,
                'days_ago': 5,
                'is_deleted': False,
                'referrers': ['github.com', 'twitter.com', 'direct']
            },
            {
                'url': 'https://news.ycombinator.com',
                'code': 'hn-front',
                'clicks': 142,
                'unique': 98,
                'days_ago': 4,
                'is_deleted': False,
                'referrers': ['hackernews.com', 'linkedin.com', 'direct']
            },
            {
                'url': 'https://docs.djangoproject.com',
                'code': 'dj-docs',
                'clicks': 65,
                'unique': 45,
                'days_ago': 3,
                'is_deleted': False,
                'referrers': ['google.com', 'direct']
            },
            {
                'url': 'https://python.org',
                'code': 'py-lang',
                'clicks': 88,
                'unique': 60,
                'days_ago': 2,
                'is_deleted': False,
                'referrers': ['twitter.com', 'reddit.com']
            },
            {
                'url': 'https://sqlite.org',
                'code': 'sqlite-db',
                'clicks': 12,
                'unique': 8,
                'days_ago': 1,
                'is_deleted': False,
                'referrers': ['google.com']
            },
            {
                'url': 'https://xops.club',
                'code': 'xops-club',
                'clicks': 40,
                'unique': 28,
                'days_ago': 0,
                'is_deleted': False,
                'referrers': ['twitter.com', 'direct']
            },
            {
                'url': 'https://stackoverflow.com',
                'code': 'so-hub',
                'clicks': 52,
                'unique': 35,
                'days_ago': 0,
                'is_deleted': True,
                'referrers': ['google.com', 'github.com']
            },
            {
                'url': 'https://github.com/XOps-Club/Prompt2Patch',
                'code': 'p2p-hack',
                'clicks': 19,
                'unique': 14,
                'days_ago': 0,
                'is_deleted': False,
                'referrers': ['direct', 'twitter.com']
            }
        ]

        created_count = 0
        with transaction.atomic():
            if options['reset']:
                ClickLog.objects.all().delete()
                Link.objects.all().delete()

            for item in sample_links:
                created_at = now - datetime.timedelta(days=item['days_ago'])
                link, created = Link.objects.get_or_create(
                    short_code=item['code'],
                    defaults={
                        'original_url': item['url'],
                        'clicks': item['clicks'],
                        'unique_clicks': item['unique'],
                        'is_deleted': item['is_deleted'],
                    }
                )

                if not created:
                    continue

                created_count += 1
                Link.objects.filter(id=link.id).update(created_at=created_at)

                for i in range(item['clicks']):
                    ref = item['referrers'][i % len(item['referrers'])]
                    ClickLog.objects.create(
                        link=link,
                        referrer=ref,
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        ip_hash=f'ip_sample_{i % 10}'
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_count} new links; existing links and logs were preserved."
            )
        )
