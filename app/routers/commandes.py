from fastapi import Query
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


@router.get("/commandes")
def lister_commandes(
    db: DbSession,
    _: UtilisateurConnecte,
    statut: str | None = None,
    client_id: int | None = None,
    en_retard: bool | None = None,
    date_min: date | None = None,
    date_max: date | None = None,
    numero: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    from sqlalchemy import and_, func
    from app.models.client import Client

    retard = and_(
        Commande.date_livraison_prevue < date.today(),
        Commande.statut.notin_(["livree", "annulee"]),
    )
    conds = []
    if statut:
        conds.append(Commande.statut == statut)
    if client_id:
        conds.append(Commande.client_id == client_id)
    if en_retard is True:
        conds.append(retard)
    if en_retard is False:
        conds.append(~retard)
    if date_min:
        conds.append(Commande.date_commande >= date_min)
    if date_max:
        conds.append(Commande.date_commande <= date_max)
    if numero:
        conds.append(Commande.numero.ilike("%" + numero + "%"))

    total = db.scalar(select(func.count(Commande.id)).where(*conds)) or 0
    rows = db.execute(
        select(Commande, Client)
        .join(Client, Commande.client_id == Client.id)
        .where(*conds)
        .order_by(Commande.date_commande.desc(), Commande.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    items = []
    for c, cli in rows:
        items.append({
            "id": c.id,
            "numero": c.numero,
            "client_id": c.client_id,
            "client_nom": cli.prenom + " " + cli.nom,
            "statut": c.statut,
            "date_commande": c.date_commande,
            "date_livraison_prevue": c.date_livraison_prevue,
            "montant_total": c.montant_total,
            "montant_paye": c.montant_paye,
            "solde": c.montant_total - c.montant_paye,
            "en_retard": c.date_livraison_prevue < date.today()
            and c.statut not in ("livree", "annulee"),
        })
    return {"items": items, "total": total, "limit": limit, "offset": offset}


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


