from perma.models import Link
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
        # It's a /schema request
        if bundle.obj.pk is None:
            return True

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
        return object_list.discoverable()

    def read_detail(self, object_list, bundle):
        # It's a /schema request
        if bundle.obj.pk == u'':
            return True

        return bundle.obj.is_discoverable()


class AuthenticatedLinkAuthorization(ReadOnlyAuthorization):
    def read_list(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized()

        return object_list.accessible_to(bundle.request.user)

    def read_detail(self, object_list, bundle):
        # It's a /schema request
        if bundle.obj.pk == u'':
            return True

        if not bundle.request.user.is_authenticated():
            raise Unauthorized()

        # If we want to patch title or another field in the future,
        # we might want to uncomment this (?).
        #if bundle.request.method == 'PATCH':
        #    return True

        if bundle.request.user.is_staff:
            return True

        return Link.objects.filter(pk=bundle.obj.pk).accessible_to(bundle.request.user).exists()

class CurrentUserAuthorization(ReadOnlyAuthorization):

    def read_list(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized()
        return object_list.empty()

    def read_detail(self, object_list, bundle):
        # It's a /schema request
        if bundle.obj.pk is None:
            return True
        return bundle.obj == bundle.request.user

class CurrentUserNestedAuthorization(ReadOnlyAuthorization):

    def read_list(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized()
        return object_list.filter(created_by=bundle.request.user)

    def read_detail(self, object_list, bundle):
        # It's a /schema request
        if bundle.obj.pk is None:
            return True
        if not bundle.request.user.is_authenticated():
            raise Unauthorized()
        return bundle.obj.created_by == bundle.request.user


class CurrentUserOrganizationAuthorization(CurrentUserNestedAuthorization):

    def read_list(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized()
        return object_list.accessible_to(bundle.request.user)

    def read_detail(self, object_list, bundle):
        # It's a /schema request
        if bundle.obj.pk is None:
            return True
        if not bundle.request.user.is_authenticated():
            raise Unauthorized()
        return bundle.request.user.can_edit_organization(bundle.obj)


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

    def update_detail(self, object_list, bundle):
        # public/private
        # If you aren't staff, you're only allowed to toggle is_private if private_reason is 'user'.
        if bundle.obj.tracker.has_changed("is_private") and not bundle.request.user.is_staff:
            if bundle.obj.is_private:
                if bundle.obj.private_reason != 'user':
                    raise Unauthorized()
            else:
                if bundle.obj.tracker.previous('private_reason') != 'user':
                    raise Unauthorized()

        # For editing
        if not self.can_access(bundle.request.user, bundle.obj):
            raise Unauthorized()

        return True

    def delete_detail(self, object_list, bundle):

        if not bundle.request.user.can_delete(bundle.obj):
            raise Unauthorized()

        return True
