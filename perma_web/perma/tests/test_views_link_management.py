# -*- coding: utf-8 -*-
from django.urls import reverse

from mock import patch


from perma.views.link_management import Link


### user_delete_link function ###

def test_confirm_delete_unpermitted_link(perma_client, link, link_user):
    response = perma_client.get(reverse('user_delete_link', args=[link.guid]),
                                as_user=link_user)
    assert 404 == response.status_code

def test_confirm_delete_nonexistent_link(perma_client, link_user):
    assert not Link.objects.filter(guid='ZZZZ-ZZZZ').exists()
    response = perma_client.get(reverse('user_delete_link', args=['ZZZZ-ZZZZ']),
                                as_user=link_user)
    assert 404 == response.status_code

# only brand new links can be deleted,
# so we have to mock Link.is_permanent to always return false
@patch.object(Link, 'is_permanent', lambda x: False)
def test_confirm_delete_permitted_link(perma_client, link_factory, link_user):
    new_link = link_factory(created_by=link_user)
    perma_client.get(reverse('user_delete_link', args=[new_link.guid]),
                as_user=link_user)
