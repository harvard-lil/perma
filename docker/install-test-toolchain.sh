#!/usr/bin/env bash
#
# Playwright's browsers and the X11 libraries they need, plus an NSS database
# for the user running this so the test suite can trust its mkcert certs.
#
# Shared by the `dev` and `test` targets in ../Dockerfile so the two stay in
# lockstep: `dev` is what a developer runs against a bind-mounted checkout,
# `test` is the same toolchain layered onto the real prod artifact in CI. If
# these drifted apart, CI and local development would stop agreeing about what
# the test suite runs on.
#
# Assumes the calling stage has already installed the dev dependency group
# (`uv sync --frozen`), which is where the `playwright` CLI comes from, so the
# browsers installed here are the ones the locked Python package expects.
#
# Installs browsers into $PLAYWRIGHT_BROWSERS_PATH (set by both targets) and
# makes them world-readable, so a stage that drops to a non-root user after
# running this can still launch them.
set -euxo pipefail

: "${PLAYWRIGHT_BROWSERS_PATH:?must be set by the calling Dockerfile stage}"

# Shared libraries Playwright's chromium/firefox builds link against.
apt-get update
apt-get install -y --no-install-recommends \
    libdbus-glib-1-2 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatspi2.0-0 \
    libwayland-client0 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-xcb1 \
    libxcursor1 \
    libgtk-3-0 \
    libpangocairo-1.0-0 \
    libcairo-gobject2 \
    libgdk-pixbuf-2.0-0
rm -rf /var/lib/apt/lists/*

playwright install chromium firefox

# Readable by whatever user the stage ends up running as.
chmod -R a+rX "$PLAYWRIGHT_BROWSERS_PATH"

# karma.config.js defaults CHROMIUM_BIN to this path for the JS unit tests.
chromium="$(find "$PLAYWRIGHT_BROWSERS_PATH" -name chrome -type f -executable | head -1)"
test -n "$chromium"
ln -sf "$chromium" /usr/local/bin/playwright-chromium

# conftest.py runs `certutil -d sql:$HOME/.pki/nssdb -A ...`; the database has
# to exist first. This creates it for the user running the script (root, for
# the `dev` target); `test` creates its own for the `perma` user afterwards.
mkdir -p "$HOME/.pki/nssdb"
certutil -d "sql:$HOME/.pki/nssdb" -N --empty-password
