import re
from playwright.sync_api import expect

two_minutes = 120 * 1000

def create_link(page):
    """
    A helper:
    clicks into the "Create a link" input,
    submits a link creation request,
    and waits for the page to redirect playback.

    Expect timeouts on failed attempt.
    """
    url_field = page.locator('#rawUrl')
    url_field.focus()
    url_field.type("https://example.com/")
    page.locator('#addlink').click()
    page.wait_for_url(re.compile('/[A-Za-z0-9]{4}-[A-Za-z0-9]{4}$'), timeout=two_minutes)
    expect(page).to_have_title('Perma | Example Domain')
    expect(page.frame_locator('.archive-iframe')
               .frame_locator('iframe')
               .frame_locator('iframe')
               .locator('h1')).to_contain_text("Example Domain")

def test_create_link_warc_playback(page, user, log_in_user) -> None:
    """
    It should be possible to successfully create a link from a URL.

    This user (no feature flag) should see a WARC playback.
    """
    log_in_user(page, user)
    create_link(page)

    # Verify we are seing a WARC playback, not a WACZ playback
    assert ".warc.gz?" in page.content()
    assert ".wacz?" not in page.content()


def test_create_link_wacz_playback(page, wacz_user, log_in_user) -> None:
    """
    It should be possible to successfully create a link from a URL.

    This user (with feature flag set) should see a WACZ playback.
    """
    log_in_user(page, wacz_user)
    create_link(page)

    # Verify we are seing a WACZ playback, not a WARC playback
    assert ".warc.gz?" not in page.content()
    assert ".wacz?" in page.content()


def test_link_required(page, user, log_in_user) -> None:
    """A friendly message should be displayed if the field is omitted"""
    log_in_user(page, user)

    page.locator('#addlink').click()
    expect(page.locator("#error-container")).to_contain_text("URL cannot be empty")

def test_upload_nonexistent(page, user, log_in_user) -> None:
    """A modal should be displayed if the user input a domain we can't resolve"""
    log_in_user(page, user)

    url_field = page.locator('#rawUrl')
    url_field.focus()
    url_field.type("https://fakedomain.fakething/")
    page.locator('#addlink').click()
    expect(page.locator("#error-container")).to_contain_text("Couldn't resolve domain.")

def test_bookmarklet_redirect(page, user, log_in_user, urls) -> None:
    """Test that the URL parameter prepopulates the input field for the bookmarklet."""
    log_in_user(page, user)

    # Navigate to the create link page with a URL parameter
    test_url = "https://example.com"
    page.goto(f"{urls.bookmarklet}?v=1&url={test_url}")
    
    # Check if the input field is prepopulated with the URL
    url_field = page.locator('#rawUrl')
    expect(url_field).to_have_value(test_url)

def test_reminder_suppression(page, user, log_in_user):
    """Test that the reminder suppression cookie works."""
    log_in_user(page, user)
    expect(page.locator("#browser-tools-message")).to_be_visible()
    page.locator(".close-browser-tools").click()
    expect(page.locator("#browser-tools-message")).not_to_be_visible()
    page.reload()
    expect(page.locator("#browser-tools-message")).not_to_be_visible()

