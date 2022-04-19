import pytest

class Login:
    def __init__(self, username, password):
        self.username = username
        self.password = password


class URLs:
    def __init__(self, base_url):
        for name, url in [('homepage', '/'),
                          ('login', '/login'),]:
            setattr(self, name, base_url+url)


@pytest.fixture
def urls():
    return URLs("https://perma.test:8000")


@pytest.fixture
def user():
    return Login("functional_test_user@example.com", "pass")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "ignore_https_errors": True
    }
