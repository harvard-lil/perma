# This is the base module that will be imported by Django.
#
# There are two ways to choose which deployment settings apply. Whichever one
# supplies settings here, everything below this point (the DJANGO__ environment
# overrides and post_process_settings) still runs -- that's the point of Django
# importing this package rather than one of its submodules directly.
#
# 1. PERMA_SETTINGS_MODULE environment variable, read at runtime. Set it to the
#    name of a module in perma/settings/deployments, e.g. "settings_ecs" or
#    "settings_prod". This lets one built image boot as any deployment target
#    without baking a settings.py into it at build time. Takes precedence over
#    settings.py below when set. A name that does not exist is an error, not a
#    fall-through to development settings.
# 2. perma/settings/settings.py, resolved at import time with no env var
#    needed. Copy settings.example.py to settings.py and edit it; it in turn
#    imports one of the deployment targets. This is for a developer's local
#    checkout, and for the Salt hosts, where Salt renders it. If settings.py
#    doesn't exist, we assume this is a vanilla development environment and
#    import .deployments.settings_dev instead.
import importlib
import os

_perma_settings_module = os.environ.get("PERMA_SETTINGS_MODULE")

if _perma_settings_module:
    if not _perma_settings_module.isidentifier():
        raise ImportError(
            f"PERMA_SETTINGS_MODULE={_perma_settings_module!r} is not a valid module name. "
            "Set it to the name of a module in perma/settings/deployments, e.g. "
            "'settings_ecs' or 'settings_prod'."
        )
    _deployments_package = f"{__name__}.deployments"
    try:
        _settings_module = importlib.import_module(f".{_perma_settings_module}", package=_deployments_package)
    except ModuleNotFoundError as e:
        # Only intercept "the module itself doesn't exist" -- an ImportError raised from
        # *inside* a module that does exist (e.g. a required env var missing) should
        # propagate as-is rather than being misreported as a bad module name.
        if e.name == f"{_deployments_package}.{_perma_settings_module}":
            raise ImportError(
                f"PERMA_SETTINGS_MODULE={_perma_settings_module!r} does not name a module "
                f"in {_deployments_package} (looked for {_deployments_package}.{_perma_settings_module}). "
                "Refusing to fall back to settings_dev -- check for a typo."
            ) from e
        raise
    # Django only reads uppercase settings, so mirror that here instead of doing
    # `import *`, which would also copy the target module's lowercase helper
    # variables (and its own imports, e.g. `os`) into these globals.
    globals().update({k: v for k, v in vars(_settings_module).items() if k.isupper()})
    del _settings_module, _deployments_package
else:
    # Try to import the custom settings.py file, which will in turn import one of the deployment targets.
    # If it doesn't exist we assume this is a vanilla development environment and import .deployments.settings_dev.
    try:
        from .settings import *  # noqa
    except ImportError as e:
        if e.msg == "No module named 'perma.settings.settings'":
            from .deployments.settings_dev import *  # noqa
        else:
            raise

del _perma_settings_module

# After we've imported one of the deployment targets, we'll override the settings based on any
# DJANGO__SETTING_NAME environment variables. This is handy for deploying to Travis, etc.
from .utils.environmental_settings import import_environmental_settings  # noqa: E402
import_environmental_settings(globals())

# Finally we'll apply some post-processing logic to the settings we've ended up with.
from .utils.post_processing import post_process_settings  # noqa: E402
post_process_settings(globals())
