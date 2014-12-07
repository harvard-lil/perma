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
            raise Unauthorized("Sorry, you don't have access")

    def delete_detail(self, object_list, bundle):
        return self.update_detail(object_list, bundle)


class LinkAuthorization(DefaultAuthorization):
    def update_detail(self, object_list, bundle):
        try:
            return bool(bundle.obj.created_by == bundle.request.user or
                        Link.objects.get(Link.objects.user_access_filter(bundle.request.user),
                                         pk=bundle.obj.pk))
        except Link.DoesNotExist:
            raise Unauthorized("Sorry, you don't have access")

    def delete_detail(self, object_list, bundle):
        if bundle.obj.created_by == bundle.request.user:
            return True
        else:
            raise Unauthorized("Sorry, you don't have access")


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
