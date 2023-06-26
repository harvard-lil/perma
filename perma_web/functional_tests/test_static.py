
def test_homepage(page, urls) -> None:
    """The homepage should render correctly"""
    page.goto(urls.homepage)
    assert page.title() == "Perma.cc"

def test_about(page, urls) -> None:
    """The About page should render correctly"""
    page.goto(urls.about)
    assert page.title() == "Perma.cc | About"

