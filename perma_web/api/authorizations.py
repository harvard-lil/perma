from tastypie.authorization import ReadOnlyAuthorization
from tastypie.exceptions import Unauthorized

class LinkAuthorization(ReadOnlyAuthorization):

    def create_detail(self, object_list, bundle):
        if bundle.request.user:
            return True
        else:
           raise Unauthorized("You must be a registered user to create an archive.")

    def update_detail(self, object_list, bundle):
        if bundle.obj.created_by == bundle.request.user:
            return True
        else:
            raise Unauthorized("Sorry, you're not the owner of that archive.")

    def delete_detail(self, object_list, bundle):
        return self.update_detail(object_list, bundle)
