
def test_log_out(logged_in_user):
    logged_in_user.locator(".dropdown-toggle").click()
    logged_in_user.locator("button", has_text="Log out").click()
    assert logged_in_user.locator("h1", has_text="You have been logged out")