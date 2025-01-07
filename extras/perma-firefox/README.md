# Perma.cc extension for Firefox

This directory contains code for the [Perma.cc extension for Firefox](https://addons.mozilla.org/en-US/firefox/addon/perma-cc/). The extension is very simple:

1. When viewing a website, click the Perma.cc button in your browser
2. You will be taken to [perma.cc/manage/create](https://perma.cc/manage/create) in a new tab (logging in first, if necessary)
3. The Create Perma Link field will be pre-populated with the URL you were viewing

## Update process

We use Mozilla's packaging tool [web-ext](https://extensionworkshop.com/documentation/develop/getting-started-with-web-ext/) to publish new versions of the extension to [addons.mozilla.org](https://addons.mozilla.org/en-US/firefox/).

In order to sign and publish the extension, you must install web-ext and add the relevant Mozilla API key and secret to your environment as `AMO_JWT_ISSUER` and `AMO_JWT_SECRET`.

Here's how to publish an update:

1. Make your changes to the extension code on a branch or fork of this repository
2. Bump the version number in [manifest.json](https://github.com/harvard-lil/perma/blob/develop/extras/perma-firefox/src/manifest.json) as part of your PR
3. Merge your PR once it's approved
4. From the current directory (`extras/perma-firefox`), run the following command to sign and publish the new release:
   ```sh
   web-ext sign --channel=listed --source-dir=src --api-key=$AMO_JWT_ISSUER --api-secret=$AMO_JWT_SECRET
   ```
5. Once your new release is approved and published (it may take a few minutes), it will be available [here](https://addons.mozilla.org/en-US/firefox/addon/perma-cc/)
