Perma API Developer Docs
========================

Perma's API is built with Django Rest Framework. If you're working on the API and haven't used DRF, you might want to
read through the first few sections of the [excellent tutorial](http://www.django-rest-framework.org/tutorial/1-serialization/).

To make debugging easier, we avoid some of DRF's higher-level features, such as ViewSets, mixins, and routers.
We also avoid building up too many layers of abstraction in our own code. This makes it easy to trace a single request
from start to end within a single file, and to see all of the routes and request methods exposed by the API.

The two features of DRF that we do make heavy use of are class-based views (which basically work like Django's class-based
views) and serializers (which basically work like Django's ModelForms).

Using LOG_API_CALLS to Debug Tests
----------------------------------

When an API test fails, a great first step (and often the only required step) is to see what API endpoints are being
called by the test, what user is calling them, and what they are returning.  You can enable logging of that information
by setting the LOG_API_CALLS environment variable. For example:

    LOG_API_CALLS=1 fab test:api2.tests.test_folder_authorization.FolderAuthorizationTestCase.test_reject_delete_of_shared_folder

(This variable is checked by our custom APIClient in api2/tests/utils.py, which does the logging.)

Once you find the endpoint that is returning something unexpected, if it's still not clear what's wrong, you'll at least
have a good idea where to set a breakpoint to start to figure out what's happening.