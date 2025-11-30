# Create your models here.

import uuid
import hashlib
from django.db import models
from django.utils import timezone


class GameChoices(models.TextChoices):
    VALORANT = 'valorant', 'Valorant'
    CSGO = 'csgo', 'CS:GO'
    APEX = 'apex', 'Apex Legends'
    LOL = 'lol', 'League of Legends'


class VibeChoices(models.TextChoices):
    SERIOUS = 'serious', 'Serious'
    CHILL = 'chill', 'Chill'
    COMPETITIVE = 'competitive', 'Competitive'
    CASUAL = 'casual', 'Casual'
    TRYHARD = 'tryhard', 'Tryhard'


# Game-specific rank choices
VALORANT_RANKS = [
    ('iron1', 'Iron 1'), ('iron2', 'Iron 2'), ('iron3', 'Iron 3'),
    ('bronze1', 'Bronze 1'), ('bronze2', 'Bronze 2'), ('bronze3', 'Bronze 3'),
    ('silver1', 'Silver 1'), ('silver2', 'Silver 2'), ('silver3', 'Silver 3'),
    ('gold1', 'Gold 1'), ('gold2', 'Gold 2'), ('gold3', 'Gold 3'),
    ('platinum1', 'Platinum 1'), ('platinum2', 'Platinum 2'), ('platinum3', 'Platinum 3'),
    ('diamond1', 'Diamond 1'), ('diamond2', 'Diamond 2'), ('diamond3', 'Diamond 3'),
    ('ascendant1', 'Ascendant 1'), ('ascendant2', 'Ascendant 2'), ('ascendant3', 'Ascendant 3'),
    ('immortal1', 'Immortal 1'), ('immortal2', 'Immortal 2'), ('immortal3', 'Immortal 3'),
    ('radiant', 'Radiant'),
    ('unranked', 'Unranked'),
]

CSGO_RANKS = [
    ('0-1k', '0-1k Rating'),
    ('1k-5k', '1k-5k Rating'),
    ('5k-10k', '5k-10k Rating'),
    ('10k-15k', '10k-15k Rating'),
    ('15k-20k', '15k-20k Rating'),
    ('20k+', '20k+ Rating'),
    ('unranked', 'Unranked'),
]

APEX_RANKS = [
    ('rookie', 'Rookie'),
    ('bronze', 'Bronze'),
    ('silver', 'Silver'),
    ('gold', 'Gold'),
    ('platinum', 'Platinum'),
    ('diamond', 'Diamond'),
    ('master', 'Master'),
    ('predator', 'Predator'),
    ('unranked', 'Unranked'),
]

LOL_RANKS = [
    ('iron', 'Iron'), ('bronze', 'Bronze'), ('silver', 'Silver'),
    ('gold', 'Gold'), ('platinum', 'Platinum'), ('diamond', 'Diamond'),
    ('master', 'Master'), ('grandmaster', 'Grandmaster'),
    ('challenger', 'Challenger'), ('unranked', 'Unranked'),
]

RANK_CHOICES_BY_GAME = {
    'valorant': VALORANT_RANKS,
    'csgo': CSGO_RANKS,
    'apex': APEX_RANKS,
    'lol': LOL_RANKS,
}


class BaseLobbyModel(models.Model):
    """Abstract base for both private and public invites"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    
    class Meta:
        abstract = True