
def test_contact(page, urls, mailoutbox) -> None:
    """The Contact form should submit"""
    msg = "I've got important things to say."
    email = "functional_test_user@example.com"

    page.goto(urls.contact)

    email_field = page.locator('#id_email')
    email_field.focus()
    email_field.type(email)
    message_field = page.locator('#id_box2')
    message_field.focus()
    message_field.type(msg)

    page.locator('.contact-form button[type=submit]').click()

    assert page.title() == "Perma.cc | Thanks"
    assert len(mailoutbox) == 1
    m = mailoutbox[0]
    assert msg in m.body


def test_contact_no_js(page, urls, mailoutbox, caplog) -> None:
    """The Contact form should submit, but be rejected."""
    msg = "I've got important things to say."
    email = "functional_test_user@example.com"

    page.goto(urls.contact)
    # Remove the form's submit event listener
    page.evaluate('() => {let elem = document.querySelector(".contact-form"); elem.innerHTML = elem.innerHTML;}')

    email_field = page.locator('#id_email')
    email_field.focus()
    email_field.type(email)
    message_field = page.locator('#id_box2')
    message_field.focus()
    message_field.type(msg)

    page.locator('.contact-form button[type=submit]').click()

    assert page.title() == "Perma.cc | Thanks"
    assert any("Suppressing invalid form submission" in msg for msg in caplog.messages)
    assert len(mailoutbox) == 0


def test_contact_no_js_logged_in(page, user, log_in_user, urls, mailoutbox, caplog) -> None:
    """The Contact form should submit, and not be rejected despite no JS."""
    msg = "I've got important things to say."

    log_in_user(page, user)

    page.goto(urls.contact)
    # Remove the form's submit event listener
    page.evaluate('() => {let elem = document.querySelector(".contact-form"); elem.innerHTML = elem.innerHTML;}')

    message_field = page.locator('#id_box2')
    message_field.focus()
    message_field.type(msg)

    page.locator('.contact-form button[type=submit]').click()

    assert len(mailoutbox) == 1
    m = mailoutbox[0]
    assert msg in m.body
