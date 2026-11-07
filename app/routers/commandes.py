from fastapi import APIRouter, Response, status
from sqlalchemy import select

from app.deps import DbSession, UtilisateurConnecte, Tailleur
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
    utilisateur: Tailleur,
):
    try:
        return commande_service.creer_commande(db, data, utilisateur.id)
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


@router.patch("/commandes/{commande_id}/statut", response_model=CommandeRead)
def modifier_statut(
    commande_id: int,
    nouveau_statut: str,
    db: DbSession,
    utilisateur: Tailleur,
):
    commande = db.get(Commande, commande_id)

    if commande is None:
        raise NonTrouve("Commande introuvable.")

    try:
        return commande_service.changer_statut_commande(
            db, commande, nouveau_statut, utilisateur.id
        )
    except ValueError as erreur:
        raise DonneesInvalides(str(erreur))


@router.get("/commandes/{commande_id}/historique")
def historique_commande(
    commande_id: int,
    db: DbSession,
    _: UtilisateurConnecte,
):
    commande = db.get(Commande, commande_id)

    if commande is None:
        raise NonTrouve("Commande introuvable.")

    return commande_service.obtenir_historique_statuts(db, commande_id)
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


@router.post("/commandes/{commande_id}/paiements", status_code=201)
def ajouter_paiement(
    commande_id: int,
    data: PaiementCreate,
    db: DbSession,
    utilisateur: Tailleur,
):
    commande = db.get(Commande, commande_id)

    if commande is None:
        raise NonTrouve("Commande introuvable.")

    try:
        return commande_service.enregistrer_paiement(
            db, commande, data.montant, data.mode,
            utilisateur.id, data.reference
        )
    except ValueError as erreur:
        raise DonneesInvalides(str(erreur))


@router.post("/commandes/{commande_id}/livraison", status_code=201)
def ajouter_livraison(
    commande_id: int,
    data: LivraisonCreate,
    db: DbSession,
    utilisateur: Tailleur,
):
    commande = db.get(Commande, commande_id)

    if commande is None:
        raise NonTrouve("Commande introuvable.")

    try:
        return commande_service.planifier_livraison(
            db, commande, data.mode, data.date_prevue,
            data.adresse, data.livreur, data.notes
        )
    except ValueError as erreur:
        raise DonneesInvalides(str(erreur))


@router.patch("/commandes/{commande_id}/livraison/confirmer")
def confirmer_livraison(
    commande_id: int,
    db: DbSession,
    utilisateur: Tailleur,
):
    commande = db.get(Commande, commande_id)

    if commande is None:
        raise NonTrouve("Commande introuvable.")

    if commande.livraison is None:
        raise NonTrouve("Aucune livraison planifiée.")

    try:
        return commande_service.confirmer_livraison(db, commande.livraison)
    except ValueError as erreur:
        raise DonneesInvalides(str(erreur))
        @router.get("/commandes/statistiques")
def statistiques_commandes(
    db: DbSession,
    _: UtilisateurConnecte
):
    return commande_service.obtenir_statistiques_commandes(db)