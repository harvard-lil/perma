Perma API Developer Docs
========================

Perma's API is built with Django Rest Framework. If you're working on the API and haven't used DRF, you might want to
read through the first few sections of the [excellent tutorial](http://www.django-rest-framework.org/tutorial/1-serialization/).

To make debugging easier, we avoid some of DRF's higher-level features, such as ViewSets, mixins, and routers.
We also avoid building up too many layers of abstraction in our own code. This makes it easy to trace a single request
from start to end within a single file, and to see all of the routes and request methods exposed by the API.

The two features of DRF that we do make heavy use of are class-based views (which basically work like Django's class-based
views) and serializers (which basically work like Django's ModelForms).