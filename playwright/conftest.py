from dataclasses import dataclass
import pytest

URL_MAP = {
    'homepage': '/',
    'login': '/login',
    'about': '/about',
    'folders': '/manage/create',
}
@dataclass
class User:
    username: str
    password: str


@pytest.fixture
def user() -> User:
    return User("functional_test_user@example.com", "pass")

class URLs:
    def __init__(self, base_url):
        for name, url in URL_MAP.items():
            setattr(self, name, base_url + url)

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "ignore_https_errors": True
    }

@pytest.fixture
def urls():
    return URLs("https://perma.test:8000")

@pytest.fixture
def logged_in_user(page, urls, user):
    """Actually log in the desired user"""
    page.goto(urls.login)
    username = page.locator('#id_username')
    username.focus()
    username.type(user.username)
    password = page.locator('#id_password')
    password.focus()
    password.type(user.password)
    page.locator("button.btn.login").click()
    return page