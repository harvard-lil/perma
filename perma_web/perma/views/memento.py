from datetime import timezone as tz
from io import StringIO
from link_header import Link as Rel, LinkHeader
from ratelimit.decorators import ratelimit
from timegate.utils import closest
from warcio.timeutils import datetime_to_http_date
from werkzeug.http import parse_date

from django.conf import settings
from django.http import (HttpResponse,JsonResponse,
    HttpResponseNotFound, HttpResponseBadRequest)
from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
from django.utils import timezone

from ..utils import (if_anonymous, ratelimit_ip_key,
    memento_data_for_url, url_with_qs_and_hash)


@if_anonymous(cache_control(max_age=settings.CACHE_MAX_AGES['timemap']))
@ratelimit(rate=settings.MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.HOUR_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.DAY_LIMIT, block=True, key=ratelimit_ip_key)
def timemap(request, response_format, url):
    url = url_with_qs_and_hash(url, request.META['QUERY_STRING'])
    data = memento_data_for_url(request, url)
    if data:
        if response_format == 'json':
            response = JsonResponse(data)
        elif response_format == 'html':
            response = render(request, 'memento/timemap.html', data)
        else:
            content_type = 'application/link-format'
            file = StringIO()
            file.writelines(f"{line},\n" for line in [
                Rel(data['original_uri'], rel='original'),
                Rel(data['timegate_uri'], rel='timegate'),
                Rel(data['self'], rel='self', type='application/link-format'),
                Rel(data['timemap_uri']['link_format'], rel='timemap', type='application/link-format'),
                Rel(data['timemap_uri']['json_format'], rel='timemap', type='application/json'),
                Rel(data['timemap_uri']['html_format'], rel='timemap', type='text/html')
            ] + [
                Rel(memento['uri'], rel='memento', datetime=datetime_to_http_date(memento['datetime'])) for memento in data['mementos']['list']
            ])
            file.seek(0)
            response = HttpResponse(file, content_type=f'{content_type}')
    else:
        if response_format == 'html':
            response = render(request, 'memento/timemap.html', {"original_uri": url}, status=404)
        else:
            response = HttpResponseNotFound('404 page not found\n')

    response['X-Memento-Count'] = str(len(data['mementos']['list'])) if data else 0
    return response


@if_anonymous(cache_control(max_age=settings.CACHE_MAX_AGES['timegate']))
@ratelimit(rate=settings.MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.HOUR_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.DAY_LIMIT, block=True, key=ratelimit_ip_key)
def timegate(request, url):
    # impose an arbitrary length-limit on the submitted URL, so that the headers don't become illegally large
    url = url_with_qs_and_hash(url, request.META['QUERY_STRING'])[:500]
    data = memento_data_for_url(request, url)
    if not data:
        return HttpResponseNotFound('404 page not found\n')

    accept_datetime = request.META.get('HTTP_ACCEPT_DATETIME')
    if accept_datetime:
        accept_datetime = parse_date(accept_datetime)
        if not accept_datetime:
            return HttpResponseBadRequest('Invalid value for Accept-Datetime.')
    else:
        accept_datetime = timezone.now()
    accept_datetime = accept_datetime.replace(tzinfo=tz.utc)

    target, target_datetime = closest([m.values() for m in data['mementos']['list']], accept_datetime)

    response = redirect(target)
    response['Vary'] = 'accept-datetime'
    response['Link'] = str(
        LinkHeader([
            Rel(data['original_uri'], rel='original'),
            Rel(data['timegate_uri'], rel='timegate'),
            Rel(data['timemap_uri']['link_format'], rel='timemap', type='application/link-format'),
            Rel(data['timemap_uri']['json_format'], rel='timemap', type='application/json'),
            Rel(data['timemap_uri']['html_format'], rel='timemap', type='text/html'),
            Rel(data['mementos']['first']['uri'], rel='first memento', datetime=datetime_to_http_date(data['mementos']['first']['datetime'])),
            Rel(data['mementos']['last']['uri'], rel='last memento', datetime=datetime_to_http_date(data['mementos']['last']['datetime'])),
            Rel(target, rel='memento', datetime=datetime_to_http_date(target_datetime)),
        ])
    )
    return response
