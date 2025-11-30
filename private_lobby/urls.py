from django.urls import path, include
from rest_framework.routers import DefaultRouter
from private_lobby.views import *

router = DefaultRouter()
router.register(r'private-lobbies', PrivateLobbyViewSet, basename='private-lobby')

urlpatterns = [
    path('', include(router.urls)),
]