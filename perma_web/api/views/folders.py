from django.db import transaction
from rest_framework.exceptions import ValidationError

from perma.models import Folder

from ..serializers import FolderSerializer
from ..utils import LongTastypiePagination, load_parent, raise_general_validation_error
from .base import BaseView


# /folders
# /folders/:parent_id/folders
class FolderListView(BaseView):
    serializer_class = FolderSerializer

    @load_parent
    def get(self, request, format=None):
        """
        List folders for user.
        """
        if request.parent:
            # for /folders/:parent_id/folders, list subfolders of parent folder
            queryset = Folder.objects.filter(parent=request.parent)
        else:
            # for /folders, list all top level folders for user
            queryset = request.user.top_level_folders()
        return self.simple_list(request, queryset, paginator_class=LongTastypiePagination)

    @load_parent
    def post(self, request, format=None):
        """
        Create folder.
        """
        # if parent folder is not supplied in post data, try to get it from /folders/:parent_id:
        data = request.data.copy()
        if request.parent:
            data.setdefault('parent', request.parent.pk)
        with transaction.atomic():
            if data.get('parent'):
                # Lock the parent to prevent anyone from deleting it while this operation is validated and saved.
                try:
                    parent = Folder.objects.accessible_to(request.user).select_for_update().get(pk=data['parent'])
                except (Folder.DoesNotExist, TypeError, ValueError):
                    raise ValidationError({
                        'parent': [f'Invalid pk "{data["parent"]}" - object does not exist.']
                    })
                # We don't want to insert any new folders while a tree's folders are being moved around.
                # Since moves lock the whole subtree, we can take out the same lock, to ensure no move is underway.
                Folder.objects.select_for_update().get(pk=parent.tree_root_id)
            return self.simple_create(data, {'created_by': request.user})


# /folders/:id
# /folders/:parent_id/folders/:id
class FolderDetailView(BaseView):
    serializer_class = FolderSerializer

    @load_parent
    def get(self, request, pk, format=None):
        """
        Single folder details
        """
        return self.simple_get(request, pk)

    def folder_update(self, request, pk, data):
        """
        Helper for updating folder details -- used by patch and put methods.
        """
        obj = self.get_object_for_user_by_pk(request.user, pk)
        return self.simple_update(obj, data)

    @load_parent
    def patch(self, request, pk, format=None):
        """
        Update folder.
        """
        return self.folder_update(request, pk, request.data)

    @load_parent
    def put(self, request, pk, format=None):
        """
        Move folder.
        For nested endpoint, PUT /folders/:id into /folders/:parent_id.
        """
        if not request.parent:
            raise_general_validation_error("PUT is only valid for nested folder endpoints.")

        with transaction.atomic():
            # Lock this folder, so no one makes new subfolders inside it, during the transaction
            this = Folder.objects.select_for_update().get(pk=pk)
            # Lock the current subtree, so no one moves anything else around while we are making this move
            Folder.objects.select_for_update().get(pk=this.tree_root_id)
            # Lock the destination subtree, if it's different, for the same reason
            if this.tree_root_id != request.parent.tree_root_id:
                Folder.objects.select_for_update().get(pk=request.parent.tree_root_id)

            return self.folder_update(request, pk, {'parent': request.parent.pk})

    @load_parent
    def delete(self, request, pk, format=None):
        """
        Delete folder.
        """
        folder = self.get_object_for_user_by_pk(request.user, pk)

        # delete validations
        if folder.is_shared_folder or folder.is_root_folder:
            raise_general_validation_error("Top-level folders cannot be deleted.")
        elif not folder.is_empty():
            raise_general_validation_error("Folders can only be deleted if they are empty.")

        return self.simple_delete(folder)
