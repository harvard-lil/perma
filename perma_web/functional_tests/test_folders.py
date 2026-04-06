from typing import Callable

from conftest import URLs, User
from playwright.sync_api import Locator, Page, expect
import pytest


@pytest.fixture
def sponsored_user() -> User:
    return User('test_sponsored_user@example.com', 'pass')


@pytest.fixture
def folder_tree_page(page: Page, user: User, log_in_user: Callable[[Page, User], None], urls: URLs):
    log_in_user(page, user)
    page.goto(urls.folders)
    page.locator('#folder-tree [role="treeitem"]').first.wait_for()
    yield page


@pytest.fixture
def sponsored_folder_tree_page(
    page: Page, sponsored_user: User, log_in_user: Callable[[Page, User], None], urls: URLs
):
    log_in_user(page, sponsored_user)
    page.goto(urls.folders)
    page.locator('#folder-tree [role="treeitem"]').first.wait_for()
    yield page


@pytest.fixture
def sponsored_folder(sponsored_folder_tree_page: Page):
    return sponsored_folder_tree_page.locator(
        '#folder-tree [role="treeitem"][aria-disabled="true"]'
    )


def create_folder(folder_tree_page: Page, name: str = None) -> Locator:
    folder_count = folder_tree_page.locator('#folder-tree [role="treeitem"]').count()
    folder_tree_page.locator('.new-folder').click()
    folder_tree_page.locator('input.folder-rename-input')
    if name:
        folder_tree_page.locator('input.folder-rename-input').fill(name)
    folder_tree_page.keyboard.press('Enter')
    new_item = folder_tree_page.locator('#folder-tree [role="treeitem"]').nth(folder_count)
    return new_item


def test_create_folder(folder_tree_page: Page):
    folder_count = folder_tree_page.locator('#folder-tree [role="treeitem"]').count()
    folder_tree_page.locator('.new-folder').click()
    folder_tree_page.locator('input.folder-rename-input')
    folder_tree_page.keyboard.press('Enter')
    new_item = folder_tree_page.locator('#folder-tree [role="treeitem"]').nth(folder_count)
    expect(new_item).to_be_visible()


def test_delete_folder(folder_tree_page: Page):
    new_folder = create_folder(folder_tree_page)
    new_folder.click()

    folder_tree_page.on('dialog', lambda dialog: dialog.accept())
    folder_tree_page.locator('.delete-folder').click()

    expect(new_folder).not_to_be_visible()


def test_create_and_rename_folder(folder_tree_page: Page):
    folder_tree_page.locator('.new-folder').click()
    rename_input = folder_tree_page.locator('input.folder-rename-input')

    rename_input.fill('My Custom Folder')
    folder_tree_page.keyboard.press('Enter')

    expect(rename_input).not_to_be_visible()
    expect(folder_tree_page.locator('#folder-tree')).to_contain_text('My Custom Folder')


def test_rename_folder_via_toolbar(folder_tree_page: Page):
    folder = create_folder(folder_tree_page)
    folder.click()

    folder_tree_page.locator('.edit-folder').click()
    rename_input = folder_tree_page.locator('input.folder-rename-input')
    rename_input.wait_for()

    rename_input.fill('Renamed Folder')
    folder_tree_page.keyboard.press('Enter')

    rename_input.wait_for(state='hidden')
    expect(folder_tree_page.locator('#folder-tree')).to_contain_text('Renamed Folder')


def test_cannot_rename_root_folder(folder_tree_page: Page):
    folder_tree_page.locator('#folder-tree [role="treeitem"]').first.click()
    folder_tree_page.locator('.edit-folder').click()

    toast = folder_tree_page.locator('.popup-alert[role="alert"]')
    expect(toast).to_be_visible()
    expect(toast).to_contain_text('cannot be moved or renamed')


def test_expand_collapse_folder(folder_tree_page: Page):
    user_folder = folder_tree_page.locator('#folder-tree [role="treeitem"]').first
    user_folder.click()
    child_folder = create_folder(folder_tree_page)

    expect(user_folder).to_have_attribute('aria-expanded', 'true')
    expect(child_folder).to_be_visible()

    user_folder.click()
    expect(user_folder).to_have_attribute('aria-expanded', 'false')
    expect(child_folder).not_to_be_visible()

    user_folder.click()
    expect(user_folder).to_have_attribute('aria-expanded', 'true')
    expect(child_folder).to_be_visible()


def test_folder_selection(folder_tree_page: Page):
    folder_a = create_folder(folder_tree_page, 'Folder A')
    folder_b = create_folder(folder_tree_page, 'Folder B')

    folder_a.click()
    expect(folder_a).to_have_attribute('aria-selected', 'true')

    folder_b.click()
    expect(folder_b).to_have_attribute('aria-selected', 'true')


def test_folder_selection_updates_url(folder_tree_page: Page):
    url_initial = folder_tree_page.url

    create_folder(folder_tree_page)
    folder = folder_tree_page.locator('#folder-tree [role="treeitem"]').nth(1)
    folder.click()

    folder_path = folder.get_attribute('data-folder-path')
    assert folder_path is not None
    assert f'folder={folder_path}' not in url_initial

    url_updated = folder_tree_page.url
    assert f'folder={folder_path}' in url_updated


def test_keyboard_navigation(folder_tree_page: Page):
    folder_a = create_folder(folder_tree_page, 'Folder A')
    folder_b = create_folder(folder_tree_page, 'Folder B')

    items = folder_tree_page.locator('#folder-tree [role="treeitem"]')
    user_folder = items.nth(0)

    user_folder.click()
    expect(user_folder).to_be_focused()

    folder_tree_page.keyboard.press('ArrowDown')
    expect(folder_a).to_be_focused()

    folder_tree_page.keyboard.press('ArrowDown')
    expect(folder_b).to_be_focused()

    folder_tree_page.keyboard.press('ArrowUp')
    expect(folder_a).to_be_focused()


def test_sponsored_folder_can_be_focused_but_not_selected(sponsored_folder: Locator):
    expect(sponsored_folder).to_be_visible()
    expect(sponsored_folder).to_be_disabled()

    classes_before_click = sponsored_folder.get_attribute('class').split()
    assert 'focused' not in classes_before_click
    expect(sponsored_folder).to_have_attribute('aria-selected', 'false')

    # For some reason sponsored_folder.click times out; maybe a z-index issue?
    sponsored_folder.evaluate('element => element.click()')

    classes_after_click = sponsored_folder.get_attribute('class').split()
    assert 'focused' in classes_after_click
    expect(sponsored_folder).to_have_attribute('aria-selected', 'false')
