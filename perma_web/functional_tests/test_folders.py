import pytest

from perma.models import Folder, LinkUser


@pytest.mark.uses_storage
def test_create_folder(page, user, log_in_user, urls):
    """Clicking the add button should create a new folder"""
    log_in_user(page, user)

    page.goto(urls.folders)
    folder_count = page.locator('.jstree-last').count()
    page.locator('.new-folder').click()
    page.locator(f":nth-match(.jstree-last, {folder_count + 1})").wait_for()


@pytest.mark.uses_storage
def test_folder_names_render_as_text(page, user, log_in_user, urls):
    """Folder names must not be interpreted as HTML by jsTree."""
    account = LinkUser.objects.get(email=user.username)
    payload = '<img src=x onerror="window.folderNameXss = true">'
    folder = Folder.objects.create(
        name=payload,
        created_by=account,
        parent=account.root_folder,
    )

    log_in_user(page, user)
    page.goto(f"{urls.folders}?folder={account.root_folder_id}-{folder.pk}")

    page.locator('#folder-tree').get_by_text(payload, exact=True).wait_for()
    assert page.locator('#folder-tree img[src="x"]').count() == 0
    assert page.evaluate('window.folderNameXss') is None


@pytest.mark.uses_storage
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


@pytest.mark.uses_storage
def test_stale_folder_path_recovers_after_move(page, user, log_in_user, urls):
    account = LinkUser.objects.get(email=user.username)
    parent = Folder.objects.create(name='Move destination', created_by=account, parent=account.root_folder)
    child = Folder.objects.create(name='Moved folder', created_by=account, parent=parent)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    log_in_user(page, user)
    # Simulate a bookmark saved before the folder moved into its new parent.
    page.goto(f'{urls.folders}?folder={account.root_folder_id}-{child.pk}')
    page.locator('#folder-tree .jstree-clicked').filter(has_text='Moved folder').wait_for()
    assert page.evaluate('new URL(location.href).searchParams.get("folder")') == f'{account.root_folder_id}-{parent.pk}-{child.pk}'
    assert not errors
