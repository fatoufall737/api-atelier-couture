from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["admin", "tailleur", "accueil"]


class UtilisateurCreate(BaseModel):
    email: EmailStr
    nom_complet: str = Field(min_length=1, max_length=150)
    mot_de_passe: str = Field(min_length=8, max_length=128)  # RG21 : 8 caractères minimum
    role: Role


class UtilisateurUpdate(BaseModel):
    nom_complet: str | None = Field(default=None, min_length=1, max_length=150)
    role: Role | None = None
    actif: bool | None = None
    mot_de_passe: str | None = Field(default=None, min_length=8, max_length=128)


class UtilisateurRead(BaseModel):
    """Jamais de mot de passe ni de hash dans ce schéma (RG21)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nom_complet: str
    role: Role
    actif: bool
    created_at: datetime