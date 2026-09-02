"""
Behavioral contract for touch activation on the supported mobile matrix.

This file exists to gate the removal of FastClick. Every assertion here
describes what one finger-tap must do -- activate exactly one control, exactly
once, with focus landing where a mouse click would put it -- and never how the
click reaches the page. That is the whole point: FastClick's job was to
synthesize the click itself, so a test that named the mechanism would have to
be rewritten by the very change it is meant to gate.

## Why the user agent is overridden

FastClick 1.0.6 decides whether to attach by sniffing `navigator.userAgent`
(`FastClick.notNeeded`, node_modules/fastclick/lib/fastclick.js:734). Any UA
containing `Chrome/` that is not also Android returns early as "Chrome
desktop, not needed" -- so under the suite's default Chromium UA, FastClick
never attaches, and a touch test run there would pass identically whether the
library were present or absent. That would be a vacuous gate.

The only configuration inside the declared support matrix where FastClick
still attaches is iOS Safari: `notNeeded` has no check for the iOS 9.3 change
that removed the 350ms tap delay, so it falls through to `return false` on
every iPhone to this day. Overriding the UA to iOS Safari reproduces exactly
that code path. What is under test is FastClick's synthetic-click machinery,
which is UA-gated JavaScript rather than engine behavior, so running it on
Blink is faithful; the rendering engine is not the subject.

## Scope

`perma_web/browserslist` (`last 3 versions, not ie < 10`) and the SCSS
breakpoints in `static/css/_vars-global.scss`, as recorded in `developer.md`.
The viewport below is a phone inside `$width-mobile`..`$width-tablet`, so the
navigation is collapsed and the mobile layout is the one being tapped.
"""

import pytest
from playwright.sync_api import expect

# Safari on iPhone and on iPad. The `iPhone`/`iPad` token and the *absence* of
# a `Chrome/` token are the two things FastClick's gate reads; the version
# numbers are ordinary support-matrix currency and carry no logic.
IPHONE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
)
IPAD_UA = (
    "Mozilla/5.0 (iPad; CPU OS 18_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
)

PHONE_VIEWPORT = {"width": 375, "height": 812}
TABLET_VIEWPORT = {"width": 1024, "height": 768}

# A ghost click arrives roughly 300ms after the tap that spawned it. Waiting
# past that window is the assertion, so this is a deliberate fixed wait rather
# than a poll: the test is proving that nothing further happens.
GHOST_CLICK_WINDOW_MS = 600


def _touch_pages(browser, browser_context_args, **overrides):
    context = browser.new_context(**{
        **browser_context_args, "has_touch": True, **overrides
    })
    try:
        yield context.new_page()
    finally:
        context.close()


@pytest.fixture
def touch_page(browser, browser_context_args):
    """A phone-sized, touch-capable page reporting itself as Safari on iPhone."""
    yield from _touch_pages(
        browser, browser_context_args,
        viewport=PHONE_VIEWPORT, user_agent=IPHONE_UA, is_mobile=True,
    )


@pytest.fixture
def tablet_touch_page(browser, browser_context_args):
    """
    A tablet-width touch page reporting itself as Safari on iPad.

    Needed because Perma hides some controls below $width-tablet -- the account
    dropdown toggle among them (`style-responsive.scss`, `.nav > li >
    .dropdown-toggle.navbar-link`), which is exactly the control this phase
    most needs to tap.
    """
    yield from _touch_pages(
        browser, browser_context_args,
        viewport=TABLET_VIEWPORT, user_agent=IPAD_UA, is_mobile=False,
    )


def _count_clicks_on(locator):
    """Start counting click events on one element; returns a reader callable."""
    locator.evaluate(
        "el => { el.__tapCount = 0; el.addEventListener('click', () => { el.__tapCount++; }); }"
    )
    return lambda: locator.evaluate("el => el.__tapCount")


@pytest.mark.uses_storage
def test_tap_opens_the_collapsed_navigation(touch_page, ui_urls) -> None:
    """
    One tap on the navigation toggle reveals the menu.

    This doubles as the strictest double-activation check available on a real
    control: the toggle is a toggle, so a tap delivered twice would open the
    menu and immediately close it again, leaving this assertion failing.
    """
    touch_page.goto(ui_urls("landing"))

    touch_page.get_by_role("button", name="Toggle navigation").tap()

    expect(touch_page.locator("#upper_right_menu")).to_be_visible()


@pytest.mark.uses_storage
def test_second_tap_closes_the_navigation_again(touch_page, ui_urls) -> None:
    """Tapping the toggle a second time collapses the menu."""
    touch_page.goto(ui_urls("landing"))
    toggle = touch_page.get_by_role("button", name="Toggle navigation")

    toggle.tap()
    expect(touch_page.locator("#upper_right_menu")).to_be_visible()
    toggle.tap()

    expect(touch_page.locator("#upper_right_menu")).to_be_hidden()


@pytest.mark.uses_storage
def test_tap_delivers_exactly_one_click_to_its_target(touch_page, ui_urls) -> None:
    """
    A tap produces one click event on the tapped element -- not two.

    Counted directly on the element rather than inferred from its effect, so a
    duplicate that happened to be idempotent would still be caught.
    """
    touch_page.goto(ui_urls("landing"))
    toggle = touch_page.get_by_role("button", name="Toggle navigation")
    clicks = _count_clicks_on(toggle)

    toggle.tap()
    expect(touch_page.locator("#upper_right_menu")).to_be_visible()
    touch_page.wait_for_timeout(GHOST_CLICK_WINDOW_MS)

    assert clicks() == 1


