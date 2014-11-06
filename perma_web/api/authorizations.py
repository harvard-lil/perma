from tastypie.authorization import DjangoAuthorization

class DefaultAuthorization(DjangoAuthorization):
    def create_list(self, object_list, bundle):
        raise Unauthorized("Sorry, no mass creates.")

    # def create_detail(self, object_list, bundle):
        # return bundle.obj.user == bundle.request.user

    def update_list(self, object_list, bundle):
        raise Unauthorized("Sorry, no mass updates.")

    # def update_detail(self, object_list, bundle):
        # return bundle.obj.user == bundle.request.user

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Sorry, no mass deletes.")

    # def delete_detail(self, object_list, bundle):
        # return bundle.obj.user == bundle.request.user
