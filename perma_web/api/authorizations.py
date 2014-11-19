from tastypie.authorization import ReadOnlyAuthorization
from tastypie.exceptions import Unauthorized

class DefaultAuthorization(ReadOnlyAuthorization):

    def __init__(self, user_field='user'):
        self.user_field = user_field
    
    def create_detail(self, object_list, bundle):
        if bundle.request.user:
            return True
        else:
           raise Unauthorized("You must be a registered user.")

    def update_detail(self, object_list, bundle):
        if getattr(bundle.obj, self.user_field) == bundle.request.user:
            return True
        else:
            raise Unauthorized("Sorry, you're not the owner of that resource.")

    def delete_detail(self, object_list, bundle):
        return self.update_detail(object_list, bundle)
