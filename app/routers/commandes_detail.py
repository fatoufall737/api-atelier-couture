from datetime import date

from fastapi import APIRouter

from app.deps import DbSession, UtilisateurConnecte
from app.exceptions import NonTrouve
from app.models.commande import Commande

router = APIRouter(tags=["Commandes"])


@router.get("/commandes/{commande_id}")
def detail_commande(commande_id: int, db: DbSession, _: UtilisateurConnecte):
    c = db.get(Commande, commande_id)
    if c is None:
        raise NonTrouve("Commande introuvable.")
    liv = c.livraison
    return {
        "id": c.id,
        "numero": c.numero,
        "client_id": c.client_id,
        "mesure_id": c.mesure_id,
        "statut": c.statut,
        "date_commande": c.date_commande,
        "date_livraison_prevue": c.date_livraison_prevue,
        "date_livraison_reelle": c.date_livraison_reelle,
        "remise": c.remise,
        "montant_total": c.montant_total,
        "montant_paye": c.montant_paye,
        "solde": c.montant_total - c.montant_paye,
        "en_retard": c.date_livraison_prevue < date.today()
        and c.statut not in ("livree", "annulee"),
        "notes": c.notes,
        "lignes": [
            {
                "id": l.id,
                "type_vetement_id": l.type_vetement_id,
                "prestation": l.type_vetement.nom,
                "description": l.description,
                "quantite": l.quantite,
                "prix_unitaire": l.prix_unitaire,
                "sous_total": l.quantite * l.prix_unitaire,
            }
            for l in c.lignes
        ],
        "paiements": [
            {
                "id": p.id,
                "montant": p.montant,
                "mode": p.mode,
                "reference": p.reference,
                "date_paiement": p.date_paiement,
            }
            for p in c.paiements
        ],
        "livraison": None if liv is None else {
            "id": liv.id,
            "mode": liv.mode,
            "adresse": liv.adresse,
            "livreur": liv.livreur,
            "date_prevue": liv.date_prevue,
            "date_effective": liv.date_effective,
            "statut": liv.statut,
        },
    }
