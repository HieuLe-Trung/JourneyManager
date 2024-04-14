from django.db.models import Q
from django.shortcuts import render
from oauth2_provider.contrib.rest_framework import permissions
from rest_framework import viewsets, generics, parsers, status, permissions
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.response import Response

from journeys import serializers, perms, paginators
from journeys.models import User, Journey


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):  # post nên dùng create
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

        q = self.request.query_params.get("q")  # search /?q=...
        if q:
            try:
                q_int = int(q)
                queries = queries.filter(Q(name_journey__icontains=q) | Q(pk=q_int))
            except ValueError:
                queries = queries.filter(name_journey__icontains=q)

        return queries


def index(request):
    return HttpResponse("Share Journey App")
