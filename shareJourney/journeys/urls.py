from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('journey',views.JourneyViewSet,basename='journey')
router.register('get_journey',views.JourneyGetViewSet,basename='get_journey')
router.register('post',views.PostViewSet,basename='post')
router.register('user',views.UserViewSet)
urlpatterns = [
    path('', include(router.urls), name="index")
]