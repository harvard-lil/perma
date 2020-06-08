services/warcprox
-----------------
In order for headless Chrome to browse sites over HTTPS through
warcprox, we provide the CA cert in this directory. Install `certutil`
with

    sudo apt-get install libnss3-tools

List certs with

    certutil -d sql:$HOME/.pki/nssdb -L

and add the cert to your development system, if necessary, with

    certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n 'warcprox CA cert' -i services/warcprox/perma-warcprox-ca.pem
