"""Layout regressions observed during staging review, independent of Bootstrap version."""

import pytest
from playwright.sync_api import expect


@pytest.mark.uses_storage
@pytest.mark.parametrize('width', [375, 768, 1200])
@pytest.mark.parametrize('route', [
    'user_management_manage_organization',
    'user_management_manage_user',
    'user_management_manage_registrar',
])
def test_management_list_columns(page, ui_urls, staff_user, log_in, width, route):
    log_in(page, staff_user)
    page.set_viewport_size({'width': width, 'height': 900})
    page.goto(ui_urls(route))
    row = page.locator('ol.result-list > .item-container').first
    expect(row).to_be_visible()
    content = row.locator(':scope > div').first.bounding_box()
    actions = row.locator('.admin-actions').bounding_box()
    if width >= 768:
        assert abs(content['y'] - actions['y']) <= 4
        assert actions['x'] >= content['x'] + content['width'] - 2
    else:
        assert actions['y'] >= content['y'] + content['height'] - 2
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')


@pytest.mark.uses_storage
@pytest.mark.parametrize('width', [990, 1200])
def test_landing_modules_share_a_desktop_row(page, ui_urls, width):
    page.set_viewport_size({'width': width, 'height': 900})
    page.goto(ui_urls('landing'))
    page.evaluate('document.fonts.ready')
    modules = page.locator('#landing-signup .signup-module')
    # Read one layout frame: lazy images elsewhere can move the section between calls.
    boxes = modules.evaluate_all('elements => elements.map(el => { const r = el.getBoundingClientRect(); '
                                 'return {x: r.x, y: r.y, width: r.width}; })')
    assert len(boxes) == 4
    assert max(box['y'] for box in boxes) - min(box['y'] for box in boxes) <= 1
    assert all(left['x'] + left['width'] <= right['x'] + 1
               for left, right in zip(boxes, boxes[1:]))


@pytest.mark.uses_storage
def test_docs_body_keeps_its_right_column(page, ui_urls):
    page.set_viewport_size({'width': 1200, 'height': 900})
    page.goto(ui_urls('docs'))
    introduction = page.locator('.reading-body').first.bounding_box()
    continuation = page.locator('#create-account .reading-body').bounding_box()
    assert abs(introduction['x'] - continuation['x']) <= 1


@pytest.mark.uses_storage
def test_batch_dialog_dimensions_and_close_control(page, ui_urls, user, log_in):
    page.set_viewport_size({'width': 1200, 'height': 900})
    log_in(page, user)
    page.goto(ui_urls('create_link'))
    page.get_by_role('button', name='create multiple links').click()
    dialog = page.get_by_role('dialog')
    expect(dialog).to_be_visible()
    content = dialog.locator('#batch-modal').bounding_box()
    close = dialog.get_by_role('button', name='Close', exact=True)
    close_box = close.bounding_box()
    assert abs(content['width'] - 900) <= 1
    assert abs(content['y'] - 37.5) <= 1
    assert close_box['x'] > content['x'] + content['width'] / 2
    assert close_box['width'] < 20
    close.click()
    expect(dialog).to_be_hidden()


@pytest.mark.uses_storage
@pytest.mark.parametrize('width', [375, 768, 1200])
def test_account_menu_stays_inside_viewport(page, ui_urls, staff_user, log_in, width):
    log_in(page, staff_user)
    page.set_viewport_size({'width': width, 'height': 900})
    page.goto(ui_urls('user_management_manage_organization'))
    if width < 768:
        page.get_by_role('button', name='Toggle navigation').click()
    else:
        page.get_by_role('button', name='Main Dropdown').click()
    expect(page.get_by_role('button', name='Log out')).to_be_visible()
    menu = page.locator('#upper_right_menu .dropdown-menu').bounding_box()
    assert menu['x'] >= 0
    assert menu['x'] + menu['width'] <= width
    for link in page.locator('#upper_right_menu .dropdown-menu a').all():
        box = link.bounding_box()
        assert box['x'] >= menu['x']
        assert box['x'] + box['width'] <= menu['x'] + menu['width']


@pytest.mark.uses_storage
@pytest.mark.parametrize('width', [768, 1440])
def test_archive_header_and_frame_geometry(page, urls, user, log_in_user, width):
    page.set_viewport_size({'width': width, 'height': 900})
    log_in_user(page, user)
    page.goto(urls.perma_link_with_warc)
    # Escape can cancel a pending iframe navigation; load replay before
    # exercising the menu's Escape-to-close behavior.
    expect(page.frame_locator('.archive-iframe').frame_locator('iframe')
           .frame_locator('iframe').locator('h1')).to_contain_text('Example Domain')
    details = page.locator('#details-button')
    expect(details).to_be_visible()
    assert details.evaluate('el => getComputedStyle(el).whiteSpace') == 'nowrap'
    assert details.bounding_box()['height'] < 50
    wrapper = page.locator('.capture-wrapper')
    assert wrapper.evaluate('el => parseFloat(getComputedStyle(el).paddingLeft)') == 0
    assert wrapper.evaluate('el => parseFloat(getComputedStyle(el).paddingRight)') == 0
    account = page.locator('#upper_right_menu .dropdown-toggle')
    assert account.bounding_box()['width'] < 200
    header_height = page.locator('header').bounding_box()['height']
    account.click()
    expect(page.get_by_role('button', name='Log out')).to_be_visible()
    assert abs(page.locator('header').bounding_box()['height'] - header_height) <= 1
    menu = page.locator('#upper_right_menu .dropdown-menu').bounding_box()
    assert menu['x'] >= 0
    assert menu['x'] + menu['width'] <= width
    page.keyboard.press('Escape')
    expect(page.get_by_role('button', name='Log out')).to_be_hidden()
