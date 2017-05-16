from selenium.common.exceptions import NoSuchElementException


def forbes_post_load(browser):
    # Wait for splash page to auto redirect
    from perma.tasks import repeat_until_truthy  # avoid circular import
    current_url = browser.current_url
    if '/welcome' in current_url:
        # attempt to click "Continue"
        try:
            browser.find_element_by_css_selector('.continue-button').click()
        except NoSuchElementException:
            pass
        # wait until URL changes
        repeat_until_truthy(lambda: browser.current_url != current_url)