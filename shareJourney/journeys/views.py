from django.db.models import Q
from django.shortcuts import render
from oauth2_provider.contrib.rest_framework import permissions
from rest_framework import viewsets, generics, parsers, status, permissions
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.response import Response

from journeys import serializers, perms, paginators
from journeys.models import User, Journey, Post


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.RetrieveAPIView):  # post nên dùng create
    queryset = User.objects.filter(is_active=True).all()
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.MultiPartParser]

    def get_permissions(self):
        if self.action.__eq__('current_user'):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    # lấy thông tin người đang đăng nhập để hiển thị profile
    @action(methods=['get'], url_name='current_user', detail=False)
    def current_user(self, request):
        return Response(serializers.UserSerializer(request.user).data)


class JourneyViewSet(viewsets.ViewSet, generics.UpdateAPIView, generics.DestroyAPIView, generics.CreateAPIView):
    queryset = Journey.objects.all()
    serializer_class = serializers.JourneySerializer
    permission_classes = [perms.OwnerAuthenticated]

    def perform_create(self, serializer):  # khi gọi api create sẽ lấy user đang đăng nhập gán vào
        serializer.save(user_create=self.request.user)


class JourneyGetViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Journey.objects.all()
    serializer_class = serializers.JourneySerializer
    pagination_class = paginators.JourneyPaginator

    def get_queryset(self):
        queries = self.queryset

        q = self.request.query_params.get("q")  # khi search /?q=... thì lấy giá trị q về
        if q:
            queries = queries.filter(name_journey__icontains=q)

        return queries


class PostViewSet(viewsets.ViewSet, generics.RetrieveAPIView, generics.UpdateAPIView, generics.DestroyAPIView, generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = serializers.PostSerializer
    permission_classes = [permissions.AllowAny()]

    def perform_create(self, serializer):  #user đăng bài
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [perms.OwnerPostAuthenticated()]
        else:
            return [permissions.AllowAny()]


def index(request):
    return HttpResponse("Share Journey App")
