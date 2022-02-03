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
    return URLs("http://perma.test:8000")


@pytest.fixture
def user():
    return Login("test_user@example.com", "pass")
