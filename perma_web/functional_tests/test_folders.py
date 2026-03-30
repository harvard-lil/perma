import pytest

def test_create_folder(page, user, log_in_user, urls):
    """Clicking the add button should create a new folder"""
    log_in_user(page, user)

    page.goto(urls.folders)
    folder_count = page.locator('#folder-tree [role="treeitem"]').count()
    page.locator('.new-folder').click()
    page.locator(f':nth-match(#folder-tree [role="treeitem"], {folder_count + 1})').wait_for()


@pytest.mark.xfail(reason="Needs more work to be reliable")
def test_delete_folder(page, user, log_in_user, urls):
    """Clicking the folder delete button should delete an existing empty folder"""
    log_in_user(page, user)
    page.goto(urls.folders)

    # Create a new folder and wait for it to exist
    folder_count = page.locator('#folder-tree [role="treeitem"]').count()
    page.locator('.new-folder').click()
    new_folder = page.locator(f':nth-match(#folder-tree [role="treeitem"], {folder_count + 1})')
    new_folder.wait_for()

    # Select and delete it
    new_folder.click()
    page.locator('.delete-folder').click()
    page.on("dialog", lambda dialog: dialog.accept())

    new_folder.wait_for(state="hidden")
