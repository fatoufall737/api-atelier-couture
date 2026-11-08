from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.deps import Accueil, Admin, DbSession, UtilisateurConnecte
from app.schemas.commande import CommandeRead
from app.services import commande_edition_service as svc

router = APIRouter(tags=["commandes"])


class PaiementOut(BaseModel):
    id: int
    commande_id: int
    montant: int
    mode: str
    reference: str | None = None
    date_paiement: date
    model_config = {"from_attributes": True}


class CommandeUpdate(BaseModel):
    mesure_id: int | None = None
    date_livraison_prevue: date | None = None
    remise: int | None = Field(default=None, ge=0)
    notes: str | None = None


class LigneCreate(BaseModel):
    type_vetement_id: int
    description: str | None = None
    quantite: int = Field(gt=0)
    prix_unitaire: int | None = Field(default=None, ge=0)


@router.patch("/commandes/{commande_id}", response_model=CommandeRead)
def modifier(commande_id: int, corps: CommandeUpdate, db: DbSession, user: Accueil):
    commande = svc.modifier_commande(db, commande_id, corps.model_dump(exclude_unset=True))
    db.commit()
    return commande


@router.post("/commandes/{commande_id}/lignes", response_model=CommandeRead, status_code=201)
def ajouter(commande_id: int, corps: LigneCreate, db: DbSession, user: Accueil):
    commande = svc.ajouter_ligne(db, commande_id, corps.model_dump())
    db.commit()
    return commande


@router.delete("/commandes/{commande_id}/lignes/{ligne_id}", response_model=CommandeRead)
def retirer(commande_id: int, ligne_id: int, db: DbSession, user: Accueil):
    commande = svc.retirer_ligne(db, commande_id, ligne_id)
    db.commit()
    return commande


@router.get("/commandes/{commande_id}/paiements", response_model=list[PaiementOut])
def lister(commande_id: int, db: DbSession, user: UtilisateurConnecte):
    return svc.lister_paiements(db, commande_id)


@router.delete("/paiements/{paiement_id}", status_code=204)
def annuler(paiement_id: int, db: DbSession, user: Admin):
    svc.annuler_paiement(db, paiement_id)
    db.commit()
