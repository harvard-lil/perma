from perma.models import Link, Folder
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.exceptions import Unauthorized


class DefaultAuthorization(ReadOnlyAuthorization):

    def create_detail(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized("You must be a registered user.")

        return True

    def update_detail(self, object_list, bundle):
        if bundle.obj.created_by != bundle.request.user:
            raise Unauthorized("Sorry, you don't have permission")

        return True

    delete_detail = update_detail


class FolderAuthorization(DefaultAuthorization):

    def can_access(self, user, obj):
        try:
            # returns true if exists
            return bool(user.id == obj.created_by_id or
                        Folder.objects.get(Folder.objects.user_access_filter(user),
                                           pk=obj.pk))
        except Folder.DoesNotExist:
            return False

    # NOTE - this is called by obj_update and obj_delete before it uses their auth
    # ex: https://github.com/toastdriven/django-tastypie/blob/master/tastypie/resources.py#L2203
    def read_detail(self, object_list, bundle):
        if not self.can_access(bundle.request.user, bundle.obj):
            raise Unauthorized("Sorry, you don't have access to that folder.")

        return True

    def delete_detail(self, object_list, bundle):
        if bundle.obj.is_shared_folder:
            raise Unauthorized("Shared folders cannot be deleted.")
        elif bundle.obj.is_root_folder:
            raise Unauthorized("Root folders cannot be deleted.")
        elif not bundle.obj.is_empty():
            raise Unauthorized("Folders can only be deleted if they are empty.")
        elif not self.can_access(bundle.request.user, bundle.obj):
            raise Unauthorized("Sorry, you don't have access to that folder.")

        return True

    def update_detail(self, object_list, bundle):
        # For renaming
        if bundle.obj.tracker.has_changed("name"):
            if bundle.obj.is_shared_folder:
                raise Unauthorized("Shared folders cannot be renamed.")
            elif bundle.obj.is_root_folder:
                raise Unauthorized("Root folders cannot be renamed.")

        return True


class LinkAuthorization(DefaultAuthorization):

    def can_access(self, user, obj):
        try:
            # returns true if exists
            return bool(user.id == obj.created_by_id or
                        Link.objects.get(Link.objects.user_access_filter(user),
                                         pk=obj.pk))
        except Link.DoesNotExist:
            return False

    def can_vest_to_org(self, user, vesting_org):
        if user.has_group('vesting_user'):
            return user.vesting_org == vesting_org
        elif user.has_group('registrar_user'):
            return user.registrar == vesting_org.registrar
        elif user.has_group('registry_user'):
            return True
        else:
            return False

    def update_detail(self, object_list, bundle):
        # For vesting
        if bundle.obj.tracker.has_changed("vested"):
            if not bundle.request.user.has_group(['registrar_user', 'registry_user', 'vesting_user']):
                raise Unauthorized("Sorry, you don't vesting have permission")
            if not self.can_vest_to_org(bundle.request.user, bundle.obj.vesting_org):
                raise Unauthorized("Sorry, you can't vest to that organization")

            return True

        # For editing
        if not self.can_access(bundle.request.user, bundle.obj):
            raise Unauthorized("Sorry, you don't have permission")

        return True

    def delete_detail(self, object_list, bundle):
        if bundle.obj.vested or bundle.obj.created_by != bundle.request.user:
            raise Unauthorized("Sorry, you don't have permission")

        return True


class CurrentUserAuthorization(ReadOnlyAuthorization):

    def all_detail(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized("You must be authenticated.")

        return True

    def all_list(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized("You must be authenticated.")

        return object_list.filter(created_by=bundle.request.user)

    read_detail = create_detail = update_detail = delete_detail = all_detail
    read_list = all_list  # create_list = update_list = delete_list = disallowed system wide
