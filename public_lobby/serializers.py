from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from public_lobby.models import PublicLobby, LobbyParticipant
from core.models import RANK_CHOICES_BY_GAME, GameChoices, VibeChoices


class LobbyParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = LobbyParticipant
        fields = ['id', 'nickname', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class PublicLobbyListSerializer(serializers.ModelSerializer):
    """List view - minimal data"""
    display_title = serializers.CharField(read_only=True)
    participant_count = serializers.SerializerMethodField()
    is_full = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PublicLobby
        fields = [
            'id', 'display_title', 'game', 'rank', 'vibe',
            'mic_required', 'region', 'participant_count',
            'max_participants', 'is_full', 'status', 'created_at'
        ]
    
    def get_participant_count(self, obj):
        return obj.participants.count()


class PublicLobbyDetailSerializer(serializers.ModelSerializer):
    """Detail view - includes participants"""
    display_title = serializers.CharField(read_only=True)
    participants = LobbyParticipantSerializer(many=True, read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PublicLobby
        fields = [
            'id', 'display_title', 'game', 'rank', 'vibe',
            'mic_required', 'region', 'participants', 'participant_count',
            'max_participants', 'is_full', 'status',
            'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']
    
    def get_participant_count(self, obj):
        return obj.participants.count()


class PublicLobbyCreateSerializer(serializers.ModelSerializer):
    """Create lobby with validation"""
    
    class Meta:
        model = PublicLobby
        fields = [
            'game', 'rank', 'vibe', 'mic_required',
            'region', 'max_participants'
        ]
    
    def validate(self, data):
        # Validate rank for selected game
        game = data.get('game')
        rank = data.get('rank')
        
        if game not in RANK_CHOICES_BY_GAME:
            raise serializers.ValidationError(f"Invalid game: {game}")
        
        valid_ranks = [r[0] for r in RANK_CHOICES_BY_GAME[game]]
        if rank not in valid_ranks:
            raise serializers.ValidationError(
                f"Invalid rank '{rank}' for game '{game}'. "
                f"Valid ranks: {', '.join(valid_ranks)}"
            )
        
        return data
    
    def create(self, validated_data):
        # Set expiry to 24 hours from now
        validated_data['expires_at'] = timezone.now() + timedelta(hours=24)
        return super().create(validated_data)


class JoinLobbySerializer(serializers.Serializer):
    """Join lobby with abuse protection"""
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    def validate(self, data):
        lobby = self.context['lobby']
        anon_token = self.context['anon_token']
        
        # Check if lobby is full
        if lobby.is_full:
            raise serializers.ValidationError("Lobby is full")
        
        # Check if lobby is expired
        if lobby.is_expired:
            raise serializers.ValidationError("Lobby has expired")
        
        # Check if user already joined (abuse protection)
        if LobbyParticipant.objects.filter(
            lobby=lobby,
            anon_token=anon_token
        ).exists():
            raise serializers.ValidationError(
                "You have already joined this lobby"
            )
        
        return data