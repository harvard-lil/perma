import pytest

def test_create_folder(logged_in_user, urls):
    """Clicking the add button should create a new folder"""
    logged_in_user.goto(urls.folders)
    folder_count = logged_in_user.locator('.jstree-last').count()
    logged_in_user.locator('.new-folder').click()
    logged_in_user.locator(f":nth-match(.jstree-last, {folder_count + 1})").wait_for()


@pytest.mark.xfail(reason="Needs more work to be reliable")
def test_delete_folder(logged_in_user, urls):
    """Clicking the folder delete button should delete an existing empty folder"""
    logged_in_user.goto(urls.folders)

    # Create a new folder and wait for it to exist
    folder_count = logged_in_user.locator('.jstree-last').count()
    logged_in_user.locator('.new-folder').click()
    new_folder = logged_in_user.locator(f":nth-match(.jstree-last, {folder_count + 1})")
    new_folder.wait_for()

    # Now delete it
    new_folder.click(button="right")
    with logged_in_user.expect_navigation():
        logged_in_user.click("text=Delete")

    new_folder.wait_for(state="hidden")
