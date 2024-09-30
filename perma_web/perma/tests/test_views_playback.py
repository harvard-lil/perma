from warcio.timeutils import datetime_to_http_date

from django.urls import reverse

from perma.models import Link, CaptureJob

import pytest
from waffle.testutils import override_flag

#
#  Helpers
#

def get_playback(client, guid, follow=False, expect_iframe=True):
    url = reverse('single_permalink', kwargs={'guid': guid})
    response = client.get(url, secure=True, follow=follow)
    assert response.status_code != 500
    if expect_iframe:
        assert b"<iframe " in response.content
    return response


def check_memento_headers(link, response):
    assert response.headers['memento-datetime'] == datetime_to_http_date(link.creation_timestamp)
    assert f'<{link.submitted_url}>; rel=original,' in response.headers['link']
    assert f'<https://testserver/timegate/{link.submitted_url}>; rel=timegate,' in response.headers['link']
    assert f'<https://testserver/timemap/link/{link.submitted_url}>; rel=timemap; type=application/link-format,' in response.headers['link']
    assert f'<https://testserver/timemap/json/{link.submitted_url}>; rel=timemap; type=application/json,' in response.headers['link']
    assert f'<https://testserver/timemap/html/{link.submitted_url}>; rel=timemap; type=text/html,' in response.headers['link']
    assert f'<https://testserver/{link.guid}>; rel=memento; datetime="{datetime_to_http_date(link.creation_timestamp)}"' in response.headers['link']


#
# Tests
#

def test_regular_archive(client, link_user, org_user, registrar_user, admin_user):
    guid = 'UU32-XY8I'

    link = Link.objects.get(guid=guid)
    assert link.capture_job.status == 'completed'

    for user in [None, link_user, org_user, registrar_user, admin_user]:
        if user:
            client.force_login(user)
        response = get_playback(client, guid)
        check_memento_headers(link, response)


@pytest.mark.django_db
@override_flag('wacz-playback', active=False)
def test_regular_archive_with_wacz_and_flag_off(client):
    guid = 'UU32-XY8I'

    response = get_playback(client, guid)
    # We are playing back a WARC
    assert b".warc.gz?" in response.content
    # We are not playing back a WACZ
    assert b".wacz?" not in response.content


@pytest.mark.django_db
@override_flag('wacz-playback', active=True)
def test_regular_archive_with_wacz_and_flag_on(client):
    guid = 'UU32-XY8I'
    link = Link.objects.get(guid=guid)
    link.wacz_size = 1  # anything non-zero
    link.save()

    response = get_playback(client, guid)
    # We are not playing back a WARC
    assert b".warc.gz?" not in response.content
    # We are playing back a WACZ
    assert b".wacz?" in response.content


@pytest.mark.django_db
@override_flag('wacz-playback', active=True)
def test_regular_archive_without_wacz_and_flag_on(client):
    guid = 'UU32-XY8I'
    link = Link.objects.get(guid=guid)
    assert not link.wacz_size

    response = get_playback(client, guid)
    # We are playing back a WARC
    assert b".warc.gz?" in response.content
    # We are not playing back a WACZ
    assert b".wacz?" not in response.content


def test_archive_without_capture_job(client, link_user, org_user, registrar_user, admin_user):
    guid = '3SLN-JHX9'

    # assert no capture job
    with pytest.raises(CaptureJob.DoesNotExist):
        link = Link.objects.get(guid=guid)
        link.capture_job

    for user in [None, link_user, org_user, registrar_user, admin_user]:
        if user:
            client.force_login(user)
        response = get_playback(client, guid)
        check_memento_headers(link, response)


@pytest.mark.django_db
def test_archive_with_unsuccessful_capturejob(client):
    guid = 'UU32-XY8I'
    link = Link.objects.get(guid=guid)
    for status in ['pending','in_progress','deleted','failed', 'invalid']:
        link.capture_job.status = status
        link.capture_job.save()
        get_playback(client, guid)


@pytest.mark.django_db
def test_screenshot_only_archive_default_to_screenshot_view_false(client):
    """
    When there is just a screenshot, no primary capture, and "default to screenshot" is false,
    we should redirect to the image playback
    """
    guid = 'ABCD-0007'
    link = Link.objects.get(guid=guid)
    assert not link.primary_capture
    assert link.screenshot_capture
    assert not link.default_to_screenshot_view

    response = get_playback(client, guid, follow=True)
    assert b'Enhance screenshot playback' in response.content
    assert response.request.get('QUERY_STRING') == 'type=image'


@pytest.mark.django_db
def test_capture_only_archive_default_to_screenshot_view_true(client):
    """
    When there is just a primary capture, no screenshot, and "default to screenshot" is true,
    we should redirect to the standard playback
    """
    guid = 'N1N0-33DB'
    link = Link.objects.get(guid=guid)
    assert link.primary_capture
    assert not link.screenshot_capture
    assert link.default_to_screenshot_view

    response = get_playback(client, guid, follow=True)
    assert b'Enhance screenshot playback' not in response.content
    assert response.request.get('QUERY_STRING') == 'type=standard'