@pytest.mark.uses_storage
def test_tap_activates_only_the_topmost_element(touch_page, ui_urls) -> None:
    """
    A tap on an element that removes itself must not fall through to whatever
    it was covering -- the "ghost click" that a delayed synthetic click causes.

    The two stacked buttons are injected because no Perma page offers a
    self-removing overlay above a clickable target on demand. What is being
    pinned is the interaction layer shared by every page, not this markup.
    """
    touch_page.goto(ui_urls("about"))
    touch_page.evaluate("""() => {
        window.__activations = [];
        const box = {
            position: 'fixed', top: '200px', left: '20px',
            width: '220px', height: '60px',
        };
        const underneath = document.createElement('button');
        underneath.id = 'tap-underneath';
        Object.assign(underneath.style, box, {zIndex: '9000'});
        underneath.addEventListener('click', () => window.__activations.push('underneath'));

        const on_top = document.createElement('button');
        on_top.id = 'tap-on-top';
        Object.assign(on_top.style, box, {zIndex: '9001'});
        on_top.addEventListener('click', () => {
            window.__activations.push('on-top');
            on_top.remove();
        });

        document.body.append(underneath, on_top);
    }""")

    touch_page.locator("#tap-on-top").tap()
    touch_page.wait_for_timeout(GHOST_CLICK_WINDOW_MS)

    assert touch_page.evaluate("() => window.__activations") == ["on-top"]


@pytest.mark.uses_storage
def test_tap_on_a_label_focuses_its_input(touch_page, ui_urls) -> None:
    """
    Tapping a field label moves focus into that field.

    FastClick special-cased `<label>` (`needsClick`, fastclick.js:253) rather
    than synthesizing its click, so this is the behavior most at risk of
    changing when the library is taken out from under it.
    """
    touch_page.goto(ui_urls("user_management_limited_login"))

    touch_page.locator("label[for='id_username']").tap()

    expect(touch_page.locator("#id_username")).to_be_focused()


@pytest.mark.uses_storage
def test_tap_toggles_a_checkbox_exactly_once(touch_page, ui_urls) -> None:
    """
    One tap flips a checkbox once. A doubled activation would flip it back and
    leave it in its starting state, which this asserts against explicitly.
    """
    touch_page.goto(ui_urls("sign_up_courts"))
    checkbox = touch_page.locator("#id_create_account")
    expect(checkbox).to_be_checked()

    checkbox.tap()
    touch_page.wait_for_timeout(GHOST_CLICK_WINDOW_MS)

    expect(checkbox).not_to_be_checked()


@pytest.mark.uses_storage
def test_tap_follows_a_link(touch_page, ui_urls) -> None:
    """
    Tapping a link navigates to it.

    An in-page link rather than one in the navigation: the navigation's hrefs
    are absolutised against the `HOST` setting, which under the live server is
    a different port, so following one lands on a connection error.
    """
    touch_page.goto(ui_urls("user_management_limited_login"))

    touch_page.get_by_role("link", name="Create a new password.").tap()

    expect(touch_page).to_have_url(ui_urls("password_reset"))


@pytest.mark.uses_storage
def test_tap_submits_a_form_once(touch_page, ui_urls, user) -> None:
    """
    Tapping a submit button submits the form and lands on the next page.

    Login is used because its success is unambiguous from the page that
    follows, and because a second submission of the same POST would fail CSRF
    rather than pass silently.
    """
    touch_page.goto(ui_urls("user_management_limited_login"))
    touch_page.locator("#id_username").fill(user.username)
    touch_page.locator("#id_password").fill(user.password)

    touch_page.get_by_role("button", name="Log in to Perma.cc").tap()

    expect(touch_page.locator("#upper_right_menu form")).to_be_attached()


@pytest.mark.uses_storage
def test_tap_opens_the_account_menu(tablet_touch_page, user, log_in) -> None:
    """
    The account dropdown opens on a tap, and reports itself open.

    Singled out because its trigger carried a `needsclick` class -- FastClick's
    own opt-out marker -- making it the one control on the site known to have
    misbehaved under a synthesized click.
    """
    log_in(tablet_touch_page, user)
    toggle = tablet_touch_page.get_by_role("button", name="Main Dropdown")
    logout = tablet_touch_page.get_by_role("button", name="Log out")
    expect(logout).to_be_hidden()

    toggle.tap()

    expect(logout).to_be_visible()
    expect(toggle).to_have_attribute("aria-expanded", "true")


@pytest.mark.uses_storage
def test_taps_arrive_as_native_clicks(touch_page, ui_urls) -> None:
    """
    Nothing synthesizes clicks on Perma's behalf any more.

    FastClick stamped `forwardedTouchEvent` on every click it manufactured
    (fastclick.js:307), so its absence is a direct, mechanism-level check that
    the library -- or any replacement doing the same thing -- is not in the
    bundle. Kept alongside the behavioral tests above because those would keep
    passing if it were reintroduced, and reintroducing it is the regression
    worth catching: on this exact user agent it attaches unconditionally.
    """
    touch_page.goto(ui_urls("landing"))
    toggle = touch_page.get_by_role("button", name="Toggle navigation")
    toggle.evaluate(
        "el => { window.__forwarded = 'no click seen';"
        " el.addEventListener('click', e => { window.__forwarded = e.forwardedTouchEvent; }); }"
    )

    toggle.tap()
    expect(touch_page.locator("#upper_right_menu")).to_be_visible()

    assert touch_page.evaluate("() => window.__forwarded") is None
