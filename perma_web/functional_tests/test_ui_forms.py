"""
Behavioral contract for forms, validation, and error display.

Written against Bootstrap 3 and must keep passing on Bootstrap 5. Bootstrap 5
renames or removes most of the classes this markup currently relies on
(.form-group, .control-label, .help-block, .has-error, .checkbox/.radio), so
these assertions describe *behavior and semantics* instead: accessible name,
label<->input association, aria state, and visible/readable error text.

Covers contact, login, sign-up, and profile-settings -- the forms named in the
Phase 4 sub-batch 4A assignment. `test_contact.py` already covers the contact
form's submission/honeypot/no-JS paths; this file extends the contract
(label association, validation-failure display, aria-invalid wiring) rather
than duplicating it.

Two pre-existing facts about the current markup shaped what is and isn't
asserted here:

- `includes/fieldset.html` never gives an error or help-text element an `id`.
  Django auto-adds `aria-describedby` on an invalid field pointing at
  `{id}_error`, but no element with that id exists, so the association is
  broken for assistive tech today. This is pinned as a defect in the final
  report, not asserted as working here.
- None of these four forms carry Perma's `.text-input` class (global.js's
  focus/`.text-input-active` hook) or contain a checkbox/radio field -- both
  are scoped to other pages (e.g. the dashboard create-link box) -- so
  neither is exercised in this file.
"""

import pytest
from playwright.sync_api import expect


@pytest.mark.uses_storage
def test_contact_form_fields_are_labeled_and_visible(page, ui_urls) -> None:
    """Every visible contact-form input resolves by its label, proving the association survives a markup rewrite."""
    page.goto(ui_urls("contact"))

    expect(page.get_by_label("Your email address", exact=True)).to_be_visible()
    expect(page.get_by_label("Message", exact=True)).to_be_visible()


@pytest.mark.uses_storage
def test_contact_form_missing_message_shows_readable_error(page, ui_urls, mailoutbox) -> None:
    """A required field left blank renders a message the user can read and marks the field invalid, without sending mail."""
    page.goto(ui_urls("contact"))

    page.get_by_label("Your email address", exact=True).fill("functional_test_user@example.com")
    # Message left blank. Bypass the browser's native "required" tooltip so
    # the submit actually reaches Django's server-rendered error instead.
    page.locator(".contact-form form").evaluate("form => form.noValidate = true")
    page.locator(".contact-form button[type=submit]").click()

    error = page.locator(".contact-form").get_by_text("This field is required.")
    expect(error).to_be_visible()
    expect(page.get_by_label("Message", exact=True)).to_have_attribute("aria-invalid", "true")
    assert len(mailoutbox) == 0


@pytest.mark.uses_storage
def test_login_form_fields_are_labeled_and_visible(page, ui_urls) -> None:
    """The login form's username and password inputs resolve by their labels."""
    page.goto(ui_urls("user_management_limited_login"))

    expect(page.get_by_label("Email address", exact=True)).to_be_visible()
    expect(page.get_by_label("Password", exact=True)).to_be_visible()


@pytest.mark.uses_storage
def test_login_with_bad_credentials_shows_readable_error(page, ui_urls, user) -> None:
    """A wrong password produces a readable error and the account menu never appears."""
    page.goto(ui_urls("user_management_limited_login"))

    page.get_by_label("Email address", exact=True).fill(user.username)
    page.get_by_label("Password", exact=True).fill("not-the-real-password")
    page.locator("button.btn.login").click()

    error = page.get_by_text(
        "Please enter a correct email address and password. "
        "Note that both fields may be case-sensitive."
    )
    expect(error).to_be_visible()
    expect(page.get_by_role("button", name="Main Dropdown")).to_be_hidden()


@pytest.mark.uses_storage
def test_sign_up_form_fields_are_labeled_and_visible(page, ui_urls) -> None:
    """The individual sign-up form's name and email inputs resolve by their labels."""
    page.goto(ui_urls("sign_up"))

    expect(page.get_by_label("First name", exact=True)).to_be_visible()
    expect(page.get_by_label("Last name", exact=True)).to_be_visible()
    expect(page.get_by_label("Email address", exact=True)).to_be_visible()


@pytest.mark.uses_storage
def test_sign_up_with_invalid_email_shows_readable_error(page, ui_urls, mailoutbox) -> None:
    """A malformed email renders a readable error and marks the field invalid, without creating an account."""
    page.goto(ui_urls("sign_up"))

    page.get_by_label("First name", exact=True).fill("Test")
    page.get_by_label("Last name", exact=True).fill("User")
    page.get_by_label("Email address", exact=True).fill("not-an-email")
    # The email input's type=email triggers native format validation before
    # Django ever sees the value; bypass it to exercise the server-side error.
    page.locator(".signup-learnMore-form form").evaluate("form => form.noValidate = true")
    page.locator(".signup-learnMore-form button[type=submit]").click()

    error = page.locator(".signup-learnMore-form").get_by_text("Enter a valid email address.")
    expect(error).to_be_visible()
    expect(page.get_by_label("Email address", exact=True)).to_have_attribute("aria-invalid", "true")
    assert len(mailoutbox) == 0


@pytest.mark.uses_storage
def test_profile_form_fields_are_labeled_and_prefilled(page, ui_urls, user, log_in) -> None:
    """The logged-in profile form's inputs resolve by their labels and carry the user's current data."""
    log_in(page, user)
    page.goto(ui_urls("settings_profile"))

    expect(page.get_by_label("First name", exact=True)).to_be_visible()
    expect(page.get_by_label("Last name", exact=True)).to_be_visible()
    email_field = page.get_by_label("Email address", exact=True)
    expect(email_field).to_be_visible()
    expect(email_field).to_have_value(user.username)


@pytest.mark.uses_storage
def test_profile_form_missing_email_shows_readable_error(page, ui_urls, user, log_in) -> None:
    """Clearing the required email field renders a readable error and blocks the save, instead of silently failing."""
    log_in(page, user)
    page.goto(ui_urls("settings_profile"))

    page.get_by_label("Email address", exact=True).fill("")
    page.locator("form.change-user").evaluate("form => form.noValidate = true")
    page.locator("form.change-user button[type=submit]").click()

    error = page.locator("form.change-user").get_by_text("This field is required.")
    expect(error).to_be_visible()
    expect(page.get_by_label("Email address", exact=True)).to_have_attribute("aria-invalid", "true")
    expect(page.get_by_text("Profile saved!")).to_be_hidden()
