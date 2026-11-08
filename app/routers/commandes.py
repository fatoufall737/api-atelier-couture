from typing import Literal
from fastapi import APIRouter, Response, status
from sqlalchemy import select

from app.deps import Accueil, DbSession, Tailleur, UtilisateurConnecte
from app.models.commande import Commande, HistoriqueStatut
from app.schemas.commande import CommandeCreate, CommandeRead
from app.services import commande_service
from app.exceptions import NonTrouve, DonneesInvalides
from datetime import date
from pydantic import BaseModel, Field
from app.models.commande import Paiement, Livraison

router = APIRouter(tags=["Commandes"])


@router.post(
    "/commandes",
    response_model=CommandeRead,
    status_code=status.HTTP_201_CREATED,
)
def creer_commande(
    data: CommandeCreate,
    db: DbSession,
    utilisateur: Accueil,
):
    try:
        commande = commande_service.creer_commande(db, data, utilisateur.id)
        db.commit()
        return commande
    except ValueError as erreur:
        raise DonneesInvalides(str(erreur))


@router.get("/commandes", response_model=list[CommandeRead])
def lister_commandes(
    db: DbSession,
    _: UtilisateurConnecte,
):
    return db.scalars(
        select(Commande).order_by(Commande.created_at.desc())
    ).all()


@router.get("/commandes/{commande_id}", response_model=CommandeRead)
def detail_commande(
    commande_id: int,
    db: DbSession,
    _: UtilisateurConnecte,
):
    commande = db.get(Commande, commande_id)

    if commande is None:
        raise NonTrouve("Commande introuvable.")

    return commande


class StatutEntree(BaseModel):
    statut: Literal["en_attente", "en_coupe", "en_couture", "essayage",
                    "retouches", "terminee", "livree", "annulee"]
    commentaire: str | None = None


@router.post("/commandes/{commande_id}/statut", response_model=CommandeRead)
def modifier_statut(commande_id: int, data: StatutEntree, db: DbSession, utilisateur: UtilisateurConnecte):
    commande = edition_service.changer_statut(db, commande_id, data.statut, data.commentaire, utilisateur)
    db.commit()
    return commande


@router.get("/commandes/{commande_id}/historique")
def historique_commande(commande_id: int, db: DbSession, _: UtilisateurConnecte):
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise NonTrouve("Commande introuvable.")
    lignes = db.scalars(
        select(HistoriqueStatut)
        .where(HistoriqueStatut.commande_id == commande_id)
        .order_by(HistoriqueStatut.date_changement, HistoriqueStatut.id)
    ).all()
    return [
        {
            "id": h.id,
            "ancien_statut": h.ancien_statut,
            "nouveau_statut": h.nouveau_statut,
            "commentaire": h.commentaire,
            "utilisateur_id": h.utilisateur_id,
            "date_changement": h.date_changement,
        }
        for h in lignes
    ]


class PaiementCreate(BaseModel):
    montant: int = Field(gt=0)
    mode: str
    reference: str | None = None


class LivraisonCreate(BaseModel):
    mode: str
    date_prevue: date
    adresse: str | None = None
    livreur: str | None = None
    notes: str | None = None


from typing import Literal
from app.services import commande_edition_service as edition_service


class PaiementEntree(BaseModel):
    montant: int = Field(gt=0)
    mode: Literal["especes", "wave", "orange_money", "virement", "cheque"]
    reference: str | None = None
    date_paiement: date | None = None


@router.post("/commandes/{commande_id}/paiements", status_code=201)
def encaisser_paiement(commande_id: int, data: PaiementEntree, db: DbSession, utilisateur: Accueil):
    p = edition_service.encaisser_paiement(db, commande_id, data.model_dump(), utilisateur.id)
    db.commit()
    return {
        "id": p.id,
        "commande_id": p.commande_id,
        "montant": p.montant,
        "mode": p.mode,
        "reference": p.reference,
        "date_paiement": p.date_paiement,
    }


@router.get("/commandes/statistiques")
def statistiques_commandes(
    db: DbSession,
    _: UtilisateurConnecte
):
    return commande_service.obtenir_statistiques_commandes(db)
