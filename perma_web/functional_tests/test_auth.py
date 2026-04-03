import pytest


@pytest.mark.uses_storage
def test_log_out(page, user, log_in_user):
    log_in_user(page, user)
    page.get_by_role("button", name="Main Dropdown").click()
    page.locator("button", has_text="Log out").click()
    assert page.locator("h1", has_text="You have been logged out")
