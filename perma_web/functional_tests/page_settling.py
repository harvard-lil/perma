"""Bring a loaded page to a stable state before it is photographed."""

from playwright.sync_api import Page


def settle_page(page: Page) -> None:
    """
    Wait until the page's layout has stopped changing, so a screenshot is repeatable.

    Waits for the network to go idle, forces lazy images to load, then waits for
    webfonts. Call it after navigation and before `page.screenshot()`; it returns
    nothing and raises Playwright's `TimeoutError` if the network never idles.
    """
    # Webfonts and late XHR change layout; shoot only once both settle.
    page.wait_for_load_state("networkidle")
    # Full-page shots don't scroll, so below-the-fold lazy images may never load; which ones varies by engine.
    page.evaluate(
        """() => Promise.all([...document.querySelectorAll('img[loading="lazy"]')].map(img => {
            img.loading = "eager";
            return img.decode().catch(() => {});
        }))"""
    )
    page.evaluate("document.fonts.ready.then(() => true)")
