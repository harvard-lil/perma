### environment settings overrides ###
# this is included by __init__.py

import os

# this lets us set values from the environment, like
# export DJANGO__SECRET_KEY=foo
# export DJANGO__INT__SITE_ID=1
# export DJANGO__DATABASES__default__NAME=perma
# export DJANGO__MIRRORS__0='http://127.0.0.1:8001'
def import_environmental_settings(settings):
    for key, value in os.environ.items():
        if key.startswith("DJANGO__"):
            try:
                path = key.split('__')[1:]

                if path[0] == 'INT':
                    # convert to int if second piece of path is 'INT'
                    value = int(value)
                    path = path[1:]
                elif value=='True':
                    # convert to boolean
                    value=True
                elif value=='False':
                    value=False

                # starting with global settings, walk down the tree to find the intended value
                target = settings
                while len(path) > 1:
                    try:
                        # if it's an int, treat it as an array index
                        path[0] = int(path[0])
                        while len(target)<=path[0]:
                            target += [{}]
                    except ValueError:
                        # otherwise it's a dict key
                        if not path[0] in target:
                            target[path[0]] = {}
                    target = target[path.pop(0)]

                # set value
                try:
                    path[0] = int(path[0])
                    while len(target) <= path[0]:
                        target += [{}]
                except ValueError:
                    pass
                target[path[0]] = value
            except Exception as e:
                print("WARNING: Can't import environmental setting %s: %s" % (key, e))
