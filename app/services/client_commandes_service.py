from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import NonTrouve
from app.models.client import Client
from app.models.commande import Commande
from app.models.mesure import Mesure


def _verifier_client(db: Session, client_id: int) -> None:
    if db.get(Client, client_id) is None:
        raise NonTrouve("Client introuvable.")


def commandes_du_client(
    db: Session, client_id: int, limit: int, offset: int
) -> tuple[list[dict], int]:
    _verifier_client(db, client_id)

    total = db.scalar(
        select(func.count(Commande.id)).where(Commande.client_id == client_id)
    )

    commandes = db.scalars(
        select(Commande)
        .where(Commande.client_id == client_id)
        # La plus récente d'abord
        .order_by(Commande.date_commande.desc(), Commande.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    aujourdhui = date.today()
    items = []
    for commande in commandes:
        prevue = commande.date_livraison_prevue
        items.append(
            {
                "id": commande.id,
                "numero": commande.numero,
                "statut": commande.statut,
                "date_commande": commande.date_commande,
                "date_livraison_prevue": prevue,
                "montant_total": commande.montant_total,
                "montant_paye": commande.montant_paye,
                "solde": commande.montant_total - commande.montant_paye,
                # RG11 : en retard = date prévue dépassée, ni livrée ni annulée
                "en_retard": (
                    prevue is not None
                    and prevue < aujourdhui
                    and commande.statut not in ("livree", "annulee")
                ),
            }
        )
    return items, int(total)


def resume_client(db: Session, client_id: int) -> dict:
    _verifier_client(db, client_id)

    # Les commandes annulées sont exclues
    nb, chiffre, paye, derniere = db.execute(
        select(
            func.count(Commande.id),
            func.coalesce(func.sum(Commande.montant_total), 0),
            func.coalesce(func.sum(Commande.montant_paye), 0),
            func.max(Commande.date_commande),
        ).where(Commande.client_id == client_id, Commande.statut != "annulee")
    ).one()

    nb_mesures = db.scalar(
        select(func.count(Mesure.id)).where(Mesure.client_id == client_id)
    )

    return {
        "nb_commandes": int(nb),
        "chiffre_affaires": int(chiffre),
        "total_paye": int(paye),
        "solde_du": int(chiffre) - int(paye),
        "derniere_commande": derniere,
        "a_des_mesures": nb_mesures > 0,
    }