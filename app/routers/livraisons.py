from datetime import date
from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.deps import Accueil, DbSession, UtilisateurConnecte
from app.services import livraison_service as svc

router = APIRouter(tags=["Livraisons"])


class LivraisonEntree(BaseModel):
    mode: Literal["retrait_atelier", "domicile"]
    date_prevue: date
    adresse: str | None = None
    livreur: str | None = None
    notes: str | None = None


class ConfirmationEntree(BaseModel):
    date_effective: date | None = None
    autoriser_solde_impaye: bool = False


@router.put("/commandes/{commande_id}/livraison")
def planifier(commande_id: int, data: LivraisonEntree, db: DbSession, user: Accueil):
    liv = svc.planifier(db, commande_id, data.model_dump())
    db.commit()
    return svc.sortie(liv)


@router.get("/commandes/{commande_id}/livraison")
def lire(commande_id: int, db: DbSession, user: UtilisateurConnecte):
    return svc.sortie(svc.lire(db, commande_id))


@router.post("/commandes/{commande_id}/livraison/confirmer")
def confirmer(commande_id: int, db: DbSession, user: Accueil, data: ConfirmationEntree | None = None):
    corps = data.model_dump() if data else {}
    liv = svc.confirmer(db, commande_id, corps, user)
    db.commit()
    return svc.sortie(liv)


@router.get("/livraisons")
def lister(
    db: DbSession,
    user: UtilisateurConnecte,
    statut: Literal["planifiee", "livree"] | None = None,
    date_min: date | None = None,
    date_max: date | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    items, total = svc.lister(db, statut, date_min, date_max, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}
