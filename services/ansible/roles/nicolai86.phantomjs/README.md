# ansible-phantomjs

binary phantomjs installer.

phantomjs is installed to /usr/local/bin, thus requiring sudo once to copy the downloaded binary over.

Only executes if phantomjs is not present, or a different version is installed.

## Usage

    - hosts: servers
      vars:
        phantomjs_version: "1.9.2"
        phantomjs_url: "https://phantomjs.googlecode.com/files/phantomjs-1.9.2-linux-x86_64.tar.bz2"
      roles:
        - nicolai86.ansible-phantomjs