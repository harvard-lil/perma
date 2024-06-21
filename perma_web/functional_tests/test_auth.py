
def test_log_out(page_with_logged_in_user):
    page_with_logged_in_user.locator(".dropdown-toggle").click()
    page_with_logged_in_user.locator("button", has_text="Log out").click()
    assert page_with_logged_in_user.locator("h1", has_text="You have been logged out")
