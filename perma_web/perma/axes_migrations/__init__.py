"""Override Axes 0009; discover all other migrations from the pinned package.

Python searches this package first, then the upstream migration directory.
Django therefore retains the upstream names, dependencies, and future migrations
without vendoring them. Test migration discovery when upgrading django-axes.
"""

from axes import migrations as upstream

__path__.extend(upstream.__path__)
