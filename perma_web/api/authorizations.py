from perma.models import Link, Folder
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.exceptions import Unauthorized, BadRequest


class FolderAuthorization(ReadOnlyAuthorization):

    def can_access(self, user, obj):
        # staff can access any folder
        if user.is_staff:
            return True

        # private folders
        if obj.owned_by_id == user.pk:
            return True

        # shared folders
        elif obj.organization_id:
            if user.is_registrar_member():
                # if user is registrar, must be registrar for this org
                return user.registrar_id == obj.organization.registrar_id
            else:
                # else, user must belong to this org
                return user.organizations.filter(pk=obj.organization_id).exists()

        return False

    def read_list(self, object_list, bundle):
        # /folders endpoint shouldn't list anything, but /folders/<id>/folders should
        if not bundle.parent_object:
            raise Unauthorized()
        return object_list

    # NOTE - this is called by obj_update and obj_delete before it uses their auth methods
    # ex: https://github.com/toastdriven/django-tastypie/blob/master/tastypie/resources.py#L2203
    def read_detail(self, object_list, bundle):
        if not self.can_access(bundle.request.user, bundle.obj):
            raise Unauthorized()

        return True

    def delete_detail(self, object_list, bundle):

        if not self.can_access(bundle.request.user, bundle.obj):
            raise Unauthorized()

        if bundle.obj.is_shared_folder:
            raise BadRequest("Shared folders cannot be deleted.")
        elif bundle.obj.is_root_folder:
            raise BadRequest("Root folders cannot be deleted.")
        elif not bundle.obj.is_empty():
            raise BadRequest("Folders can only be deleted if they are empty.")

        return True

    def update_detail(self, object_list, bundle):
        if not self.can_access(bundle.request.user, bundle.obj):
            raise Unauthorized()

        return True

    def create_detail(self, object_list, bundle):
        return bundle.obj.parent and self.can_access(bundle.request.user, bundle.obj.parent)


class PublicLinkAuthorization(ReadOnlyAuthorization):

    def read_list(self, object_list, bundle):
        return object_list.filter(vested=True)

    def read_detail(self, object_list, bundle):
        return bundle.obj.vested


class AuthenticatedLinkAuthorization(ReadOnlyAuthorization):
    def read_list(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized()

        return object_list.accessible_to(bundle.request.user)

    def read_detail(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized()

        # It is possible to vest a link you can't (yet) read.
        # If patching an unvested link, we skip the read permissions check and rely on patch authorization.
        if bundle.request.method == 'PATCH' and not bundle.obj.vested and bundle.request.user.can_vest():
            return True

        if bundle.request.user.is_staff:
            return True

        return Link.objects.filter(pk=bundle.obj.pk).accessible_to(bundle.request.user).exists()

class CurrentUserAuthorization(ReadOnlyAuthorization):

    def all_detail(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized()

        return True

    def all_list(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized()

        return object_list.filter(created_by=bundle.request.user)

    read_detail = create_detail = update_detail = delete_detail = all_detail
    read_list = all_list  # create_list = update_list = delete_list = disallowed system wide


class CurrentUserOrganizationAuthorization(CurrentUserAuthorization):

    def all_list(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized()

        return object_list.accessible_to(bundle.request.user)

    read_list = all_list  # create_list = update_list = delete_list = disallowed system wide

class LinkAuthorization(AuthenticatedLinkAuthorization):

    def can_access(self, user, obj):
        # staff can access any link
        if user.is_staff:
            return True

        return Link.objects.filter(pk=obj.pk).accessible_to(user).exists()

    def create_detail(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized("You must be a registered user.")

        return True

    def can_vest_to_org(self, user, org):
        if user.is_registrar_member():
            # user must be registrar for this org ...
            return user.registrar == org.registrar
        elif user.is_staff:
            # ... or staff ...
            return True
        else:
            # ... or belong to this org
            return user.organizations.filter(pk=org.pk).exists()

    def update_detail(self, object_list, bundle):
        # For vesting
        if bundle.obj.tracker.has_changed("vested"):
            if not bundle.request.user.can_vest() or not self.can_vest_to_org(bundle.request.user, bundle.obj.organization):
                raise Unauthorized()

            return True

        # For editing
        if not self.can_access(bundle.request.user, bundle.obj):
            raise Unauthorized()

        return True

    def delete_detail(self, object_list, bundle):
        if bundle.obj.vested or not self.can_access(bundle.request.user, bundle.obj):
            raise Unauthorized()

        return True