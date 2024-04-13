from django.shortcuts import render
from oauth2_provider.contrib.rest_framework import permissions
from rest_framework import viewsets, generics, parsers, status
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.response import Response

from journeys import serializers
from journeys.models import User


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


def index(request):
    return HttpResponse("Share Journey App")
