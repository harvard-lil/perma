
def test_homepage(page, urls) -> None:
    """The homepage should render correctly"""
    page.goto(urls.homepage)
    assert page.title() == "Perma.cc"

def test_about(page, urls) -> None:
    """The About page should list the set of partners"""
    page.goto(urls.about)
    assert "About" in page.title()
    assert page.locator('.perma-partner').count() > 0
