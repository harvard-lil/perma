from tastypie.authorization import Authorization, ReadOnlyAuthorization
from tastypie.exceptions import Unauthorized

class DefaultAuthorization(ReadOnlyAuthorization):

    def create_detail(self, object_list, bundle):
        if bundle.request.user.is_authenticated():
            return True
        else:
           raise Unauthorized("You must be a registered user.")

    def update_detail(self, object_list, bundle):
        if getattr(bundle.obj, self.resource_meta.user_field) == bundle.request.user:
            return True
        else:
            raise Unauthorized("Sorry, you're not the owner of that.")

    def delete_detail(self, object_list, bundle):
        return self.update_detail(object_list, bundle)


class CurrentUserAuthorization(ReadOnlyAuthorization):
    def all_detail(self, object_list, bundle):
        if bundle.request.user.is_authenticated():
            return True
        else:
            raise Unauthorized("You must be authenticated.")

    def all_list(self, object_list, bundle):
        if bundle.request.user.is_authenticated():
            filters = {self.resource_meta.user_field: bundle.request.user}
            return object_list.filter(**filters)
        else:
            raise Unauthorized("You must be authenticated.")

    read_detail = create_detail = update_detail = delete_detail = all_detail
    read_list = all_list # create_list = update_list = delete_list = disallowed system wide
