from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import BaseLobbyModel, GameChoices, VibeChoices
from django.utils import timezone
import uuid


class LobbyStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    FULL = 'full', 'Full'
    EXPIRED = 'expired', 'Expired'


class PublicLobby(BaseLobbyModel):
    """Public 5v5 lobbies with game-specific ranks"""
    game = models.CharField(
        max_length=20,
        choices=GameChoices.choices,
        db_index=True
    )
    rank = models.CharField(
        max_length=20,
        help_text="Game-specific rank (validated in serializer)"
    )
    vibe = models.CharField(
        max_length=20,
        choices=VibeChoices.choices
    )
    mic_required = models.BooleanField(default=False)
    max_participants = models.IntegerField(
        default=10,
        validators=[MinValueValidator(2), MaxValueValidator(10)]
    )
    status = models.CharField(
        max_length=10,
        choices=LobbyStatus.choices,
        default=LobbyStatus.ACTIVE,
        db_index=True
    )
    region = models.CharField(
        max_length=10,
        blank=True,
        help_text="Server region (e.g., NA, EU, ASIA)"
    )

    class Meta:
        db_table = 'public_lobbies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['game', 'status', 'created_at']),
            models.Index(fields=['status', 'expires_at']),
        ]

    def __str__(self):
        return f"{self.game} • {self.rank} • {self.vibe}"

    @property
    def display_title(self):
        """Generate human-readable title"""
        return f"{self.get_game_display()} • {self.rank.title()} • {self.get_vibe_display()}"

    @property
    def is_full(self):
        return self.participants.count() >= self.max_participants

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    def archive_and_delete(self):
        """Archive stats and delete lobby"""
        from public_lobby.models import ArchivedLobbyStats
        
        participant_count = self.participants.count()
        
        ArchivedLobbyStats.objects.create(
            lobby_id=self.id,
            game=self.game,
            rank=self.rank,
            vibe=self.vibe,
            total_participants=participant_count,
            created_at=self.created_at,
            expired_at=timezone.now(),
            mic_required=self.mic_required,
            region=self.region,
        )
        
        self.participants.all().delete()
        self.delete()


class LobbyParticipant(models.Model):
    """Ephemeral participant data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lobby = models.ForeignKey(
        PublicLobby,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    anon_token = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA256(IP+UA+salt) for abuse prevention"
    )
    nickname = models.CharField(max_length=50, blank=True)
    joined_at = models.DateTimeField(default=timezone.now)
    device_fingerprint = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = 'lobby_participants'
        ordering = ['joined_at']
        constraints = [
            models.UniqueConstraint(
                fields=['lobby', 'anon_token'],
                name='unique_participant_per_lobby'
            )
        ]

    def __str__(self):
        name = self.nickname if self.nickname else self.anon_token[:8]
        return f"{name} in {self.lobby_id}"


class ArchivedLobbyStats(models.Model):
    """Archive for analytics - NO PII"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lobby_id = models.UUIDField(db_index=True)
    game = models.CharField(max_length=20, choices=GameChoices.choices)
    rank = models.CharField(max_length=20)
    vibe = models.CharField(max_length=20, choices=VibeChoices.choices)
    total_participants = models.IntegerField()
    created_at = models.DateTimeField()
    expired_at = models.DateTimeField(default=timezone.now)
    mic_required = models.BooleanField(default=False)
    region = models.CharField(max_length=10, blank=True)

    class Meta:
        db_table = 'archived_lobby_stats'
        ordering = ['-expired_at']
        indexes = [
            models.Index(fields=['game', 'expired_at']),
            models.Index(fields=['created_at']),
        ]

    @property
    def duration_minutes(self):
        delta = self.expired_at - self.created_at
        return delta.total_seconds() / 60
