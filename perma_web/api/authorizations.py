from tastypie.authorization import ReadOnlyAuthorization
from tastypie.exceptions import Unauthorized

class DefaultAuthorization(ReadOnlyAuthorization):

    def create_detail(self, object_list, bundle):
        if bundle.request.user:
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
