import re

two_minutes = 120 * 1000


def test_create_link_warc_playback(page_with_logged_in_user) -> None:
    """It should be possible to successfully create a link from a URL"""
    url_field = page_with_logged_in_user.locator('#rawUrl')
    url_field.focus()
    url_field.type("https://example.com/")
    page_with_logged_in_user.locator('#addlink').click()
    page_with_logged_in_user.wait_for_url(re.compile('/[A-Za-z0-9]{4}-[A-Za-z0-9]{4}$'), timeout=two_minutes)
    assert page_with_logged_in_user.title() == 'Perma | Example Domain'
    assert"Example Domain" in page_with_logged_in_user \
        .frame_locator('.archive-iframe') \
        .frame_locator('iframe') \
        .frame_locator('iframe') \
        .locator('h1').inner_text()


def test_link_required(logged_in_user) -> None:
def test_link_required(page_with_logged_in_user) -> None:
    """A friendly message should be displayed if the field is omitted"""
    page_with_logged_in_user.locator('#rawUrl')
    page_with_logged_in_user.locator('#addlink').click()
    assert "URL cannot be empty" in page_with_logged_in_user.locator("p.message-large").text_content()


def test_upload_nonexistent(page_with_logged_in_user) -> None:
    """A modal should be displayed if the user input a domain we can't resolve"""
    url_field = page_with_logged_in_user.locator('#rawUrl')
    url_field.focus()
    url_field.type("https://fakedomain.fakething/")
    page_with_logged_in_user.locator('#addlink').click()
    assert "Couldn't resolve domain." in page_with_logged_in_user.locator("p.message-large").text_content()

