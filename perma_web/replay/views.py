import urllib.parse

from django.shortcuts import render, get_object_or_404
from django.views.decorators.clickjacking import xframe_options_exempt

from perma.models import Link

@xframe_options_exempt
def iframe(request):
    guid = request.GET.get('guid')
    screenshot = request.GET.get('type', '') == 'screenshot'
    replay_only = request.GET.get('embed', '') == 'replayonly' or screenshot
    web_worker = not request.GET.get('worker', '') == 'false'
    hidden = request.GET.get('hidden', '') == 'true'
    ondemand = request.GET.get('ondemand', '') == 'true'
    if request.GET.get('target', '') == 'blank':
        target = 'blank'
    elif screenshot:
        target = 'img'
    else:
        target = ''
    context = {}
    if guid:
        link = get_object_or_404(Link.objects.prefetch_related('captures'), guid=guid)
        context['guid'] = link.guid
        context['warc_source_allowed_host'] = urllib.parse.urlparse(link.warc_presigned_url()).netloc
        context['target_url'] = link.screenshot_capture.url if screenshot else link.submitted_url
        context['embed_style'] = 'replayonly' if replay_only else 'default'
        context['web_worker'] = web_worker
        context['hidden'] = hidden
        context['ondemand'] = ondemand
        context['target'] = target
        # only sandbox when:
        # a) the mime-type allows (https://github.com/harvard-lil/perma/blob/e761f4ab597c293f0fd6612e015428100899f28b/perma_web/perma/models.py#L1928)
        # b) the playback will be inline in the browser, rather than an on-demand download mediated by an interstitial,
        #    because some browsers (for instance, Safari) may block downloads from sandboxed iframes even when `allow-downloads` is present.
        #    See https://perma.cc/M36S-ZLVS for `allow-downloads` support on 6/22/22.
        context['sandbox'] = link.primary_capture.use_sandbox() and not ondemand
    response = render(request, 'iframe.html', context)
    response['Clear-Site-Data'] = '"cache", "cookies", "storage"'
    return response


@xframe_options_exempt
def replay_fallback(request):
    """
    If the service worker isn't processing fetch requests at the moment that the
    replay-web-page's internal iframe is loaded, this route will catch the requests.
    """
    return render(request, 'fallback.html', {})
