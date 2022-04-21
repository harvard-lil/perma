from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_exempt

from perma.models import Link

@xframe_options_exempt
def iframe(request):
    guid = request.GET.get('guid')
    screenshot = request.GET.get('type', '') == 'screenshot'
    replay_only = request.GET.get('embed', '') == 'replayonly' or screenshot
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
        link = get_object_or_404(Link.objects.all_with_deleted().prefetch_related('captures'), guid=guid)
        context['guid'] = link.guid
        context['warc_source'] = f"{ request.scheme }://{ settings.HOST }{ reverse('serve_warc', args=[link.guid], urlconf='perma.urls') }"
        context['target_url'] = link.screenshot_capture.url if screenshot else link.submitted_url
        context['embed_style'] = 'replayonly' if replay_only else 'default'
        context['sandbox'] = link.primary_capture.use_sandbox()
        context['hidden'] = hidden
        context['ondemand'] = ondemand
        context['target'] = target
    return render(request, 'iframe.html', context)

def replay_service_worker(request):
    """
    The service worker required for client-side playback:
    """
    return HttpResponse(f'importScripts("{ settings.SERVICE_WORKER_URL }");\n', content_type='application/x-javascript')
