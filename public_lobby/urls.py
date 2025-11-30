from django.urls import path, include
from rest_framework.routers import DefaultRouter
from public_lobby.views import PublicLobbyViewSet

router = DefaultRouter()
router.register(r'public-lobbies', PublicLobbyViewSet, basename='public-lobby')

urlpatterns = [
    path('', include(router.urls)),
]