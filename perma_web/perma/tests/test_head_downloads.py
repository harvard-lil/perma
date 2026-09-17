"""HEAD downloads check access and metadata without reading native archives."""
from types import SimpleNamespace
from unittest.mock import Mock

from django.http import Http404
from django.test import RequestFactory
import pytest

from perma import utils


@pytest.fixture(scope='session')
def create_storage_buckets():
    # Storage is mocked throughout this module.
    pass


@pytest.fixture
def link():
    return SimpleNamespace(
        guid='ABCD-1234', user_deleted=False, warc_size=100, wacz_size=100,
        can_play_back=Mock(return_value=True),
        warc_storage_file=Mock(return_value='archive.warc.gz'),
        wacz_storage_file=Mock(return_value='archive.wacz'),
        get_warc=Mock(), get_wacz=Mock(),
    )


@pytest.mark.parametrize('file_format,mime,suffix', [
    ('warc', 'application/gzip', 'warc.gz'),
    ('wacz', 'application/wacz', 'wacz'),
])
def test_head_native_archive(link, monkeypatch, file_format, mime, suffix):
    storage = Mock()
    monkeypatch.setattr(utils, 'storages', dict.fromkeys([utils.settings.WARC_STORAGE, utils.settings.WACZ_STORAGE], storage))
    response = utils.stream_archive(link, file_format=file_format, head=True)
    assert b''.join(response.streaming_content) == b''
    assert response['Content-Type'] == mime
    assert response['Content-Disposition'] == f'attachment; filename="ABCD-1234.{suffix}"'
    assert 'Content-Length' not in response
    storage.exists.assert_called_once()
    storage.open.assert_not_called()
    link.get_warc.assert_not_called()
    link.get_wacz.assert_not_called()


@pytest.mark.parametrize('file_format', ['warc', 'wacz'])
def test_head_missing_storage(link, monkeypatch, file_format):
    storage = Mock()
    storage.exists.return_value = False
    monkeypatch.setattr(utils, 'storages', dict.fromkeys([utils.settings.WARC_STORAGE, utils.settings.WACZ_STORAGE], storage))
    with pytest.raises(Http404):
        utils.stream_archive(link, file_format=file_format, head=True)


@pytest.mark.parametrize('authenticated,allowed,status', [(False, False, 401), (True, False, 403)])
def test_head_permissions(link, authenticated, allowed, status):
    user = SimpleNamespace(is_authenticated=authenticated, can_view=lambda link: allowed)
    assert utils.stream_archive_if_permissible(link, user, head=True).status_code == status
    link.can_play_back.assert_not_called()


@pytest.mark.parametrize('deleted,playable', [(True, True), (False, False)])
def test_head_unavailable_archive(link, deleted, playable):
    link.user_deleted = deleted
    link.can_play_back.return_value = playable
    with pytest.raises(Http404):
        utils.stream_archive(link, head=True)


def test_head_missing_warc(link):
    link.warc_size = 0
    link.get_warc.side_effect = RuntimeError('No archive present')
    with pytest.raises(Http404):
        utils.stream_archive(link, head=True)


@pytest.mark.parametrize('method', ['GET', 'HEAD'])
def test_api_download_forwards_method(link, monkeypatch, method):
    from api.views import links
    link.replacement_link_id = None
    view = links.AuthenticatedLinkDownloadView()
    view.get_object_for_user_by_pk = Mock(return_value=link)
    monkeypatch.setattr(links, 'get_download_file_format', lambda request: 'warc')
    download = Mock()
    monkeypatch.setattr(links, 'stream_archive_if_permissible', download)
    request = SimpleNamespace(method=method, user=SimpleNamespace(guid='user'))
    view.get(request, link.guid)
    download.assert_called_once_with(link, request.user, file_format='warc', head=method == 'HEAD')


@pytest.mark.parametrize('method', ['GET', 'HEAD'])
@pytest.mark.parametrize('serve_type', ['warc_download', 'wacz_download'])
def test_permalink_download_forwards_method(link, monkeypatch, method, serve_type):
    from inspect import unwrap
    monkeypatch.setattr("ratelimit.decorators.is_ratelimited", lambda **kwargs: False)
    from perma.views import playback
    link.replacement_link_id = None
    monkeypatch.setattr(playback, 'get_object_or_404', lambda *args, **kwargs: link)
    download = Mock()
    monkeypatch.setattr(playback, 'stream_archive_if_permissible', download)
    request = RequestFactory().generic(method, '/ABCD-1234', QUERY_STRING=f'type={serve_type}')
    request.user = SimpleNamespace(is_authenticated=True)
    unwrap(playback.single_permalink)(request, link.guid)
    download.assert_called_once_with(link, request.user, file_format=serve_type.split('_')[0], head=method == 'HEAD')


@pytest.mark.parametrize('method,queued', [('GET', True), ('HEAD', False)])
def test_head_does_not_queue_conversion(monkeypatch, settings, method, queued):
    from inspect import unwrap
    monkeypatch.setattr("ratelimit.decorators.is_ratelimited", lambda **kwargs: False)
    from django.http import HttpResponse
    from perma.views import playback
    settings.WARC_TO_WACZ_ON_DEMAND = True
    link = Mock(
        guid='ABCD-1234', replacement_link_id=None, warc_size=1, wacz_size=0,
        is_user_uploaded=False, user_deleted=False, submitted_description='description',
    )
    link.primary_capture.status = 'success'
    link.has_wacz_version.return_value = False
    link.is_visible_to_memento.return_value = False
    user = Mock(is_authenticated=False)
    monkeypatch.setattr(playback, 'get_object_or_404', lambda *args, **kwargs: link)
    monkeypatch.setattr(playback, 'render', lambda *args, **kwargs: HttpResponse('page'))
    convert = Mock()
    monkeypatch.setattr(playback, 'convert_warc_to_wacz', convert)
    request = RequestFactory().generic(method, '/ABCD-1234', QUERY_STRING='type=standard')
    request.user = user
    response = unwrap(playback.single_permalink)(request, link.guid)
    assert response.status_code == 200
    assert convert.delay.called == queued