@pytest.mark.django_db
def test_screenshot_only_archive_default_to_screenshot_view_true(client):
    """
    When there is just a screenshot, no primary capture, and "default to screenshot" is true,
    there should not be a redirect the "type=image" query
    """
    guid = 'ABCD-0008'
    link = Link.objects.get(guid=guid)
    assert not link.primary_capture
    assert link.screenshot_capture
    assert link.default_to_screenshot_view

    response = get_playback(client, guid, follow=True)
    assert b'Enhance screenshot playback' in response.content
    assert response.request.get('QUERY_STRING') == ''


@pytest.mark.django_db
def test_capture_only_archive_default_to_screenshot_view_false(client):
    """
    When there is just a primary capture, no screenshot, "default to screenshot" is false,
    there should not be a redirect to the "type=standard" query
    """
    guid = 'M1L0-87DB'
    link = Link.objects.get(guid=guid)
    assert link.primary_capture
    assert not link.screenshot_capture
    assert not link.default_to_screenshot_view

    response = get_playback(client, guid, follow=True)
    assert response.request.get('QUERY_STRING') == ''


@pytest.mark.django_db
def test_full_archive_default_to_screenshot_view_false(client):
    """
    When there is BOTH a primary capture and a screenshot, and "default to screenshot" is false,
    there should not be a redirect to the "type=standard" query
    """
    guid='UU32-XY8I'
    link = Link.objects.get(guid=guid)
    assert link.primary_capture
    assert link.screenshot_capture
    assert not link.default_to_screenshot_view

    response = get_playback(client, guid, follow=True)
    assert b'Enhance screenshot playback' not in response.content
    assert response.request.get('QUERY_STRING') == ''


@pytest.mark.django_db
def test_full_archive_default_to_screenshot_view_true(client):
    """
    When there is BOTH a primary capture and a screenshot and "default to screenshot" is true,
    there should not be a redirect to the "type=standard" query
    """
    guid = 'F1X1-LS24'
    link = Link.objects.get(guid=guid)
    assert link.primary_capture
    assert link.screenshot_capture
    assert link.default_to_screenshot_view

    response = get_playback(client, guid, follow=True)
    assert b'Enhance screenshot playback' in response.content
    assert response.request.get('QUERY_STRING') == ''


@pytest.mark.django_db
def test_capture_only_default_to_screenshot_view_true(client):
    """
    When there is just a primary capture, no screenshot, "default to screenshot" is true,
    we should redirect to the "type=standard" query
    """
    guid = 'N1N0-33DB'
    link = Link.objects.get(guid=guid)
    assert link.primary_capture
    assert not link.screenshot_capture
    assert link.default_to_screenshot_view

    response = get_playback(client, guid, follow=True)
    assert b'Enhance screenshot playback' not in response.content
    assert response.request.get('QUERY_STRING') == 'type=standard'


def test_dark_archive(client, link_user, org_user, registrar_user, admin_user):
    for user in [None, link_user, org_user, registrar_user, admin_user]:
        if user:
            client.force_login(user)

        response = get_playback(client, 'ABCD-0001')

        assert b"This record is private" in response.content
        assert 'memento-datetime' not in response.headers
        assert 'link' not in response.headers

        if user and user.is_staff:
            assert response.status_code == 200
        else:
            assert response.status_code == 403


# Feature temporarily disabled
# NB: this test has not been ported to Pytest syntax
"""
def test_redirect_to_download(self):
    with patch('perma.storage_backends.S3MediaStorage.open', lambda path, mode: open(os.path.join(settings.PROJECT_ROOT, 'perma/tests/assets/new_style_archive/archive.warc.gz'), 'rb')):
        # Give user option to download to view pdf if on mobile
        link = Link.objects.get(pk='7CF8-SS4G')

        client = Client(HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 6_1_4 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10B350 Safari/8536.25')
        response = client.get(reverse('single_permalink', kwargs={'guid': link.guid}), secure=True)
        self.assertIn(b"Perma.cc can\xe2\x80\x99t display this file type on mobile", response.content)

        # If not on mobile, display link as normal
        client = Client(HTTP_USER_AGENT='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/601.7.7 (KHTML, like Gecko) Version/9.1.2 Safari/601.7.7')
        response = client.get(reverse('single_permalink', kwargs={'guid': link.guid}), secure=True)
        self.assertNotIn(b"Perma.cc can\xe2\x80\x99t display this file type on mobile", response.content)
"""

@pytest.mark.django_db
def test_deleted(client):
    response = get_playback(client, 'ABCD-0003', follow=True)
    assert response.status_code == 410
    assert b"This record has been deleted." in response.content
    assert 'memento-datetime' not in response.headers
    assert 'link' not in response.headers


@pytest.mark.django_db
def test_misformatted_nonexistent_links_404(client):
    for guid in ['JJ99--JJJJ', '988-JJJJ=JJJJ']:
        response = get_playback(client, guid, expect_iframe=False)
        assert response.status_code == 404


@pytest.mark.django_db
def test_properly_formatted_nonexistent_links_404(client):
    for guid in ['JJ99-JJJJ', '0J6pkzDeQwT']:
        response = get_playback(client, guid, expect_iframe=False)
        assert response.status_code == 404


@pytest.mark.django_db
def test_replacement_link(client):
    response = get_playback(client, 'ABCD-0006', expect_iframe=False)
    assert response.status_code == 302
    assert response.headers['location'] == reverse('single_permalink', kwargs={'guid': '3SLN-JHX9'})
