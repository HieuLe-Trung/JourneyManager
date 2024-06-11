from rest_framework import permissions

from journeys.models import Participation


class OwnerAuthenticated(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request,
                                   view) and request.user == obj.user_create


class OwnerPostAuthenticated(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request,
                                   view) and request.user == obj.user


class MemberJourney(permissions.IsAuthenticated):  # đánh giá hành trình
    def has_object_permission(self, request, view, obj):
        return Participation.objects.get(journey=obj, user=request.user, is_approved=True)
