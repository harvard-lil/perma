from warcio.timeutils import datetime_to_http_date

from django.urls import reverse

from conftest import json_serialize_datetime
import pytest


def test_timemap_json(client, memento_link_set):
    link_set = memento_link_set

    response = client.get(
        reverse('timemap', args=['json', link_set['domain']]),
        secure=True
    )
    assert response.headers['content-type'] == 'application/json'
    assert response.headers['x-memento-count'] == str(len(link_set['links']))

    response_json = response.json()
    assert response_json['self'] == f"https://testserver/timemap/json/{link_set['domain']}"
    assert response_json['original_uri'] == link_set['domain']
    assert response_json['timegate_uri'] == f"https://testserver/timegate/{link_set['domain']}"
    assert response_json['timemap_uri'] == {
        'json_format': f"https://testserver/timemap/json/{link_set['domain']}",
        'link_format': f"https://testserver/timemap/link/{link_set['domain']}",
        'html_format': f"https://testserver/timemap/html/{link_set['domain']}"
    }
    assert response_json['mementos']['first'] == {
        'uri': f"https://testserver/{link_set['links'][0]['guid']}", 'datetime': json_serialize_datetime(link_set['links'][0]['timestamp'])
    }
    assert response_json['mementos']['last'] == {
        'uri': f"https://testserver/{link_set['links'][-1]['guid']}", 'datetime': json_serialize_datetime(link_set['links'][-1]['timestamp'])
    }
    assert response_json['mementos']['list'] == [
        {
            'uri': f"https://testserver/{link['guid']}",
            'datetime': json_serialize_datetime(link['timestamp'])
        } for link in link_set['links']
    ]


def test_timemap_link(client, memento_link_set):
    link_set = memento_link_set

    response = client.get(
        reverse('timemap', args=['link', link_set['domain']]),
        secure=True
    )

    assert response.headers['content-type'] == 'application/link-format'
    assert response.headers['x-memento-count'] == str(len(link_set['links']))

    top = f"""\
<{link_set['domain']}>; rel=original,
<https://testserver/timegate/{link_set['domain']}>; rel=timegate,
<https://testserver/timemap/link/{link_set['domain']}>; rel=self; type=application/link-format,
<https://testserver/timemap/link/{link_set['domain']}>; rel=timemap; type=application/link-format,
<https://testserver/timemap/json/{link_set['domain']}>; rel=timemap; type=application/json,
<https://testserver/timemap/html/{link_set['domain']}>; rel=timemap; type=text/html,\n"""
    bottom = "\n".join(
        [
            f'<https://testserver/{link["guid"]}>; rel=memento; datetime="{datetime_to_http_date(link["timestamp"])}",'
            for link in link_set['links']
        ]
    )
    expected = (top + bottom + "\n").encode()
    assert response.content == expected


@pytest.mark.parametrize(
    "response_type", ["link", "json"]
)
def test_timemap_not_found_standard(response_type, client, memento_link_set):
    response = client.get(
        reverse('timemap', args=[response_type, memento_link_set['domain'] + "?foo=bar"]),
        secure=True
    )
    assert response.status_code == 404
    assert response.headers['x-memento-count'] == '0'
    assert response.content == b'404 page not found\n'


def test_timemap_not_found_html(client, memento_link_set):
    destination = memento_link_set['domain'] + "?foo=bar"
    response = client.get(
        reverse('timemap', args=['html', destination]),
        secure=True
    )
    assert response.status_code == 404
    assert response.headers['x-memento-count'] == '0'
    assert f'<i>No captures found for <b>{destination}</b></i>'.encode() in response.content


def test_timegate_most_recent(client, memento_link_set):
    link_set = memento_link_set
    response = client.get(
        reverse('timegate', args=[link_set['domain']]),
        secure=True
    )
    assert response.status_code == 302
    assert response.headers['location'] == f'https://testserver/{link_set["links"][-1]["guid"]}'
    assert 'accept-datetime' in response.headers['vary']
    assert f'<https://testserver/{link_set["links"][0]["guid"]}>; rel="first memento"; datetime="{datetime_to_http_date(link_set["links"][0]["timestamp"])}"' in response.headers['link']
    assert f'<https://testserver/{link_set["links"][-1]["guid"]}>; rel="last memento"; datetime="{datetime_to_http_date(link_set["links"][-1]["timestamp"])}"' in response.headers['link']
    assert f'<https://testserver/{link_set["links"][-1]["guid"]}>; rel=memento; datetime="{datetime_to_http_date(link_set["links"][-1]["timestamp"])}"' in response.headers['link']
    assert f'<{link_set["domain"]}>; rel=original,' in response.headers['link']
    assert f'<https://testserver/timegate/{link_set["domain"]}>; rel=timegate,' in response.headers['link']
    assert f'<https://testserver/timemap/link/{link_set["domain"]}>; rel=timemap; type=application/link-format,' in response.headers['link']
    assert f'<https://testserver/timemap/json/{link_set["domain"]}>; rel=timemap; type=application/json,' in response.headers['link']
    assert f'<https://testserver/timemap/html/{link_set["domain"]}>; rel=timemap; type=text/html,' in response.headers['link']


def test_timegate_with_target_date(client, memento_link_set):
    link_set = memento_link_set
    target = link_set['links'][3]

    response = client.get(
        reverse('timegate', args=[link_set['domain']]),
        secure=True,
        HTTP_ACCEPT_DATETIME=datetime_to_http_date(target['timestamp'])
    )

    assert response.status_code == 302
    assert response.headers['location'] == f'https://testserver/{target["guid"]}'
    assert 'accept-datetime', response.headers['vary']
    assert f'<https://testserver/{link_set["links"][0]["guid"]}>; rel="first memento"; datetime="{datetime_to_http_date(link_set["links"][0]["timestamp"])}"' in response.headers['link']
    assert f'<https://testserver/{link_set["links"][-1]["guid"]}>; rel="last memento"; datetime="{datetime_to_http_date(link_set["links"][-1]["timestamp"])}"' in response.headers['link']
    assert f'<https://testserver/{target["guid"]}>; rel=memento; datetime="{datetime_to_http_date(target["timestamp"])}"' in response.headers['link']
    assert f'<https://testserver/timegate/{link_set["domain"]}>; rel=timegate,' in response.headers['link']
    assert f'<https://testserver/timemap/link/{link_set["domain"]}>; rel=timemap; type=application/link-format,' in response.headers['link']
    assert f'<https://testserver/timemap/json/{link_set["domain"]}>; rel=timemap; type=application/json,' in response.headers['link']
    assert f'<https://testserver/timemap/html/{link_set["domain"]}>; rel=timemap; type=text/html,' in response.headers['link']


def test_timegate_not_found(client, memento_link_set):
    destination = memento_link_set['domain'] + "?foo=bar"
    response = client.get(
        reverse('timegate', args=[destination]),
        secure=True
    )

    assert response.status_code == 404
    assert response.content ==  b'404 page not found\n'
