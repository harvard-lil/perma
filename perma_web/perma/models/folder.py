import logging
import time

from django.conf import settings
from django.db import models, transaction
from django.db.models import Exists, F, OuterRef, Q
from model_utils import FieldTracker
from tree_queries.models import TreeNode
from tree_queries.query import TreeQuerySet

from .registrar import Sponsorship

logger = logging.getLogger(__name__)


class FolderQuerySet(TreeQuerySet):
    def user_access_filter(self, user):
        if user.is_staff:
            return Q()  # all

        access_filter = (
            Q(owned_by=user) |
            Q(organization__in=user.get_orgs())
        )

        # folders sponsored by the user's registrar
        if user.registrar_id:
            access_filter |= Q(sponsored_by_id=user.registrar_id)

        return access_filter

    def accessible_to(self, user):
        return self.filter(self.user_access_filter(user))


class Folder(TreeNode):
    name = models.CharField(max_length=255, null=False, blank=False)
    creation_timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='folders_created', on_delete=models.CASCADE)

    # this may be null if this is the shared folder for a org
    owned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='folders', on_delete=models.CASCADE)

    # this will be set if this is inside a shared folder
    organization = models.ForeignKey('Organization', null=True, blank=True, related_name='folders', on_delete=models.CASCADE)

    # true if this is the apex shared folder (not subfolder) for a org, denormalized
    is_shared_folder = models.BooleanField(default=False)

    # true if this is the apex folder for a user; denormalized
    is_root_folder = models.BooleanField(default=False)

    # true if this is the apex sponsored folder for a user; denormalized
    is_sponsored_root_folder = models.BooleanField(default=False)
    sponsored_by = models.ForeignKey('Registrar', null=True, blank=True, related_name='sponsored_folders', on_delete=models.CASCADE)

    # true if this is a sponsored folder, but the sponsorship is deactivated; denormalized
    read_only = models.BooleanField(default=False)

    # since a textual representation of the folder's ancestry is included in the folder's API serialization,
    # keep a cached copy on the model, so we don't have to constantly hit the DB
    cached_path = models.TextField()
    cached_has_children = models.BooleanField(default=False)

    # denormalized, a reference to the apex folder in this folder's tree
    tree_root = models.ForeignKey('self', null=True, on_delete=models.CASCADE)

    objects = FolderQuerySet.as_manager()
    tracker = FieldTracker()

    def is_leaf_node(self):
        return not self.cached_has_children

    def get_descendants(self, include_self=False):
        return self.descendants(
            include_self=include_self
        ).tree_filter(
            tree_root_id=self.tree_root_id
        )

    def get_ancestors(self, include_self=False):
        return self.ancestors(include_self=include_self).tree_filter(
            tree_root_id=self.tree_root_id
        )

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            super().delete(*args, **kwargs)
            if self.parent_id:
                Folder.objects.filter(id=self.parent_id).update(
                    cached_has_children=Exists(
                        Folder.objects.filter(
                            parent_id=self.parent_id
                        )
                    )
                )

    def save(self, *args, **kwargs):

        #
        # Helper methods
        #

        def get_shared_fields_from_parent(parent):
            return {
                "tree_root_id": parent.tree_root_id,
                "read_only": parent.read_only,
                "owned_by_id": parent.owned_by_id,
                "organization_id": parent.organization_id,
                "sponsored_by_id": parent.sponsored_by_id if not parent.is_sponsored_root_folder else self.sponsored_by_id
            }

        def set_owner_for_personal_and_sponsored_folders():
            if self.created_by_id and not self.owned_by_id and not self.organization_id:
                self.owned_by_id = self.created_by_id

        def get_own_subtree_ids():
            if self.cached_has_children:
                return list(
                    self.get_descendants(
                        include_self=True
                    ).tree_filter(
                        tree_root_id=self.tree_root_id
                    ).values_list(
                        'id', flat=True
                    )
                )
            return [self.id]

        def update_tree_root(id, tree_root_id):
            Folder.objects.filter(id=id).update(
                tree_root_id=tree_root_id
            )

        def update_cached_path(ids, tree_root_id):
            Folder.objects.with_tree_fields().filter(
                id__in=ids
            ).update(
                cached_path=Folder.objects.with_tree_fields().tree_filter(
                    tree_root_id=tree_root_id
                ).filter(
                    id=OuterRef('id')
                ).extra(
                    select={"path_string" : "array_to_string((__tree.tree_path), '-')"}
                ).values_list(
                    "path_string", flat=True
                )[:1]
            )

        def update_parents_cached_has_children(parent_id=None, previous_parent_id=None):
            if parent_id:
                Folder.objects.filter(
                    id=parent_id
                ).update(
                    cached_has_children = True
                )
            if previous_parent_id:
                Folder.objects.filter(
                    id=previous_parent_id
                ).update(
                    cached_has_children = Exists(
                        Folder.objects.exclude(
                            id=self.id
                        ).filter(
                            parent_id=previous_parent_id
                        )
                    )
                )

        #
        # Save the folder
        #

        new = not self.pk
        parent_has_changed = not new and self.tracker.has_changed('parent_id')

        start = time.time()
        with transaction.atomic():

            if new:

                if self.parent_id:

                    # fetch the parent
                    parent = Folder.objects.get(id=self.parent_id)

                    # copy shared fields from parent
                    for field, value in get_shared_fields_from_parent(parent).items():
                        setattr(self, field, value)

                    # set ownership, if appropriate
                    set_owner_for_personal_and_sponsored_folders()

                    # simple insert
                    super().save(*args, **kwargs)

                    # update the cached path, now that the folder has an "id"
                    update_cached_path([self.id], parent.tree_root_id)

                    # inform the parent it has a new child
                    update_parents_cached_has_children(parent_id=parent.id)

                else:

                    # set ownership, if appropriate
                    set_owner_for_personal_and_sponsored_folders()

                    # simple insert
                    super().save(*args, **kwargs)

                    # update the tree root and cached path, now that the folder has an "id"
                    update_tree_root(self.id, self.id)
                    update_cached_path([self.id], self.id)

            elif parent_has_changed:

                # make note of the former parent and the new one
                parent = Folder.objects.get(id=self.parent_id)
                previous_parent_id = self.tracker.previous('parent_id')

                # retrieve the ids of this folder and all its descendants, so we can propagate changes.
                # do it before calling "save", while the database is still in a consistent state
                # and tree queries work as expected
                subtree_ids = get_own_subtree_ids()

                # save the change to this folder's parent id
                super().save(*args, **kwargs)

                # copy shared fields from parent to this folder and all its descendants
                subtree = Folder.objects.filter(id__in=subtree_ids)
                subtree.update(**get_shared_fields_from_parent(parent))

                from .link import Link
                # update the de-normalized reference to owning org on any links in this folder's subtree
                links = Link.objects.filter(folders__in=subtree_ids)
                links.update(organization_id=parent.organization_id)

                # if any bonus links got transferred to an org or to a sponsored folder, give users their bonus credit back
                bonus_links = links.filter(bonus_link=True)
                if (parent.organization_id or parent.sponsored_by_id) and (any_link := bonus_links.first()):
                    user = any_link.created_by
                    count = bonus_links.update(bonus_link=False)
                    user.bonus_links = F('bonus_links') + count
                    user.save(update_fields=['bonus_links'])

                # update the cached paths of this folder and all its descendants
                update_cached_path(subtree_ids, parent.tree_root_id)

                # now that the move is over, inform the parent it has a new child, and inform the previous parent it has one fewer
                update_parents_cached_has_children(parent_id=parent.id, previous_parent_id=previous_parent_id)

            else:
                super().save(*args, **kwargs)

        logger.debug(f"Saved {self.id} in {time.time() - start}s")

    class Meta:
        ordering = ['name', 'id']

    def is_empty(self):
        return not self.children.exists() and not self.links.exists()

    def __str__(self):
        return self.name

    @classmethod
    def format_tree_path(cls, tree_path):
        return '-'.join([str(i) for i in tree_path])

    def get_path(self):
        try:
            return Folder.format_tree_path(self.tree_path)
        except AttributeError:
            return Folder.format_tree_path(Folder.objects.with_tree_fields().tree_filter(
                tree_root_id=self.tree_root_id
            ).get(id=self.id).tree_path)

    def accessible_to(self, user):
        # staff can access any folder
        if user.is_staff:
            return True

        # private folders (including sponsored folders when viewed by sponsored users)
        if self.owned_by_id == user.pk:
            return True

        # sponsored
        elif self.sponsored_by_id:
            return self.sponsored_by_id == user.registrar_id

        # shared folders
        elif self.organization_id:
            if user.is_registrar_user():
                # if user is registrar, must be registrar for this org
                return user.registrar_id == self.organization.registrar_id
            else:
                # else, user must belong to this org
                return user.organizations.filter(pk=self.organization_id).exists()

    @property
    def sponsorship(self):
        if self.sponsored_by:
            return Sponsorship.objects.get(user=self.owned_by, registrar_id=self.sponsored_by)
