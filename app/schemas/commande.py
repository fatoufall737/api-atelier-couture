from datetime import date
from pydantic import BaseModel, ConfigDict, Field, model_validator


class LigneCommandeCreate(BaseModel):
    type_vetement_id: int
    description: str | None = None
    quantite: int = Field(gt=0)
    prix_unitaire: int = Field(ge=0)


class CommandeCreate(BaseModel):
    client_id: int
    mesure_id: int | None = None
    date_livraison_prevue: date
    remise: int = Field(default=0, ge=0)
    notes: str | None = None
    lignes: list[LigneCommandeCreate] = Field(min_length=1)


class LigneCommandeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type_vetement_id: int
    description: str | None
    quantite: int
    prix_unitaire: int


class CommandeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    client_id: int
    mesure_id: int | None
    statut: str
    date_commande: date
    date_livraison_prevue: date
    date_livraison_reelle: date | None
    remise: int
    montant_total: int
    montant_paye: int
    notes: str | None
    lignes: list[LigneCommandeRead]

    @property
    def solde(self) -> int:
        return self.montant_total - self.montant_paye