# -*- coding: utf-8 -*-
from django.urls import reverse

from mock import patch

# from .utils import PermaTestCase

from perma.views.link_management import Link


### create_link function ###

def test_display_after_delete_real_link(perma_client, link_user):
    response = perma_client.get(reverse('create_link'),
                            as_user=link_user,
                            data={'deleted':'ABCD-0003'})
    messages = list(response.context['messages'])
    assert len(messages) == 1
    assert str(messages[0]) == "Deleted - Wikipedia"
    assert 200 == response.status_code

def test_display_after_delete_fake_link(perma_client, link_user):
    response = perma_client.get(reverse('create_link'),
                                as_user=link_user,
                                data={'deleted': 'ZZZZ-ZZZZ'})
    messages = list(response.context['messages'])
    assert len(messages) == 0
    assert 200 == response.status_code

def test_reminder(perma_client, link_user):
    response_content = perma_client.get(reverse('create_link'),
                                as_user=link_user).content
    assert b"browser-tools-message" in response_content

def test_no_reminder_when_refered_from_bookmarklet(perma_client, link_user):
    response_content = perma_client.get(reverse('create_link'),
                                as_user=link_user,
                                data = {'url':'some-url-here'}).content
    assert b"browser-tools-message" not in response_content

def test_no_reminder_when_suppression_cookie_present(perma_client, client, link_user):
    # client.cookies.load({'suppress_reminder': 'true'})
    response = perma_client.get(reverse('create_link'),
                                as_user=link_user)
    assert b"browser-tools-message" not in response
    assert 200 == response.status_code


### user_delete_link function ###

def test_confirm_delete_unpermitted_link(perma_client, link_user):
    response = perma_client.get(reverse('user_delete_link', args=['7CF8-SS4G']),
                                as_user=link_user)
    assert 404 == response.status_code

def test_confirm_delete_nonexistent_link(perma_client, link_user):
    response = perma_client.get(reverse('user_delete_link', args=['ZZZZ-ZZZZ']),
                                as_user=link_user)
    assert 404 == response.status_code

# only brand new links can be deleted,
# so we have to mock Link.is_permanent to always return false
@patch.object(Link, 'is_permanent', lambda x: False)
def test_confirm_delete_permitted_link(perma_client, link_user):
    response = perma_client.get(reverse('user_delete_link', args=['JJ3S-2Q5N']),
                as_user=link_user)
    assert 404 == response.status_code
