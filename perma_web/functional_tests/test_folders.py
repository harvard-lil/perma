import pytest

def test_create_folder(page, user, log_in_user, urls):
    """Clicking the add button should create a new folder"""
    log_in_user(page, user)

    page.goto(urls.folders)
    folder_count = page.locator('.jstree-last').count()
    page.locator('.new-folder').click()
    page.locator(f":nth-match(.jstree-last, {folder_count + 1})").wait_for()


@pytest.mark.xfail(reason="Needs more work to be reliable")
def test_delete_folder(page, user, log_in_user, urls):
    """Clicking the folder delete button should delete an existing empty folder"""
    log_in_user(page, user)
    page.goto(urls.folders)

    # Create a new folder and wait for it to exist
    folder_count = page.locator('.jstree-last').count()
    page.locator('.new-folder').click()
    new_folder = page.locator(f":nth-match(.jstree-last, {folder_count + 1})")
    new_folder.wait_for()

    # Now delete it
    new_folder.click(button="right")
    with page.expect_navigation():
        page.click("text=Delete")

    new_folder.wait_for(state="hidden")
