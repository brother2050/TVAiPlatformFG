"""Models package — re-exports all ORM models and schemas."""

from api.models.base import Base, get_db, init_db, close_db
from api.models.project import Project, Episode, ProjectCreate, ProjectUpdate, ProjectOut, EpisodeCreate, EpisodeUpdate, EpisodeOut, ProjectGlobalSettings
from api.models.character import Character, CharacterCreate, CharacterUpdate, CharacterOut, AppearanceSpec, BodySpec, VoiceSpec, WardrobeSpec
from api.models.script import Scene, Shot, SceneCreate, SceneUpdate, SceneOut, ShotUpdate, ShotOut, Position, Dialogue
from api.models.template import JSONTemplate, TemplateCreate, TemplateUpdate, TemplateOut
from api.models.production import ProductionTask, ProductionTaskOut, ProductionProgress
from api.models.summary import Summary, SummaryCreate, SummaryOut

__all__ = [
    "Base", "get_db", "init_db", "close_db",
    "Project", "Episode", "ProjectCreate", "ProjectUpdate", "ProjectOut",
    "EpisodeCreate", "EpisodeUpdate", "EpisodeOut", "ProjectGlobalSettings",
    "Character", "CharacterCreate", "CharacterUpdate", "CharacterOut",
    "AppearanceSpec", "BodySpec", "VoiceSpec", "WardrobeSpec",
    "Scene", "Shot", "SceneCreate", "SceneUpdate", "SceneOut", "ShotUpdate", "ShotOut", "Position", "Dialogue",
    "JSONTemplate", "TemplateCreate", "TemplateUpdate", "TemplateOut",
    "ProductionTask", "ProductionTaskOut", "ProductionProgress",
    "Summary", "SummaryCreate", "SummaryOut",
]
