"""Layout regressions observed during staging review, independent of Bootstrap version."""

import pytest
from playwright.sync_api import expect


@pytest.mark.uses_storage
@pytest.mark.parametrize('width', [375, 768, 1200])
def test_organization_list_columns(page, ui_urls, staff_user, log_in, width):
    log_in(page, staff_user)
    page.set_viewport_size({'width': width, 'height': 900})
    page.goto(ui_urls('user_management_manage_organization'))
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
def test_archive_header_and_frame_geometry(page, urls, user, log_in_user):
    page.set_viewport_size({'width': 1440, 'height': 900})
    log_in_user(page, user)
    page.goto(urls.perma_link_with_warc)
    details = page.locator('#details-button')
    expect(details).to_be_visible()
    assert details.evaluate('el => getComputedStyle(el).whiteSpace') == 'nowrap'
    assert details.bounding_box()['height'] < 50
    wrapper = page.locator('.capture-wrapper')
    assert wrapper.evaluate('el => parseFloat(getComputedStyle(el).paddingLeft)') == 0
    assert wrapper.evaluate('el => parseFloat(getComputedStyle(el).paddingRight)') == 0
    account = page.locator('#upper_right_menu .dropdown-toggle')
    assert account.bounding_box()['width'] < 200
    account.click()
    expect(page.get_by_role('button', name='Log out')).to_be_visible()
    page.keyboard.press('Escape')
    expect(page.get_by_role('button', name='Log out')).to_be_hidden()
    expect(page.frame_locator('.archive-iframe').frame_locator('iframe')
           .frame_locator('iframe').locator('h1')).to_contain_text('Example Domain')
