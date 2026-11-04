from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Role = Literal["admin", "tailleur", "accueil"]


class UtilisateurRead(BaseModel):
    """Jamais de mot de passe ni de hash dans ce schéma (RG21)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nom_complet: str
    role: Role
    actif: bool
    created_at: datetime