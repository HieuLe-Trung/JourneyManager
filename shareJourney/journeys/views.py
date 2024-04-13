from django.shortcuts import render
from oauth2_provider.contrib.rest_framework import permissions
from rest_framework import viewsets, generics, parsers, status, permissions
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.response import Response

from journeys import serializers
from journeys.models import User, Journey
from journeys.serializers import JourneySerializer


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


class JourneyViewSet(viewsets.ViewSet):
    queryset = Journey.objects.filter(active=True).all()
    serializer_class = JourneySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queries = self.queryset

        q = self.request.query_params.get("q")  # search /?q=...
        if q:
            queries = queries.filter(name_journey__icontains=q)

        return queries

    # def get_permissions(self):
    #     if self.action in ['create_journey']:
    #         return [permissions.IsAuthenticated()]
    #     return self.permission_classes

    @action(detail=False, methods=['GET'])
    def get_journeys(self, request):
        journeys = Journey.objects.all()
        serializer = JourneySerializer(journeys, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def get_journey(self, request, pk=None):
        try:
            journey = Journey.objects.get(pk=pk)
        except Journey.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = JourneySerializer(journey)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'])
    def create_journey(self, request):
        data = request.data.copy()
        data['user_create'] = request.user.id
        serializer = JourneySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['PATCH'])
    def update_journey(self, request, pk=None):
        try:
            journey = Journey.objects.get(pk=pk)
        except Journey.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = JourneySerializer(journey, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['DELETE'])
    def delete_journey(self, request, pk=None):
        try:
            journey = Journey.objects.get(pk=pk)
        except Journey.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        journey.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def index(request):
    return HttpResponse("Share Journey App")
