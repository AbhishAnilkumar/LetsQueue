from django.db import models
from core.models import BaseLobbyModel
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.utils import timezone

class PrivateLobbyStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    FULL = 'full', 'Full'
    EXPIRED = 'expired', 'Expired'


class PrivateLobby(BaseLobbyModel):
    """Private 1-5 player lobbies"""
    creator_token = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Anon token of creator"
    )
    max_participants = models.IntegerField(
        default=5,
        validators=[MinValueValidator(2), MaxValueValidator(5)]
    )
    status = models.CharField(
        max_length=10,
        choices=PrivateLobbyStatus.choices,
        default=PrivateLobbyStatus.ACTIVE,
        db_index=True
    )
    lobby_code = models.CharField(
        max_length=8,
        unique=True,
        db_index=True,
        help_text="Short shareable code"
    )

    class Meta:
        db_table = 'private_lobbies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['creator_token', 'created_at']),
        ]

    def __str__(self):
        return f"Private Lobby {self.lobby_code}"

    @property
    def is_full(self):
        return self.participants.count() >= self.max_participants

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    def archive_and_delete(self):
        """Archive stats and delete lobby"""
        
        participant_count = self.participants.count()
        
        ArchivedPrivateLobbyStats.objects.create(
            lobby_id=self.id,
            total_participants=participant_count,
            created_at=self.created_at,
            expired_at=timezone.now(),
        )
        
        self.participants.all().delete()
        self.delete()


class PrivateLobbyParticipant(models.Model):
    """Ephemeral participant data for private lobbies"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lobby = models.ForeignKey(
        PrivateLobby,
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

    class Meta:
        db_table = 'private_lobby_participants'
        ordering = ['joined_at']
        constraints = [
            models.UniqueConstraint(
                fields=['lobby', 'anon_token'],
                name='unique_participant_per_private_lobby'
            )
        ]

    def __str__(self):
        name = self.nickname if self.nickname else self.anon_token[:8]
        return f"{name} in {self.lobby.lobby_code}"


class ArchivedPrivateLobbyStats(models.Model):
    """Archive for analytics - NO PII"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lobby_id = models.UUIDField(db_index=True)
    total_participants = models.IntegerField()
    created_at = models.DateTimeField()
    expired_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'archived_private_lobby_stats'
        ordering = ['-expired_at']

    @property
    def duration_minutes(self):
        delta = self.expired_at - self.created_at
        return delta.total_seconds() / 60