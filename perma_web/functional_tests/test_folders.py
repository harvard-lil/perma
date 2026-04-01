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


def create_folder(folder_tree_page: Page):
    count_next = folder_tree_page.locator('#folder-tree [role="treeitem"]').count() + 1
    folder_tree_page.locator('.new-folder').click()
    folder_tree_page.locator('input.folder-rename-input').wait_for()
    folder_tree_page.keyboard.press('Escape')
    new_item = folder_tree_page.locator(f':nth-match(#folder-tree [role="treeitem"], {count_next})')
    new_item.wait_for()
    return count_next


def test_create_folder(folder_tree_page: Page):
    folder_count = folder_tree_page.locator('#folder-tree [role="treeitem"]').count()
    folder_tree_page.locator('.new-folder').click()
    folder_tree_page.locator(
        f':nth-match(#folder-tree [role="treeitem"], {folder_count + 1})'
    ).wait_for()


def test_delete_folder(folder_tree_page: Page):
    folder_count = create_folder(folder_tree_page)
    new_folder = folder_tree_page.locator(
        f':nth-match(#folder-tree [role="treeitem"], {folder_count})'
    )
    new_folder.click()

    folder_tree_page.on('dialog', lambda dialog: dialog.accept())
    folder_tree_page.locator('.delete-folder').click()

    new_folder.wait_for(state='hidden')


def test_create_and_rename_folder(folder_tree_page: Page):
    folder_tree_page.locator('.new-folder').click()
    rename_input = folder_tree_page.locator('input.folder-rename-input')
    rename_input.wait_for()

    rename_input.fill('My Custom Folder')
    folder_tree_page.keyboard.press('Enter')

    rename_input.wait_for(state='hidden')
    expect(folder_tree_page.locator('#folder-tree')).to_contain_text('My Custom Folder')


def test_rename_folder_via_toolbar(folder_tree_page: Page):
    folder_count = create_folder(folder_tree_page)
    folder = folder_tree_page.locator(f':nth-match(#folder-tree [role="treeitem"], {folder_count})')
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
    root_folder = folder_tree_page.locator('#folder-tree [role="treeitem"]').first
    root_folder.click()

    folder_count = create_folder(folder_tree_page)
    child_folder = folder_tree_page.locator(
        f':nth-match(#folder-tree [role="treeitem"], {folder_count})'
    )

    expect(root_folder).to_have_attribute('aria-expanded', 'true')
    expect(child_folder).to_be_visible()

    # First click re-selects root (which was deselected by create_folder);
    # second click collapses it (collapse requires wasAlreadySelected).
    root_folder.click()
    root_folder.click()
    expect(root_folder).to_have_attribute('aria-expanded', 'false')
    expect(child_folder).not_to_be_visible()

    root_folder.click()
    expect(root_folder).to_have_attribute('aria-expanded', 'true')
    expect(child_folder).to_be_visible()


def test_folder_selection(folder_tree_page: Page):
    create_folder(folder_tree_page)
    create_folder(folder_tree_page)

    items = folder_tree_page.locator('#folder-tree [role="treeitem"]')
    first = items.nth(1)
    second = items.nth(2)

    first.click()
    expect(first).to_have_attribute('aria-selected', 'true')
    expect(second).to_have_attribute('aria-selected', 'false')

    second.click()
    expect(second).to_have_attribute('aria-selected', 'true')
    expect(first).to_have_attribute('aria-selected', 'false')


def test_keyboard_navigation(folder_tree_page: Page):
    create_folder(folder_tree_page)
    create_folder(folder_tree_page)

    items = folder_tree_page.locator('#folder-tree [role="treeitem"]')
    root = items.nth(0)
    first_child = items.nth(1)
    second_child = items.nth(2)

    root.click()
    expect(root).to_be_focused()

    folder_tree_page.keyboard.press('ArrowDown')
    expect(first_child).to_be_focused()

    folder_tree_page.keyboard.press('ArrowDown')
    expect(second_child).to_be_focused()

    folder_tree_page.keyboard.press('ArrowUp')
    expect(first_child).to_be_focused()


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
