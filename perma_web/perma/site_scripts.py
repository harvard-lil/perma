from selenium.common.exceptions import NoSuchElementException, TimeoutException
from time import sleep

def forbes_post_load(browser):
    # Wait for splash page to auto redirect
    from perma.tasks import repeat_until_truthy  # avoid circular import
    try:
        current_url = browser.current_url
    except TimeoutException:
        return

    if '/welcome' in current_url:
        # attempt to click "Continue"
        try:
            browser.find_element_by_css_selector('.continue-button').click()
        except (NoSuchElementException, TimeoutException):
            pass
        # wait until URL changes
        repeat_until_truthy(lambda: browser.current_url != current_url)

def iurisprudentia_post_load(browser):
    # wait for slow-to-start AJAX requests to start
    sleep(2)
