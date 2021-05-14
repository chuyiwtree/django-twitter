from rest_framework import viewsets, status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from newsfeeds.models import NewsFeed
from newsfeeds.api.serializers import NewsFeedSerializer


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = NewsFeed.objects.all()

    def list(self, request):
        newsfeeds = NewsFeed.objects.filter(user=request.user)
        serializer = NewsFeedSerializer(newsfeeds, many=True)
        return Response({
            'newsfeeds': serializer.data,
        }, status=status.HTTP_200_OK)
