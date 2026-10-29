import secrets
import string
import hashlib
from urllib.parse import quote, urlparse
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from .models import Link, ClickLog


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
    encoded_url = quote(short_url, safe='')
    return f'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_url}'


def validate_target_url(original_url: str) -> str:
    """Returns a normalized URL after enforcing supported web protocols."""
    if not isinstance(original_url, str):
        raise ValueError('Target URL must be a string')

    normalized = original_url.strip()
    if not normalized or any(character.isspace() for character in normalized):
        raise ValueError('Target URL must be valid HTTP or HTTPS')

    try:
        parsed = urlparse(normalized)
        hostname = parsed.hostname
    except ValueError:
        raise ValueError('Target URL is malformed')
    if parsed.scheme.lower() not in ('http', 'https') or not parsed.netloc or not hostname:
        raise ValueError('URL must use http:// or https://')
    if parsed.username or parsed.password:
        raise ValueError('Target URL must not include credentials')
    return normalized


def create_link(original_url: str, custom_slug: str = None) -> Link:
    """Creates a new shortened link with optional custom slug."""
    original_url = validate_target_url(original_url)
    slug = (custom_slug or '').strip()
    if not slug:
        slug = generate_random_slug(6)

    # Verify if an active link already uses this slug
    existing = Link.objects.filter(short_code=slug, is_deleted=False).exists()
    if existing:
        raise ValueError(f"Slug '{slug}' is already in use")

    link = Link.objects.create(
        original_url=original_url.strip(),
        short_code=slug,
        clicks=0,
        unique_clicks=0,
        is_deleted=False
    )
    return link


def get_links(page: int = 1, limit: int = 10, include_deleted: bool = False) -> dict:
    """Returns paginated links along with pagination metadata."""
    offset = max(0, (page - 1) * limit)
    qs = Link.objects.filter(is_deleted=include_deleted).order_by('-id')
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
    if referrer:
        try:
            parsed = urlparse(referrer)
            clean_referrer = parsed.netloc or referrer
        except Exception:
            clean_referrer = 'direct'

    ip_hash = 'unknown'
    if ip:
        ip_hash = hashlib.sha256(ip.encode('utf-8')).hexdigest()[:16]

    # Check if this IP has clicked this link before
    prior_click = ClickLog.objects.filter(link_id=link_id, ip_hash=ip_hash).exists()
    is_unique = not prior_click

    ClickLog.objects.create(
        link_id=link_id,
        referrer=clean_referrer,
        user_agent=user_agent or '',
        ip_hash=ip_hash
    )

    link = Link.objects.get(id=link_id)
    link.clicks += 1
    if is_unique:
        link.unique_clicks += 1
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
        link = Link.objects.get(id=link_id)
        if Link.objects.filter(short_code=link.short_code, is_deleted=False).exclude(id=link.id).exists():
            raise ValueError("Slug is already in use by an active link")
        link.is_deleted = False
        link.save(update_fields=['is_deleted', 'updated_at'])
        return link
    except Link.DoesNotExist:
        raise ValueError("Link not found")


def get_global_stats() -> dict:
    """Computes aggregate statistics across active links and click analytics."""
    active_qs = Link.objects.filter(is_deleted=False)
    summary = active_qs.aggregate(
        total_links=Count('id'),
        total_clicks=Coalesce(Sum('clicks'), 0),
        total_unique_clicks=Coalesce(Sum('unique_clicks'), 0)
    )

    top_referrers = list(
        ClickLog.objects.values('referrer')
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
