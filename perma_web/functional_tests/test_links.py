import re

two_minutes = 120 * 1000


def test_create_link_warc_playback(page, user, log_in_user) -> None:
    """It should be possible to successfully create a link from a URL"""
    log_in_user(page, user)

    url_field = page.locator('#rawUrl')
    url_field.focus()
    url_field.type("https://example.com/")
    page.locator('#addlink').click()
    page.wait_for_url(re.compile('/[A-Za-z0-9]{4}-[A-Za-z0-9]{4}$'), timeout=two_minutes)
    assert page.title() == 'Perma | Example Domain'
    assert"Example Domain" in page \
        .frame_locator('.archive-iframe') \
        .frame_locator('iframe') \
        .frame_locator('iframe') \
        .locator('h1').inner_text()
    # Verify we are seing a WARC playback, not a WACZ playback
    assert ".warc.gz?" in page.content()
    assert ".wacz?" not in page.content()



def test_link_required(logged_in_user) -> None:
def test_link_required(page_with_logged_in_user) -> None:


def test_link_required(page, user, log_in_user) -> None:
    """A friendly message should be displayed if the field is omitted"""
    log_in_user(page, user)

    page.locator('#rawUrl')
    page.locator('#addlink').click()
    assert "URL cannot be empty" in page.locator("p.message-large").text_content()


def test_upload_nonexistent(page, user, log_in_user) -> None:
    """A modal should be displayed if the user input a domain we can't resolve"""
    log_in_user(page, user)

    url_field = page.locator('#rawUrl')
    url_field.focus()
    url_field.type("https://fakedomain.fakething/")
    page.locator('#addlink').click()
    assert "Couldn't resolve domain." in page.locator("p.message-large").text_content()

