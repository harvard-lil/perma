from django.db import models

from perma.models import Registrar

# Proxy models for generating changelist pages in the reporting admin. While these superficially match
# the reporting views, they are Django models based on the real models in `perma` and so
# have all the same fields as their `perma` equivalents, rather than the columns synthesized
# in the reporting admin views. (What does that mean?)

class FederalCourtManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            tags__slug__in=["court"]
        ).filter(
            tags__slug__in=["federal"]
        )

class FederalCourt(Registrar):

    class Meta:
        proxy = True
        verbose_name = "Federal Court"

    objects = FederalCourtManager()
