import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from . import services


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def index_view(request):
    """
    Renders the modern LinkSnip Dashboard.
    Provides initial context for SSR, while client-side JS handles live reactivity.
    """
    stats = services.get_global_stats()
    links_data = services.get_links(page=1, limit=10, include_deleted=False)
    archived_data = services.get_links(page=1, limit=10, include_deleted=True)

    context = {
        'stats': stats,
        'initial_links': links_data['data'],
        'initial_pagination': links_data['pagination'],
        'archived_count': archived_data['pagination']['total'],
    }
    return render(request, 'index.html', context)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def links_collection_api(request):
    """
    Handles GET /links (list links) and POST /links (create short link).
    """
    if request.method == 'GET':
        try:
            page = max(1, int(request.GET.get('page', 1)))
            limit = max(1, min(100, int(request.GET.get('limit', 10))))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'page and limit must be integers'}, status=400)
        include_deleted = request.GET.get('includeDeleted', 'false').lower() == 'true'

        result = services.get_links(page=page, limit=limit, include_deleted=include_deleted)
        return JsonResponse(result)

    elif request.method == 'POST':
        # Accept either JSON body or standard form POST
        data = {}
        if request.content_type == 'application/json' and request.body:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON body'}, status=400)
        else:
            data = request.POST.dict()

        original_url = data.get('originalUrl') or data.get('original_url')
        custom_slug = data.get('customSlug') or data.get('custom_slug')

        if not original_url:
            return JsonResponse({
                'error': 'Validation failed',
                'details': {'originalUrl': ['Target URL is required']}
            }, status=400)

        try:
            link = services.create_link(original_url, custom_slug)
            return JsonResponse(link.to_dict(), status=201)
        except services.LinkValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except services.SlugConflictError as e:
            return JsonResponse({'error': str(e)}, status=409)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def stats_api(request):
    """GET /links/stats - Aggregate metrics"""
    stats = services.get_global_stats()
    return JsonResponse(stats)


@csrf_exempt
@require_http_methods(["GET", "DELETE", "POST"])
def link_detail_api(request, identifier):
    """
    Handles:
    - GET /links/<identifier>
    - DELETE /links/<id> (Archive link)
    """
    if request.method == 'DELETE':
        try:
            link_id = int(identifier)
        except ValueError:
            return JsonResponse({'error': 'Invalid ID'}, status=400)

        success = services.delete_link(link_id)
        if not success:
            return JsonResponse({'error': 'Link not found'}, status=404)
        return JsonResponse({'success': True, 'message': 'Link archived'})

    # If GET: check if integer ID or string shortcode
    try:
        link_id = int(identifier)
        link = services.get_link_by_id(link_id)
        if link is None:
            link = services.get_link_by_short_code(identifier)
    except ValueError:
        link = services.get_link_by_short_code(identifier)

    if not link:
        return JsonResponse({'error': f"Link '{identifier}' not found"}, status=404)

    return JsonResponse(link.to_dict())


@csrf_exempt
@require_http_methods(["POST"])
def restore_link_api(request, link_id):
    """POST /links/<id>/restore - Restores an archived link"""
    try:
        restored = services.restore_link(link_id)
        return JsonResponse(restored.to_dict())
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            return JsonResponse({'error': msg}, status=404)
        return JsonResponse({'error': msg}, status=409)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def qr_code_api(request, identifier):
    """
    GET /links/<identifier>/qr - Generates QR code URL
    """
    try:
        link_id = int(identifier)
        link = services.get_link_by_id(link_id)
        if link is None:
            link = services.get_link_by_short_code(identifier)
    except ValueError:
        link = services.get_link_by_short_code(identifier)

    if not link:
        return JsonResponse({'error': 'Link not found'}, status=404)

    short_url = request.build_absolute_uri(f"/{link.short_code}")
    qr_url = services.get_qr_code_url(short_url)

    if not qr_url:
        return JsonResponse({
            'error': 'QR Code generation not implemented or returned empty URL',
            'qrCodeUrl': ''
        }, status=400)

    return JsonResponse({
        'shortUrl': short_url,
        'qrCodeUrl': qr_url
    })


def redirect_short_code(request, code):
    """
    GET /<code_or_slug>
    Resolves short code and redirects to target destination with telemetry logging.
    """
    if code in ['favicon.ico', 'robots.txt', 'static', 'admin', 'links', 'api']:
        return HttpResponseNotFound()

    link = services.get_link_by_short_code(code)
    if not link:
        context = {'code': code}
        return render(request, '404.html', context, status=404)

    # Telemetry logging
    referrer = request.META.get('HTTP_REFERER')
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT')

    services.record_click(link.id, referrer=referrer, ip=ip, user_agent=user_agent)

    return redirect(link.original_url)
