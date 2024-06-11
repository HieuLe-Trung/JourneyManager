from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import CommentListAPIView, CommentJourneyListAPIView, UserJourneysListView

router = DefaultRouter()
router.register('journey', views.JourneyViewSet, basename='journey')
router.register('post', views.PostViewSet, basename='post')
router.register('user', views.UserViewSet)
# router.register('commentsJourney', views.CommentJourneyViewSet, basename='commentsJourney') # ds cmt của 1 cmt cha
# router.register('commentsPost', views.CommentViewSet, basename='commentsPost')
# router.register('notifications', views.NotificationViewSet)
router.register('Report', views.ReportViewSet)

urlpatterns = [
    path('', include(router.urls), name="index"),
    path('post/<int:pk>/update_comment/<int:comment_pk>/', views.PostViewSet.as_view({'patch': 'update_comment'}),
         name='update_comment'),
    path('post/<int:pk>/delete_comment/<int:comment_pk>/', views.PostViewSet.as_view({'delete': 'delete_comment'}),
         name='delete_comment'),
    path('post/<int:post_id>/comments/', CommentListAPIView.as_view(), name='post-comment-list'),
    path('journey/<int:journey_id>/comments/', CommentJourneyListAPIView.as_view(), name='journey-comment-list'),
    path('user_journeys/', UserJourneysListView.as_view(), name='user_journeys_list'),
]
