import secrets
import string
import hashlib
import re
from urllib.parse import quote, urlparse
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError, transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce
from .models import Link, ClickLog


class InvalidTargetUrl(ValueError):
    """Raised when a target URL is not a valid HTTP or HTTPS URL."""


class InvalidSlug(ValueError):
    """Raised when a custom short code has an invalid value or format."""


def generate_random_slug(length: int = 6) -> str:
    """Generate a random alphanumeric slug of specified length."""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def calculate_conversion_rate(unique_clicks: int, total_clicks: int) -> float:
    """Calculates percentage of unique clicks to total clicks."""
    if total_clicks == 0:
        return 0.0
    return round((unique_clicks / total_clicks) * 10000) / 100.0


def get_qr_code_url(short_url: str) -> str:
    """Generates QR code image URL for a given short URL."""
    if not short_url:
        return ''
    return (
        'https://api.qrserver.com/v1/create-qr-code/'
        f'?size=180x180&data={quote(short_url, safe="")}'
    )


def create_link(original_url: str, custom_slug: str = None) -> Link:
    """Creates a new shortened link with optional custom slug."""
    if not isinstance(original_url, str):
        raise InvalidTargetUrl('URL must be a valid HTTP or HTTPS URL')
    original_url = original_url.strip()
    try:
        URLValidator(schemes=['http', 'https'])(original_url)
    except (ValidationError, TypeError) as exc:
        raise InvalidTargetUrl(
            'URL must be a valid HTTP or HTTPS URL'
        ) from exc

    if custom_slug is not None and not isinstance(custom_slug, str):
        raise InvalidSlug('Slug must contain only lowercase letters, numbers, hyphens, or underscores')
    slug = custom_slug.strip() if custom_slug is not None else ''
    custom_slug_provided = bool(slug)
    if custom_slug_provided:
        if len(slug) > 64:
            raise InvalidSlug('Slug must be 64 characters or fewer')
        if re.fullmatch(r'[a-z0-9_-]+', slug) is None:
            raise InvalidSlug('Slug must contain only lowercase letters, numbers, hyphens, or underscores')

    attempts = 1 if custom_slug_provided else 5
    for _ in range(attempts):
        candidate = slug if custom_slug_provided else generate_random_slug(6)
        if Link.objects.filter(short_code=candidate, is_deleted=False).exists():
            if custom_slug_provided:
                raise ValueError(f"Slug '{candidate}' is already in use")
            continue

        try:
            with transaction.atomic():
                return Link.objects.create(
                    original_url=original_url,
                    short_code=candidate,
                    clicks=0,
                    unique_clicks=0,
                    is_deleted=False
                )
        except IntegrityError:
            if not Link.objects.filter(short_code=candidate, is_deleted=False).exists():
                raise
            if custom_slug_provided:
                raise ValueError(f"Slug '{candidate}' is already in use")

    raise RuntimeError('Could not generate an available short code')


def get_links(
    page: int = 1,
    limit: int = 10,
    include_deleted: bool = False,
    search: str = ''
) -> dict:
    """Returns paginated links along with pagination metadata."""
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('Page must be a positive integer')
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError('Limit must be a positive integer')
    if not isinstance(search, str):
        raise ValueError('Search must be a string')

    offset = (page - 1) * limit
    qs = Link.objects.filter(is_deleted=include_deleted).order_by('-id')
    if search:
        qs = qs.filter(
            Q(short_code__icontains=search) |
            Q(original_url__icontains=search)
        )
    total = qs.count()
    links_page = qs[offset:offset + limit]

    data = [link.to_dict() for link in links_page]
    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    return {
        'data': data,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'totalPages': total_pages
        }
    }


def get_link_by_id(link_id: int) -> Link:
    try:
        return Link.objects.get(id=link_id)
    except Link.DoesNotExist:
        return None


def get_link_by_short_code(short_code: str) -> Link:
    try:
        return Link.objects.get(short_code=short_code, is_deleted=False)
    except Link.DoesNotExist:
        return None


def record_click(link_id: int, referrer: str = None, ip: str = None, user_agent: str = None):
    """Logs a click and increments click and unique click counts."""
    clean_referrer = 'direct'
    if isinstance(referrer, str) and referrer:
        try:
            parsed = urlparse(referrer)
            clean_referrer = (parsed.netloc or referrer)[:255]
        except ValueError:
            clean_referrer = 'direct'

    ip_hash = 'unknown'
    if ip:
        ip_hash = hashlib.sha256(ip.encode('utf-8')).hexdigest()[:16]

    with transaction.atomic():
        link = Link.objects.select_for_update().get(id=link_id)
        prior_click = (
            ClickLog.objects.filter(link_id=link_id, ip_hash=ip_hash).exists()
            if ip else False
        )
        is_unique = not prior_click

        ClickLog.objects.create(
            link=link,
            referrer=clean_referrer,
            user_agent=user_agent or '',
            ip_hash=ip_hash
        )

        link.clicks = F('clicks') + 1
        link.unique_clicks = F('unique_clicks') + int(is_unique)
        link.save(update_fields=['clicks', 'unique_clicks', 'updated_at'])


def delete_link(link_id: int) -> bool:
    """Soft-deletes / archives a link by ID."""
    try:
        link = Link.objects.get(id=link_id)
        link.is_deleted = True
        link.save(update_fields=['is_deleted', 'updated_at'])
        return True
    except Link.DoesNotExist:
        return False


def restore_link(link_id: int) -> Link:
    """Restores an archived link back to active status."""
    try:
        with transaction.atomic():
            link = Link.objects.select_for_update().get(id=link_id)
            slug_in_use = Link.objects.filter(
                short_code=link.short_code,
                is_deleted=False
            ).exclude(id=link.id).exists()
            if slug_in_use:
                raise ValueError(f"Slug '{link.short_code}' is already in use")

            link.is_deleted = False
            link.save(update_fields=['is_deleted', 'updated_at'])
            return link
    except Link.DoesNotExist:
        raise ValueError("Link not found")
    except IntegrityError as exc:
        link = Link.objects.get(id=link_id)
        if Link.objects.filter(
            short_code=link.short_code,
            is_deleted=False
        ).exclude(id=link.id).exists():
            raise ValueError(f"Slug '{link.short_code}' is already in use") from exc
        raise


def get_global_stats() -> dict:
    """Computes aggregate statistics across active links and click analytics."""
    active_qs = Link.objects.filter(is_deleted=False)
    summary = active_qs.aggregate(
        total_links=Count('id'),
        total_clicks=Coalesce(Sum('clicks'), 0),
        total_unique_clicks=Coalesce(Sum('unique_clicks'), 0)
    )

    top_referrers = list(
        ClickLog.objects.filter(link__is_deleted=False).values('referrer')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    total_clicks = summary['total_clicks']
    total_unique = summary['total_unique_clicks']
    avg_conversion = calculate_conversion_rate(total_unique, total_clicks)

    return {
        'totalLinks': summary['total_links'],
        'totalClicks': total_clicks,
        'totalUniqueClicks': total_unique,
        'averageConversionRate': avg_conversion,
        'topReferrers': top_referrers
    }
