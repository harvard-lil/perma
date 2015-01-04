from perma.models import Link
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.exceptions import Unauthorized


class DefaultAuthorization(ReadOnlyAuthorization):

    def create_detail(self, object_list, bundle):
        if bundle.request.user.is_authenticated():
            return True
        else:
            raise Unauthorized("You must be a registered user.")

    def update_detail(self, object_list, bundle):
        if bundle.obj.created_by == bundle.request.user:
            return True
        else:
            raise Unauthorized("Sorry, you don't have permission")

    def delete_detail(self, object_list, bundle):
        return self.update_detail(object_list, bundle)


class FolderAuthorization(DefaultAuthorization):
    def delete_detail(self, object_list, bundle):
        if bundle.obj.is_shared_folder:
            raise Unauthorized("Shared folders cannot be deleted.")
        elif bundle.obj.is_root_folder:
            raise Unauthorized("Root folders cannot be deleted.")
        elif not bundle.obj.is_empty():
            raise Unauthorized("Folders can only be deleted if they are empty.")

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
            if bundle.request.user.has_group(['registrar_user', 'registry_user', 'vesting_user']):
                if self.can_vest_to_org(bundle.request.user, bundle.obj.vesting_org):
                    return True
                else:
                    raise Unauthorized("Sorry, you can't vest to that organization")
            else:
                raise Unauthorized("Sorry, you don't vesting have permission")

        # For editing
        try:
            return bool(bundle.obj.created_by == bundle.request.user or
                        Link.objects.get(Link.objects.user_access_filter(bundle.request.user),
                                         pk=bundle.obj.pk))
        except Link.DoesNotExist:
            raise Unauthorized("Sorry, you don't have permission")

    def delete_detail(self, object_list, bundle):
        if not bundle.obj.vested and bundle.obj.created_by == bundle.request.user:
            return True
        else:
            raise Unauthorized("Sorry, you don't have permission")


class CurrentUserAuthorization(ReadOnlyAuthorization):

    def all_detail(self, object_list, bundle):
        if bundle.request.user.is_authenticated():
            return True
        else:
            raise Unauthorized("You must be authenticated.")

    def all_list(self, object_list, bundle):
        if bundle.request.user.is_authenticated():
            return object_list.filter(created_by=bundle.request.user)
        else:
            raise Unauthorized("You must be authenticated.")

    read_detail = create_detail = update_detail = delete_detail = all_detail
    read_list = all_list  # create_list = update_list = delete_list = disallowed system wide
