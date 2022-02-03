import pytest
import re

two_minutes = 120*1000

def test_homepage(page, urls):
    page.goto(urls.homepage)
    assert page.title() == "Perma.cc"
    page.locator('body')


@pytest.fixture
def logged_in_user(page, urls, user):
    page.goto(urls.login)
    username = page.locator('#id_username')
    username.focus()
    username.type(user.username)
    password = page.locator('#id_password')
    password.focus()
    password.type(user.password)
    page.locator("button.btn.login").click()
    return page

def test_example_dot_com(logged_in_user):
    url_field = logged_in_user.locator('#rawUrl')
    url_field.focus()
    url_field.type("https://example.com/")
    logged_in_user.locator('#addlink').click()
    logged_in_user.wait_for_url(re.compile('/[A-Za-z0-9]{4}-[A-Za-z0-9]{4}$'), timeout=two_minutes)
    replay_frame = logged_in_user.frame('https://example.com/')
    assert logged_in_user.title() == 'Perma | Example Domain'
    assert "Example Domain" in replay_frame.locator('h1').text_content()
