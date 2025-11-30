from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
import random
import string
from private_lobby.models import PrivateLobby, PrivateLobbyParticipant


def generate_lobby_code(length=8):  
    """Generate random alphanumeric lobby code"""
    chars = string.ascii_uppercase + string.digits
    # Exclude confusing characters: 0, O, I, 1
    chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    return ''.join(random.choice(chars) for _ in range(length))


class PrivateLobbyParticipantSerializer(serializers.ModelSerializer):  
    class Meta:
        model = PrivateLobbyParticipant  
        fields = ['id', 'nickname', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class PrivateLobbyListSerializer(serializers.ModelSerializer): 
    """List view for creator - see their lobbies"""
    participant_count = serializers.SerializerMethodField()
    is_full = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PrivateLobby  
        fields = [
            'id', 'lobby_code', 'participant_count',  
            'max_participants', 'is_full', 'is_expired',
            'status', 'created_at', 'expires_at'
        ]
    
    def get_participant_count(self, obj):
        return obj.participants.count()


class PrivateLobbyDetailSerializer(serializers.ModelSerializer):  
    """Detail view - includes participants"""
    participants = PrivateLobbyParticipantSerializer(many=True, read_only=True)  
    participant_count = serializers.SerializerMethodField()
    is_full = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_creator = serializers.SerializerMethodField()
    
    class Meta:
        model = PrivateLobby  
        fields = [
            'id', 'lobby_code', 'participants', 'participant_count',  
            'max_participants', 'is_full', 'is_expired', 'is_creator',
            'status', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'lobby_code', 'status', 'created_at']  
    
    def get_participant_count(self, obj):
        return obj.participants.count()
    
    def get_is_creator(self, obj):
        """Check if current user is creator"""
        request = self.context.get('request')
        if not request:
            return False
        
        from core.utils import generate_anon_token, get_client_ip, get_user_agent
        anon_token = generate_anon_token(
            get_client_ip(request),
            get_user_agent(request)
        )
        return obj.creator_token == anon_token


class PrivateLobbyCreateSerializer(serializers.ModelSerializer):  
    """Create private lobby"""
    
    class Meta:
        model = PrivateLobby  
        fields = ['max_participants']
    
    def validate_max_participants(self, value):
        if value < 2 or value > 5:
            raise serializers.ValidationError(
                "Private lobbies must have 2-5 participants"  
            )
        return value
    
    def create(self, validated_data):
        # Generate unique lobby code
        while True:
            lobby_code = generate_lobby_code() 
            if not PrivateLobby.objects.filter(lobby_code=lobby_code).exists():  
                break
        
        # Set creator token from request context
        creator_token = self.context['creator_token']
        
        # Set expiry to 24 hours
        validated_data['lobby_code'] = lobby_code  
        validated_data['creator_token'] = creator_token
        validated_data['expires_at'] = timezone.now() + timedelta(hours=24)
        
        lobby = super().create(validated_data)  
        
        # Auto-join creator as first participant
        PrivateLobbyParticipant.objects.create(  
            lobby=lobby,  
            anon_token=creator_token,
            nickname=""  # Creator can set nickname later
        )
        
        return lobby  


class JoinPrivateLobbySerializer(serializers.Serializer):  
    """Join lobby with abuse protection"""
    nickname = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True
    )
    
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
        if PrivateLobbyParticipant.objects.filter(  
            lobby=lobby, 
            anon_token=anon_token
        ).exists():
            raise serializers.ValidationError(
                "You have already joined this lobby" 
            )
        
        return data