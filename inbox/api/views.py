from notifications.models import Notification
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from inbox.api.serializers import NotificationSerializer


class NotificationViewSet(viewsets.GenericViewSet,
                          viewsets.mixins.ListModelMixin):
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    filterset_fields = ('unread',)

    def get_queryset(self):
        # 下面两句等价
        return Notification.objects.filter(recipient=self.request.user)
        # return self.request.user.notifications.all()

    @action(methods=['GET'], detail=False, url_path='unread-count')
    # GET /api/notifications/unread-count
    def unread_count(self, request, *args, **kwargs):
        count = self.get_queryset().filter(unread=True).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='mark-all-as-read')
    # POST /api/notifications/mark-all-as-read
    def mark_all_as_read(self, request, *args, **kwargs):
        undated_count = self.get_queryset().filter(unread=True).update(unread=False)
        return Response({'marked_count': undated_count}, status=status.HTTP_200_OK)
