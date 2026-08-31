"""
Django-side asset-pipeline contract: what django-webpack-loader must keep
resolving for Perma's templates once webpack-bundle-tracker/django-webpack-loader
move from 1.x to 3.x (Arc 2 Phase 2, sub-batch 2F). See
.plans/plan_dependency-upgrade-roadmap.md.
"""
import json
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from django.apps import apps
from django.conf import settings
from django.template import engines
from django.urls import reverse
from webpack_loader.exceptions import WebpackBundleLookupError
from webpack_loader.utils import get_files

from perma.models import Link

# matches {% render_bundle 'name' %} and {% render_bundle 'name' 'ext' %},
# not the {% load render_bundle from webpack_loader %} tags that also appear in templates
RENDER_BUNDLE_RE = re.compile(
    r"\{%\s*render_bundle\s+(['\"])(?P<name>[^'\"]+)\1"
    r"(?:\s+(['\"])(?P<extension>[^'\"]+)\3)?"
)


def _discover_render_bundle_calls():
    """Scan every template for render_bundle calls, so the expected entry/template list can't drift from reality."""
    templates_dir = Path(apps.get_app_config('perma').path) / 'templates'
    calls = []
    for template_path in sorted(templates_dir.rglob('*.html')):
        text = template_path.read_text()
        for match in RENDER_BUNDLE_RE.finditer(text):
            calls.append({
                'template': template_path.relative_to(templates_dir).as_posix(),
                'name': match.group('name'),
                'extension': match.group('extension'),
            })
    return calls


RENDER_BUNDLE_CALLS = _discover_render_bundle_calls()


def _load_stats():
    stats_path = Path(settings.WEBPACK_LOADER['DEFAULT']['STATS_FILE'])
    with stats_path.open() as f:
        return json.load(f)


def _bundle_dir():
    return Path(settings.PROJECT_ROOT) / 'static' / settings.WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME']


def _chunk_files(entry_name, extension):
    """Non-map file names for one stats entry/extension, read fresh from the stats file (never hardcoded)."""
    return [
        name for name in _load_stats()['chunks'][entry_name]
        if name.endswith(f'.{extension}') and not name.endswith('.map')
    ]


def _expected_url(filename):
    return settings.STATIC_URL + settings.WEBPACK_LOADER['DEFAULT']['BUNDLE_DIR_NAME'] + filename


def _render_bundle_tag(bundle_name, extension=None):
    """Render an actual {% render_bundle %} tag through the real Django template engine, not a re-implementation."""
    args = f"'{bundle_name}'" + (f" '{extension}'" if extension else '')
    source = "{% load render_bundle from webpack_loader %}" + f"{{% render_bundle {args} %}}"
    return engines['django'].from_string(source).render()


#
# 1. Stats file is well-formed and matches settings.
#

def test_render_bundle_calls_are_discovered_across_templates():
    # guards against the discovery regex silently matching nothing and every downstream test passing vacuously
    assert len(RENDER_BUNDLE_CALLS) > 0
    assert len({call['template'] for call in RENDER_BUNDLE_CALLS}) > 0


def test_stats_file_is_well_formed_and_covers_every_requested_entry():
    stats_path = Path(settings.WEBPACK_LOADER['DEFAULT']['STATS_FILE'])
    assert stats_path.is_file()

    stats = _load_stats()
    assert stats['status'] == 'done'

    requested_entries = {call['name'] for call in RENDER_BUNDLE_CALLS}
    assert requested_entries
    assert requested_entries <= stats['chunks'].keys()


#
# 2. Every referenced bundle file exists on disk.
#

def test_every_chunk_file_exists_under_the_bundle_directory():
    stats = _load_stats()
    bundle_dir = _bundle_dir()
    missing = [
        f"{entry}: {filename}"
        for entry, files in stats['chunks'].items()
        for filename in files
        if not (bundle_dir / filename).is_file()
    ]
    assert missing == []


#
# 3. Every template render_bundle call resolves through the real loader API.
#

def test_every_render_bundle_call_resolves():
    for call in RENDER_BUNDLE_CALLS:
        files = get_files(call['name'], extension=call['extension'])
        assert files, (
            f"{call['template']}: render_bundle {call['name']!r} {call['extension']!r} resolved to no files"
        )


def test_unknown_bundle_name_raises_lookup_error():
    with pytest.raises(WebpackBundleLookupError):
        get_files('this-bundle-does-not-exist')


#
# 4. Rendered tag shape and URL construction.
#

def test_render_bundle_js_produces_a_script_tag_with_the_expected_src():
    js_files = _chunk_files('global', 'js')
    assert len(js_files) == 1
    expected_src = _expected_url(js_files[0])

    rendered = _render_bundle_tag('global', 'js').strip()

    assert rendered.startswith('<script ')
    assert rendered.endswith('</script>')
    assert f'src="{expected_src}"' in rendered


def test_render_bundle_css_produces_a_stylesheet_link_with_the_expected_href():
    css_files = _chunk_files('global', 'css')
    assert len(css_files) == 1
    expected_href = _expected_url(css_files[0])

    rendered = _render_bundle_tag('global', 'css').strip()

    assert rendered.startswith('<link ')
    assert f'href="{expected_href}"' in rendered
    assert 'rel="stylesheet"' in rendered


#
# 5. Extension filtering excludes source maps and the other asset type.
#

def test_render_bundle_js_excludes_source_maps_and_css():
    rendered = _render_bundle_tag('global', 'js')
    assert '.map' not in rendered
    assert '.css' not in rendered
    assert rendered.count('<script') == 1


def test_render_bundle_css_excludes_source_maps_and_js():
    rendered = _render_bundle_tag('global', 'css')
    assert '.map' not in rendered
    assert rendered.count('<link') == 1


def test_bundle_lookup_excludes_source_maps_even_without_an_extension_filter():
    # loader's default IGNORE config (not the extension arg) is what actually keeps .map out
    all_files = get_files('global')
    assert not any(f['name'].endswith('.map') for f in all_files)


#
# 6. Templates that load bundles render without a webpack-loader error.
#
# base-responsive.html and archive/base-archive-responsive.html have no view of
# their own -- they are {% extends %} targets -- so they are exercised
# transitively through admin-stats.html/dev_docs/create-link.html/
# link-delete-confirm.html (base-responsive.html) and single-link.html
# (archive/base-archive-responsive.html).
#

def test_admin_stats_page_renders(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse('admin_stats', kwargs={'stat_type': ''}), secure=True)
    assert response.status_code == 200


def test_developer_docs_page_renders(client):
    response = client.get(reverse('dev_docs'), secure=True)
    assert response.status_code == 200


def test_create_link_dashboard_page_renders(client, link_user):
    client.force_login(link_user)
    response = client.get(reverse('create_link'), secure=True)
    assert response.status_code == 200


@patch.object(Link, 'is_permanent', lambda self: False)
def test_link_delete_confirm_page_renders(client, link_factory, link_user):
    new_link = link_factory(created_by=link_user)
    client.force_login(link_user)
    response = client.get(reverse('user_delete_link', args=[new_link.guid]), secure=True)
    assert response.status_code == 200


def test_single_link_playback_page_renders(client, complete_link):
    response = client.get(reverse('single_permalink', kwargs={'guid': complete_link.guid}), secure=True)
    assert response.status_code == 200
