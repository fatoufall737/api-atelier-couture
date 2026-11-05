from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.telephone import normaliser_telephone

Genre = Literal["homme", "femme", "enfant"]


class ClientCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    telephone: str
    email: EmailStr | None = None
    adresse: str | None = Field(default=None, max_length=255)
    genre: Genre | None = None
    notes: str | None = None

    @field_validator("telephone")
    @classmethod
    def _telephone(cls, v: str) -> str:
        return normaliser_telephone(v)


class ClientUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nom: str | None = Field(default=None, min_length=1, max_length=100)
    prenom: str | None = Field(default=None, min_length=1, max_length=100)
    telephone: str | None = None
    email: EmailStr | None = None
    adresse: str | None = Field(default=None, max_length=255)
    genre: Genre | None = None
    notes: str | None = None

    @field_validator("telephone")
    @classmethod
    def _telephone(cls, v: str | None) -> str | None:
        return None if v is None else normaliser_telephone(v)

    @model_validator(mode="after")
    def _champs_obligatoires(self):
        # route 10 : nom, prenom et telephone ne peuvent pas être vidés (422)
        for champ in ("nom", "prenom", "telephone"):
            if champ in self.model_fields_set and getattr(self, champ) is None:
                raise ValueError(f"Le champ « {champ} » ne peut pas être vidé")
        return self


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    prenom: str
    telephone: str
    email: str | None
    adresse: str | None
    genre: Genre | None
    notes: str | None
    created_at: datetime
    updated_at: datetime