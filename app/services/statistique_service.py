from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.commande import Commande, Livraison, Paiement

STATUTS = [
    "en_attente",
    "en_coupe",
    "en_couture",
    "essayage",
    "retouches",
    "terminee",
    "livree",
    "annulee",
]


def tableau_de_bord(db: Session) -> dict:
    aujourdhui = date.today()
    debut_mois = aujourdhui.replace(day=1)
    if debut_mois.month == 12:
        mois_suivant = date(debut_mois.year + 1, 1, 1)
    else:
        mois_suivant = date(debut_mois.year, debut_mois.month + 1, 1)

    # Chiffre d'affaires du mois : commandes non annulées, datées à la date de commande
    ca_mois, nb_mois = db.execute(
        select(
            func.coalesce(func.sum(Commande.montant_total), 0),
            func.count(Commande.id),
        ).where(
            Commande.statut != "annulee",
            Commande.date_commande >= debut_mois,
            Commande.date_commande < mois_suivant,
        )
    ).one()

    # Encaissé du mois : paiements datés à leur date de paiement
    encaisse_mois = db.scalar(
        select(func.coalesce(func.sum(Paiement.montant), 0)).where(
            Paiement.date_paiement >= debut_mois,
            Paiement.date_paiement < mois_suivant,
        )
    )

    # Reste à encaisser : somme des soldes des commandes non annulées
    reste = db.scalar(
        select(
            func.coalesce(
                func.sum(Commande.montant_total - Commande.montant_paye), 0
            )
        ).where(Commande.statut != "annulee")
    )

    # Nombre de commandes par statut, tous les statuts présents, même à 0
    par_statut = {statut: 0 for statut in STATUTS}
    lignes = db.execute(
        select(Commande.statut, func.count(Commande.id)).group_by(Commande.statut)
    ).all()
    for statut, nombre in lignes:
        par_statut[statut] = nombre

    # RG11 : en retard = date prévue dépassée, ni livrée ni annulée
    en_retard = db.scalar(
        select(func.count(Commande.id)).where(
            Commande.date_livraison_prevue < aujourdhui,
            Commande.statut.not_in(["livree", "annulee"]),
        )
    )

    pretes = db.scalar(
        select(func.count(Commande.id)).where(Commande.statut == "terminee")
    )

    livraisons_du_jour = db.scalar(
        select(func.count(Livraison.id)).where(
            Livraison.date_prevue == aujourdhui,
            Livraison.statut == "planifiee",
        )
    )

    return {
        "chiffre_affaires_mois": int(ca_mois),
        "encaisse_mois": int(encaisse_mois),
        "nb_commandes_mois": int(nb_mois),
        "reste_a_encaisser": int(reste),
        "commandes_par_statut": par_statut,
        "nb_commandes_en_retard": int(en_retard),
        "commandes_pretes_a_livrer": int(pretes),
        "livraisons_du_jour": int(livraisons_du_jour),
    }