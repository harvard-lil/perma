import csv

from django.db.models import Prefetch
from django.http import HttpResponse
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from perma.models import CaptureJob, LinkBatch

from ..serializers import DetailedLinkBatchSerializer, LinkBatchSerializer
from ..utils import dispatch_multiple_requests, reverse_api_view_relative
from .base import BaseView


# /archives/batches
class LinkBatchesListView(BaseView):
    serializer_class = LinkBatchSerializer
    queryset = (LinkBatch.objects
        .select_related('target_folder')
        # order capture_jobs for each batch by order they were run
        .prefetch_related(
            Prefetch(
                'capture_jobs',
                queryset=CaptureJob.objects.order_by('-human', 'order', 'pk').select_related('link')
            ))
        # order batches by most recent first
        .order_by('-started_on'))

    def get(self, request, format=None):
        """
        List link batches for user.
        """
        return self.simple_list(
            request,
            queryset=self.queryset.filter(created_by=request.user.pk),
            serializer_class=DetailedLinkBatchSerializer
        )

    def post(self, request, format=None):
        """
        Create link batch.
        """
        # mark batch with user
        if not request.user.is_authenticated:
            raise PermissionDenied()
        if request.content_type != 'application/json':
            content = {'detail': 'content-type must be aplication/json'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        request.data['created_by'] = request.user.pk

        # save batch
        serializer = self.serializer_class(data=request.data, context={'request': self.request})
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)
        serializer.save(created_by=request.user)

        # Attempt creation of Perma Links
        path = reverse_api_view_relative('archives')
        batch_id = serializer.data['id']
        call_list = [
            {
                'path': path,
                'verb': 'POST',
                'data': {
                    'url': url,
                    'folder': request.data['target_folder'],
                    'human': request.data.get('human', False)
                }
            } for url in request.data.get('urls', [])
        ]
        dispatch_multiple_requests(request, call_list, {"batch": batch_id})
        # TODO: how can we communicate these errors to the user?
        # if dispatch_multiple_requests returns to "responses"
        # internal_server_errors = [
        #     response['data']['data']['url'] for response in responses if response['status_code'] == 500
        # ]
        # Get an up-to-date version of this LinkBatch's data,
        # formatted by the LinkBatch serializer
        call_for_fresh_serializer_data = [{
            'path': reverse_api_view_relative('link_batch', kwargs={"pk": batch_id}),
            'verb': 'GET'
        }]
        response = dispatch_multiple_requests(request, call_for_fresh_serializer_data)
        data = response[0]['data'].copy()
        links_remaining = request.user.get_links_remaining()
        data['links_remaining'] = 'Infinity' if links_remaining[0] == float('inf') else links_remaining[0]
        data['links_remaining_period'] = links_remaining[1]
        return Response(data, status=status.HTTP_201_CREATED)


# /archives/batches/:id
class LinkBatchesDetailView(BaseView):
    serializer_class = DetailedLinkBatchSerializer
    queryset = LinkBatchesListView.queryset

    def get(self, request, pk, format=None):
        """
        Single link batch details
        """
        return self.simple_get(request, pk)


# /archives/batches/:id/export
class LinkBatchesDetailExportView(LinkBatchesDetailView):
    def get(self, request, pk, format=None):
        """
        Single link batch details
        """
        api_response = self.simple_get(request, pk)
        formatted_data = [
            {
                'url': job['submitted_url'],
                'status': "success",
                'error_message': "",
                'title': job['title'],
                'perma_link': f"{request.scheme}://{request.get_host()}/{job['guid']}"
            } if job['status'] == "completed" else {
                'url': job['submitted_url'],
                'status': "error",
                'error_message': job['message'],
                'title': "",
                "perma_link": ""
            }
            for job in api_response.data['capture_jobs']
        ]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="perma-batch-{pk}.csv"'
        if formatted_data:
            writer = csv.DictWriter(response, fieldnames=list(formatted_data[0].keys()))
            writer.writeheader()
            writer.writerows(formatted_data)
        return response
