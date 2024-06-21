import pytest

def test_create_folder(page_with_logged_in_user, urls):
    """Clicking the add button should create a new folder"""
    page_with_logged_in_user.goto(urls.folders)
    folder_count = page_with_logged_in_user.locator('.jstree-last').count()
    page_with_logged_in_user.locator('.new-folder').click()
    page_with_logged_in_user.locator(f":nth-match(.jstree-last, {folder_count + 1})").wait_for()


@pytest.mark.xfail(reason="Needs more work to be reliable")
def test_delete_folder(page_with_logged_in_user, urls):
    """Clicking the folder delete button should delete an existing empty folder"""
    page_with_logged_in_user.goto(urls.folders)

    # Create a new folder and wait for it to exist
    folder_count = page_with_logged_in_user.locator('.jstree-last').count()
    page_with_logged_in_userr.locator('.new-folder').click()
    new_folder = page_with_logged_in_user.locator(f":nth-match(.jstree-last, {folder_count + 1})")
    new_folder.wait_for()

    # Now delete it
    new_folder.click(button="right")
    with page_with_logged_in_user.expect_navigation():
        page_with_logged_in_user.click("text=Delete")

    new_folder.wait_for(state="hidden")
