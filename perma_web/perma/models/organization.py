from django.db import models, transaction
from django.db.models import F, Q, QuerySet
from django.utils import timezone
from model_utils import FieldTracker
from simple_history.models import HistoricalRecords

from perma.utils import tz_datetime

from .folder import Folder
from .registrar import Registrar
from .utils import DeletableManager, DeletableModel, link_count_in_time_period


class OrganizationQuerySet(QuerySet):
    def accessible_to(self, user):
        qset = self.user_access_filter(user)
        if qset is None:
            return self.none()
        else:
            return self.filter(qset)

    def user_access_filter(self, user):
        if user.is_organization_user:
            return Q(id__in=user.organizations.all())
        elif user.is_registrar_user():
            return Q(registrar_id=user.registrar_id)
        elif user.is_staff:
            return Q()  # all
        else:
            return None


OrganizationManager = DeletableManager.from_queryset(OrganizationQuerySet)


class Organization(DeletableModel):
    """
    This is generally a journal.
    """
    name = models.CharField(max_length=400)
    registrar = models.ForeignKey(Registrar, null=True, related_name="organizations", on_delete=models.CASCADE)
    shared_folder = models.OneToOneField('Folder', blank=True, null=True, related_name="top_level_for_org", on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    default_to_private = models.BooleanField(default=False)
    link_count = models.IntegerField(default=0) # A cache of the number of links under this org's purview

    objects = OrganizationManager()
    tracker = FieldTracker()
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=['user_deleted']),
        ]

    def save(self, *args, **kwargs):
        with transaction.atomic():

            if not self.pk:
                self.default_to_private = self.registrar.orgs_private_by_default

            with self.tracker:
                # Save here, so we have a PK if we need it below, to create the shared folder
                super().save(*args, **kwargs)

                if self.tracker.has_changed('registrar_id'):
                    self._transfer_registrar_link_counts(self.tracker.previous('registrar_id'), self.registrar_id)

                if not self.shared_folder_id:
                    # Create a top-level folder for this org
                    shared_folder = Folder.objects.create(
                        name=self.name,
                        organization=self,
                        is_shared_folder=True
                    )
                    self.shared_folder = shared_folder
                    # Save with super again, instead of plain save,
                    # so we don't run through our custom logic twice
                    super().save()

                elif self.tracker.has_changed('name'):
                    # Rename shared folder if org name changes.
                    self.shared_folder.name = self.name
                    self.shared_folder.save()

    def _transfer_registrar_link_counts(self, old_registrar_id, new_registrar_id):
        """ Move this org's link_count between registrars when registrar changes. """
        if old_registrar_id == new_registrar_id or not self.link_count:
            return

        Registrar.objects.filter(pk=old_registrar_id).update(link_count=F('link_count') - self.link_count)
        Registrar.objects.filter(pk=new_registrar_id).update(link_count=F('link_count') + self.link_count)

    def __str__(self):
        return self.name

    def link_count_in_time_period(self, start_time=None, end_time=None):
        from .link import Link
        links = Link.objects.filter(organization=self)
        return link_count_in_time_period(links, start_time, end_time)

    def link_count_this_year(self):
        return self.link_count_in_time_period(tz_datetime(timezone.now().year, 1, 1))

    def accessible_to(self, user):
        if user.is_staff:
            return True
        if user.is_registrar_user():
            return self.registrar_id == user.registrar_id
        return self.users.filter(pk=user.pk).exists()
