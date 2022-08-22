Installing Perma
================

Perma is a Python application built on the [Django](https://www.djangoproject.com/)
web framework.

Perma has a lot of moving pieces. We recommend using [Docker](https://www.docker.com/what-docker) for local development. If you are new to Docker, it may take some
time before you are comfortable with its vocabulary and commands, but it allows you
to jump right into coding instead of spending a lot of time getting all the services
running on your machine.

If you prefer to install Perma locally, see our [legacy installation instructions](#manual-installation-legacy).

For advice about production deployments, [send us a note](mailto:info@perma.cc)!

Be sure to check out [the developer documentation](./developer.md)
for a list of command commands and other tips and tricks for working with Perma.


Dependencies
------------

* [Git](http://git-scm.com/downloads)
* [Docker](https://docs.docker.com/install/)
* [mkcert](https://github.com/FiloSottile/mkcert) (for macOS installs, run `brew bundle`)


Hosts
-----

Perma serves content at several hosts. To ensure that URLs resolve correctly,
add the following domains to your computer's hosts file:

    127.0.0.1 perma.test api.perma.test replay.perma.test perma-archives.test perma.minio.test

For additional information on modifying your hosts file,
[try this help doc](http://www.rackspace.com/knowledge_center/article/how-do-i-modify-my-hosts-file).


Shortcuts
---------

Docker commands can be lengthy. To cut down on keystrokes, we recommend
adding the following to your `.bash_profile`.

```
alias d="docker-compose exec web"
```


Installation
------------

Then check out the code:

    $ git clone https://github.com/harvard-lil/perma.git
    $ cd perma

Using `pull` first after fetching new code will avoid rebuilding images locally:

    $ docker-compose pull

Start up the Docker containers in the background:

    $ docker-compose up -d

The first time this runs, it may take several minutes. With up-to-date docker images,
it should only take a few seconds.

Finally, initialize the databases and generate the SSL certificates and keys required to access your local Perma over SSL:

    $ bash init.sh

You should now have a working installation of Perma! See [common commands](./developer.md#common-tasks-and-commands) to explore what you can do, like [running
the application](./developer.md#run-perma) and [running the tests](/developer.md#run-all-the-tests).

When you are finished, spin down Docker containers by running:

    $ docker-compose down

Making Mac OS trust self-signed certificate if it doesn't
---------------------------------------------------------
It _"sometimes"_ happen that `mkcert`'s setup is incomplete, and Mac OS doesn't trust the certificates it generated as a result.

**Here's how to fix it:**
- Go to `Applications > Utilities > Keychain Access`
- Click on the `login` filter
- Drag and drop the `rootCA.pem` file `mkcert` generated onto the UI
- Look for the certificate in the list: it should start with `mkcert` followed by the name of your machine
- Right-click on it and pick _"Get Info"_
- Unfold the _"Trust"_ dropdown, and pick _"Always trust"_ for the relevant categories. 

If you're still encountering issues, you may want to hit these urls in your browser and manually bypass the security alerts: 
```
https://perma.test:8000
https://replay.perma.test:8000
https://perma.minio.test:9000
https://perma-archives.test:8092
```