from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from public_lobby.models import PublicLobby, LobbyParticipant
from public_lobby.serializers import (
    PublicLobbyListSerializer,
    PublicLobbyDetailSerializer,
    PublicLobbyCreateSerializer,
    JoinLobbySerializer
)
from core.utils import generate_anon_token, get_client_ip, get_user_agent
from core.models import RANK_CHOICES_BY_GAME


class PublicLobbyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Public Lobbies
    
    list: Get all active lobbies
    retrieve: Get specific lobby details
    create: Create new lobby
    join: Join a lobby (POST /lobbies/{id}/join/)
    leave: Leave a lobby (POST /lobbies/{id}/leave/)
    ranks: Get valid ranks for a game (GET /lobbies/ranks/?game=valorant)
    """
    queryset = PublicLobby.objects.filter(status='active')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PublicLobbyListSerializer
        elif self.action == 'create':
            return PublicLobbyCreateSerializer
        return PublicLobbyDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """List active lobbies with filtering"""
        queryset = self.get_queryset()
        
        # Filter by game
        game = request.query_params.get('game')
        if game:
            queryset = queryset.filter(game=game)
        
        # Filter by rank
        rank = request.query_params.get('rank')
        if rank:
            queryset = queryset.filter(rank=rank)
        
        # Filter by vibe
        vibe = request.query_params.get('vibe')
        if vibe:
            queryset = queryset.filter(vibe=vibe)
        
        # Filter by mic requirement
        mic_required = request.query_params.get('mic_required')
        if mic_required is not None:
            mic_bool = mic_required.lower() == 'true'
            queryset = queryset.filter(mic_required=mic_bool)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def ranks(self, request):
        """
        Get valid ranks for a specific game
        Usage: GET /api/lobbies/ranks/?game=valorant
        """
        game = request.query_params.get('game')
        
        if not game:
            return Response(
                {"error": "game parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if game not in RANK_CHOICES_BY_GAME:
            return Response(
                {"error": f"Invalid game. Valid games: {', '.join(RANK_CHOICES_BY_GAME.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ranks = [
            {"value": rank[0], "label": rank[1]}
            for rank in RANK_CHOICES_BY_GAME[game]
        ]
        
        return Response({"game": game, "ranks": ranks})
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """
        Join a lobby with abuse protection
        Body: {"nickname": "PlayerName"} (optional)
        """
        lobby = self.get_object()
        
        # Generate anon_token from IP + User Agent
        ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        anon_token = generate_anon_token(ip, user_agent)
        
        # Validate
        serializer = JoinLobbySerializer(
            data=request.data,
            context={'lobby': lobby, 'anon_token': anon_token}
        )
        serializer.is_valid(raise_exception=True)
        
        # Create participant
        participant = LobbyParticipant.objects.create(
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
                "participant_id": participant.id,
                "lobby": PublicLobbyDetailSerializer(lobby).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """
        Leave a lobby
        Uses anon_token to identify participant
        """
        lobby = self.get_object()
        
        # Generate anon_token
        ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        anon_token = generate_anon_token(ip, user_agent)
        
        # Find and delete participant
        try:
            participant = LobbyParticipant.objects.get(
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
                    "lobby": PublicLobbyDetailSerializer(lobby).data
                },
                status=status.HTTP_200_OK
            )
        
        except LobbyParticipant.DoesNotExist:
            return Response(
                {"error": "You are not in this lobby"},
                status=status.HTTP_404_NOT_FOUND
            )
