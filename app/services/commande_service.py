from datetime import date
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.commande import Commande, LigneCommande, HistoriqueStatut
from app.models.client import Client
from app.models.mesure import Mesure
from app.schemas.commande import CommandeCreate
from sqlalchemy import select
from app.models.commande import Paiement
from app.models.commande import Livraison
from sqlalchemy import func

def creer_commande(
    db: Session,
    donnees: CommandeCreate,
    cree_par_id: int
) -> Commande:

    client = db.get(Client, donnees.client_id)

    if client is None:
        raise ValueError("Client introuvable.")

    if donnees.mesure_id is not None:
        mesure = db.get(Mesure, donnees.mesure_id)

        if mesure is None or mesure.client_id != donnees.client_id:
            raise ValueError("Mensuration introuvable pour ce client.")

    sous_total = sum(
        ligne.quantite * ligne.prix_unitaire
        for ligne in donnees.lignes
    )

    if donnees.remise > sous_total:
        raise ValueError("La remise ne peut pas dépasser le montant total.")

    montant_total = sous_total - donnees.remise

    commande = Commande(
        numero=f"TEMP-{uuid4().hex}",
        client_id=donnees.client_id,
        mesure_id=donnees.mesure_id,
        date_livraison_prevue=donnees.date_livraison_prevue,
        remise=donnees.remise,
        montant_total=montant_total,
        montant_paye=0,
        notes=donnees.notes,
        cree_par_id=cree_par_id,
    )

    for ligne in donnees.lignes:
        commande.lignes.append(
            LigneCommande(
                type_vetement_id=ligne.type_vetement_id,
                description=ligne.description,
                quantite=ligne.quantite,
                prix_unitaire=ligne.prix_unitaire,
            )
        )

    db.add(commande)
    db.flush()

    commande.numero = f"CMD-{date.today().year}-{commande.id:05d}"

    commande.historique.append(
        HistoriqueStatut(
            ancien_statut=None,
            nouveau_statut="en_attente",
            commentaire="Création de la commande.",
            utilisateur_id=cree_par_id,
        )
    )

    db.commit()
    db.refresh(commande)

    return commande
    def changer_statut_commande(
    db: Session,
    commande: Commande,
    nouveau_statut: str,
    utilisateur_id: int,
    commentaire: str | None = None,
) -> Commande:

    statuts_autorises = {
        "en_attente",
        "en_coupe",
        "en_confection",
        "en_finition",
        "terminee",
        "livree",
        "annulee",
    }

    if nouveau_statut not in statuts_autorises:
        raise ValueError("Statut de commande invalide.")

    ancien_statut = commande.statut

    if ancien_statut == nouveau_statut:
        raise ValueError("La commande possède déjà ce statut.")

    commande.statut = nouveau_statut

    commande.historique.append(
        HistoriqueStatut(
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            commentaire=commentaire,
            utilisateur_id=utilisateur_id,
        )
    )

    db.commit()
    db.refresh(commande)

    return commande
    def obtenir_historique_statuts(
    db: Session,
    commande_id: int
) -> list[HistoriqueStatut]:

    requete = (
        select(HistoriqueStatut)
        .where(HistoriqueStatut.commande_id == commande_id)
        .order_by(HistoriqueStatut.date_changement.asc())
    )

    return db.scalars(requete).all()
    def enregistrer_paiement(
    db: Session,
    commande: Commande,
    montant: int,
    mode: str,
    utilisateur_id: int,
    reference: str | None = None,
) -> Paiement:

    modes_autorises = {
        "especes",
        "wave",
        "orange_money",
        "virement",
        "cheque",
    }

    if montant <= 0:
        raise ValueError("Le montant du paiement doit être positif.")

    if mode not in modes_autorises:
        raise ValueError("Mode de paiement invalide.")

    if montant > commande.solde:
        raise ValueError("Le paiement dépasse le solde restant.")

    paiement = Paiement(
        commande_id=commande.id,
        montant=montant,
        mode=mode,
        reference=reference,
        enregistre_par_id=utilisateur_id,
    )

    commande.montant_paye += montant

    db.add(paiement)
    db.commit()
    db.refresh(paiement)

    return paiement
    def planifier_livraison(
    db: Session,
    commande: Commande,
    mode: str,
    date_prevue: date,
    adresse: str | None = None,
    livreur: str | None = None,
    notes: str | None = None,
) -> Livraison:

    modes_autorises = {"retrait_atelier", "domicile"}

    if mode not in modes_autorises:
        raise ValueError("Mode de livraison invalide.")

    if mode == "domicile" and not adresse:
        raise ValueError("Une adresse est obligatoire pour une livraison à domicile.")

    if commande.livraison is not None:
        raise ValueError("Une livraison est déjà planifiée pour cette commande.")

    livraison = Livraison(
        commande_id=commande.id,
        mode=mode,
        date_prevue=date_prevue,
        adresse=adresse,
        livreur=livreur,
        notes=notes,
        statut="planifiee",
    )

    db.add(livraison)
    db.commit()
    db.refresh(livraison)

    return livraison
    def confirmer_livraison(
    db: Session,
    livraison: Livraison,
) -> Livraison:

    if livraison.statut == "livree":
        raise ValueError("Cette livraison est déjà confirmée.")

    livraison.statut = "livree"
    livraison.date_effective = date.today()

    livraison.commande.statut = "livree"

    livraison.commande.historique.append(
        HistoriqueStatut(
            ancien_statut="terminee",
            nouveau_statut="livree",
            commentaire="Livraison confirmée.",
            utilisateur_id=livraison.commande.cree_par_id,
        )
    )

    db.commit()
    db.refresh(livraison)

    return livraison
    def obtenir_statistiques_commandes(db: Session) -> dict:
    total_commandes = db.scalar(
        select(func.count(Commande.id))
    ) or 0

    chiffre_affaires = db.scalar(
        select(func.sum(Commande.montant_total))
        .where(Commande.statut != "annulee")
    ) or 0

    montant_encaisse = db.scalar(
        select(func.sum(Commande.montant_paye))
    ) or 0

    commandes_par_statut = db.execute(
        select(Commande.statut, func.count(Commande.id))
        .group_by(Commande.statut)
    ).all()

    return {
        "total_commandes": total_commandes,
        "chiffre_affaires": chiffre_affaires,
        "montant_encaisse": montant_encaisse,
        "commandes_par_statut": {
            statut: nombre
            for statut, nombre in commandes_par_statut
        },
    }