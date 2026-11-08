from collections import defaultdict
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import DonneesInvalides
from app.models.catalogue import TypeVetement
from app.models.client import Client
from app.models.commande import Commande, LigneCommande, Livraison, Paiement

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


def chiffre_affaires_par_periode(
    db: Session, granularite: str, date_debut: date, date_fin: date
) -> list[dict]:
    if date_debut > date_fin:
        raise DonneesInvalides("date_debut doit être antérieure à date_fin.")

    def periode(jour) -> str:
        if hasattr(jour, "date"):  # au cas où la colonne contient une heure
            jour = jour.date()
        return jour.isoformat() if granularite == "jour" else jour.strftime("%Y-%m")

    periodes = defaultdict(lambda: {"chiffre_affaires": 0, "encaisse": 0})

    # Chiffre d'affaires : commandes non annulées, datées à la date de commande
    commandes = db.execute(
        select(Commande.date_commande, Commande.montant_total).where(
            Commande.statut != "annulee",
            Commande.date_commande >= date_debut,
            Commande.date_commande <= date_fin,
        )
    ).all()
    for jour, montant in commandes:
        periodes[periode(jour)]["chiffre_affaires"] += montant

    # Encaissé : paiements datés à leur date de paiement
    paiements = db.execute(
        select(Paiement.date_paiement, Paiement.montant).where(
            Paiement.date_paiement >= date_debut,
            Paiement.date_paiement <= date_fin,
        )
    ).all()
    for jour, montant in paiements:
        periodes[periode(jour)]["encaisse"] += montant

    # Seules les périodes avec de l'activité apparaissent, triées dans l'ordre
    return [{"periode": nom, **valeurs} for nom, valeurs in sorted(periodes.items())]


def ventes_par_type_vetement(
    db: Session, date_debut: date, date_fin: date
) -> list[dict]:
    if date_debut > date_fin:
        raise DonneesInvalides("date_debut doit être antérieure à date_fin.")

    # Quantité vendue et chiffre d'affaires AVANT remise, par type de vêtement.
    # Commandes annulées exclues, période sur la date de commande.
    chiffre = func.sum(LigneCommande.quantite * LigneCommande.prix_unitaire)
    lignes = db.execute(
        select(
            TypeVetement.id,
            TypeVetement.nom,
            func.sum(LigneCommande.quantite),
            chiffre,
        )
        .join(LigneCommande, LigneCommande.type_vetement_id == TypeVetement.id)
        .join(Commande, Commande.id == LigneCommande.commande_id)
        .where(
            Commande.statut != "annulee",
            Commande.date_commande >= date_debut,
            Commande.date_commande <= date_fin,
        )
        .group_by(TypeVetement.id, TypeVetement.nom)
        .order_by(chiffre.desc(), TypeVetement.nom)
    ).all()

    return [
        {
            "type_vetement_id": identifiant,
            "nom": nom,
            "quantite_vendue": int(quantite),
            "chiffre_affaires": int(montant),
        }
        for identifiant, nom, quantite, montant in lignes
    ]


def meilleurs_clients(
    db: Session, date_debut: date, date_fin: date, limite: int
) -> list[dict]:
    if date_debut > date_fin:
        raise DonneesInvalides("date_debut doit être antérieure à date_fin.")

    # Commandes non annulées de la période, regroupées par client
    chiffre = func.sum(Commande.montant_total)
    lignes = db.execute(
        select(
            Client.id,
            Client.nom,
            Client.prenom,
            func.count(Commande.id),
            chiffre,
            func.sum(Commande.montant_total - Commande.montant_paye),
        )
        .join(Commande, Commande.client_id == Client.id)
        .where(
            Commande.statut != "annulee",
            Commande.date_commande >= date_debut,
            Commande.date_commande <= date_fin,
        )
        .group_by(Client.id, Client.nom, Client.prenom)
        .order_by(chiffre.desc(), Client.nom)
        .limit(limite)
    ).all()

    return [
        {
            "client_id": identifiant,
            "client_nom": f"{prenom} {nom}",
            "nb_commandes": int(nombre),
            "chiffre_affaires": int(montant),
            "solde_du": int(solde),
        }
        for identifiant, nom, prenom, nombre, montant, solde in lignes
    ]


def commandes_impayees(db: Session, limit: int, offset: int) -> tuple[list[dict], int]:
    # Commandes non annulées dont le solde n'est pas à zéro
    solde = Commande.montant_total - Commande.montant_paye
    conditions = (Commande.statut != "annulee", solde > 0)

    total = db.scalar(select(func.count(Commande.id)).where(*conditions))

    lignes = db.execute(
        select(Commande, Client)
        .join(Client, Client.id == Commande.client_id)
        .where(*conditions)
        # Les plus urgentes d'abord : date prévue la plus proche
        .order_by(Commande.date_livraison_prevue.asc().nulls_last(), Commande.id)
        .limit(limit)
        .offset(offset)
    ).all()

    aujourdhui = date.today()
    items = []
    for commande, client in lignes:
        prevue = commande.date_livraison_prevue
        items.append(
            {
                "id": commande.id,
                "numero": commande.numero,
                "client_id": client.id,
                "client_nom": f"{client.prenom} {client.nom}",
                "statut": commande.statut,
                "montant_total": commande.montant_total,
                "montant_paye": commande.montant_paye,
                "solde": commande.montant_total - commande.montant_paye,
                "date_livraison_prevue": prevue,
                "en_retard": prevue is not None and prevue < aujourdhui,
            }
        )
    return items, int(total)