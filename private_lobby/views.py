from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from private_lobby.models import PrivateLobby, PrivateLobbyParticipant
from private_lobby.serializers import (
    PrivateLobbyListSerializer,
    PrivateLobbyDetailSerializer,
    PrivateLobbyCreateSerializer,
    JoinPrivateLobbySerializer  
)
from core.utils import generate_anon_token, get_client_ip, get_user_agent
import requests

class PrivateLobbyViewSet(viewsets.ModelViewSet): 
    """
    ViewSet for Private Lobbies
    
    list: Get creator's lobbies (only their own)
    retrieve: Get specific lobby details (by ID or code)
    create: Create new private lobby
    join: Join a lobby (POST /private-lobbies/join/{code}/)
    leave: Leave a lobby (POST /private-lobbies/{id}/leave/)
    by_code: Get lobby by code (GET /private-lobbies/by-code/{code}/)
    """
    queryset = PrivateLobby.objects.filter(status='active')  
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PrivateLobbyListSerializer  
        elif self.action == 'create':
            return PrivateLobbyCreateSerializer  
        return PrivateLobbyDetailSerializer  
    
    def get_queryset(self):
        """Filter to only show creator's own lobbies in list view"""
        queryset = super().get_queryset()
        
        # For list view, only show user's own lobbies
        if self.action == 'list':
            anon_token = self.request.headers.get("X-ANON-TOKEN")
            queryset = queryset.filter(creator_token=anon_token)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new private lobby"""
        # Generate creator's anon token
        creator_token = request.headers.get("X-ANON-TOKEN")
        if not creator_token:
            return Response({"error": "Missing token"}, status=400)
        
        serializer = self.get_serializer(
            data=request.data,
            context={'creator_token': creator_token})
        serializer.is_valid(raise_exception=True)
        lobby = serializer.save()  
        
        return Response(
            {
                "message": "Lobby created successfully",  
                "lobby_code": lobby.lobby_code,  
                "lobby": PrivateLobbyDetailSerializer(  
                    lobby, 
                    context={'request': request}
                ).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], url_path='by-code/(?P<code>[^/.]+)')
    def by_code(self, request, code=None):
        """
        Get lobby by code instead of UUID
        Usage: GET /api/private-lobbies/by-code/ABC123XY/
        """
        lobby = get_object_or_404( 
            PrivateLobby,  
            lobby_code=code.upper(),  
            status='active'
        )
        
        # Check if expired
        if lobby.is_expired:
            return Response(
                {"error": "This lobby has expired"}, 
                status=status.HTTP_410_GONE
            )
        
        serializer = PrivateLobbyDetailSerializer(  
            lobby, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='join/(?P<code>[^/.]+)')
    def join_by_code(self, request, code=None):
        """
        Join lobby by code
        Usage: POST /api/private-lobbies/join/ABC123XY/
        Body: {"nickname": "PlayerName"} (optional)
        """
        lobby = get_object_or_404(PrivateLobby, lobby_code=code.upper())
    
        anon_token = request.headers.get("X-ANON-TOKEN")
        if not anon_token:
            return Response({"error": "Missing token"}, status=400)
        
        # Validate
        serializer = JoinPrivateLobbySerializer(  
            data=request.data,
            context={'lobby': lobby, 'anon_token': anon_token} 
        )
        serializer.is_valid(raise_exception=True)
        
        # Create participant
        participant = PrivateLobbyParticipant.objects.create(  
            lobby=lobby,  
            anon_token=anon_token,
            nickname=serializer.validated_data.get('nickname', '')
        )
        
        # Update lobby status if full
        if lobby.is_full:
            lobby.status = 'full'
            lobby.save()
        
        return Response(
            {
                "message": "Successfully joined lobby", 
                "participant_id": str(participant.id),
                "lobby": PrivateLobbyDetailSerializer(  
                    lobby,  
                    context={'request': request}
                ).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """
        Leave a lobby
        Creator cannot leave their own lobby
        """
        lobby = self.get_object() 
        
        # Generate anon_token
        ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        anon_token = generate_anon_token(ip, user_agent)
        
        # Check if user is creator
        if lobby.creator_token == anon_token:
            return Response(
                {"error": "Creator cannot leave their own lobby. Delete it instead."},  
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Find and delete participant
        try:
            participant = PrivateLobbyParticipant.objects.get(  
                lobby=lobby,  
                anon_token=anon_token
            )
            participant.delete()
            
            # Update lobby status if no longer full
            if lobby.status == 'full' and not lobby.is_full:
                lobby.status = 'active'
                lobby.save()
            
            return Response(
                {
                    "message": "Successfully left lobby", 
                    "lobby": PrivateLobbyDetailSerializer( 
                        lobby, 
                        context={'request': request}
                    ).data
                },
                status=status.HTTP_200_OK
            )
        
        except PrivateLobbyParticipant.DoesNotExist: 
            return Response(
                {"error": "You are not in this lobby"},  
                status=status.HTTP_404_NOT_FOUND
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete lobby (creator only)
        """
        lobby = self.get_object() 
        
        # Generate anon_token
        ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        anon_token = generate_anon_token(ip, user_agent)
        
        # Check if user is creator
        if lobby.creator_token != anon_token:
            return Response(
                {"error": "Only the creator can delete this lobby"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Archive and delete
        lobby.archive_and_delete()
        
        return Response(
            {"message": "Lobby deleted successfully"},  
            status=status.HTTP_204_NO_CONTENT
        )