Perma - developer notes

=====

## Notes on dancing

This document does not cover installing Perma.cc. You should use the install doc for that.

There are a bunch of moving pieces in Perma.cc. This document provides some notes on common dances you might have to perform.

### Git and GitHub

We use git to track code changes and use [GitHub](https://github.com/harvard-lil/perma) to host the code publicly.

The Master branch always contains production code (probably the thing currently running at [Perma.cc](http://perma.cc)) while the develop branch contains the group's working version. We follow this [Vincent Driessen's approach](http://nvie.com/posts/a-successful-git-branching-model/)

Leverage [feature branches](http://nvie.com/posts/a-successful-git-branching-model/) in your local development flow. Merge your code back into the develop branch and push to GitHub often. Small, quick commits avoid nightmare merge problems.

###  Schema and data migrations using South

If you make a change to the Django model (models get mapped directly to relational database tables), you'll need to create a [south](http://south.aeracode.org/) migration. South migrations come in two flavors: schema migrations and data migrations.

Schema migrations are used when changing the model structure (adding, removing, editing fields) and data migrations are used when you need to ferry data between your schema changes (you renamed a field and need to move data from the old field name to the new field name).

The most straight forward data migration might be the addition of a new model or the addition of a field to a model. When you perform a straight forward change to the model, your south command might look like this

    $ ./manage.py schemamigration perma --auto

This will create a migration file for you on disk, something like

    $ cat perma_web/perma/migrations/0003_auto__add_vestingorg__add_field_linkuser_vesting_org.py

Even though you've changed your models file and created a migration (just a python file on disk), your database remains unchanged. You'll need to apply the migration to update your database,

    $ /manage.py migrate perma



If you've just installed Perma.cc, you'll want to make sure to perform the first migration as a "fake" migation,

    $ ./manage.py migrate perma 0001 --fake

### Debugging email-related issues

### Working with Celery

### Working with RabbitMQ