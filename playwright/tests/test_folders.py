
def test_create_folder(logged_in_user, urls):
    """Clicking the add button should create a new folder"""
    logged_in_user.goto(urls.folders)
    folder_count = logged_in_user.locator('.jstree-last').count()
    logged_in_user.locator('.new-folder').click()
    assert logged_in_user.locator('.jstree-last').count() == folder_count + 1