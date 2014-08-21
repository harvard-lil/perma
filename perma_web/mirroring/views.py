import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, StreamingHttpResponse

from perma.models import Asset, Link
from perma.utils import run_task
from perma.views.common import single_link_header

from .tasks import update_perma, compress_link_assets
from .utils import must_be_mirrored, may_be_mirrored


@may_be_mirrored
def link_assets(request, guid):
    """
        A service that returns a downloadable archive of the assets of a
        given perma link.
    """
    target_asset = get_object_or_404(Asset, link__guid=guid)
    # TODO: this should probably be a field on the Asset object
    archive_path = os.path.join(settings.MEDIA_ARCHIVES_ROOT, target_asset.base_storage_path + ".zip")
    try:
        zip_file = default_storage.open(archive_path, "r")
    except IOError:
        # We already found the Asset in the database, but the zip file doesn't exist for some reason.
        # Let's re-create it.
        compress_link_assets(guid=guid)
        try:
            zip_file = default_storage.open(archive_path, "r")
        except IOError:
            # Weird, it still doesn't exist. Throw an error.
            raise

    # Now we've managed to open the zip file, pass the open filehandle back to Django.
    response = StreamingHttpResponse(zip_file, content_type="application/force-download")
    response["Content-Disposition"] = 'attachment; filename="%s"' % ("assets_%s.zip" % guid,)
    return response


@must_be_mirrored
def do_update_perma(request, guid):
    run_task(update_perma, link_guid=guid)
    return HttpResponse("OK")


def single_link_json(request, guid):
    """
        This is a version of the single link page that can only be called on the main server.
        It gets called as JSON (by the regular single link page on a mirror) and returns
        the data necessary for the mirror to render the page.
    """
    return single_link_header(request, guid)

@may_be_mirrored
def manifest(request):
    """
        List all Perma Links known to this server in a text file, one per line.
    """
    # Get queryset that returns each link as a simple list containing guid.
    known_links = Link.objects.values_list('guid')
    # Create generator to spit out each result on its own line.
    output_generator = (link[0]+"\n" for link in known_links)
    # Stream results.
    return StreamingHttpResponse(output_generator, content_type="text/tab-separated-values")
