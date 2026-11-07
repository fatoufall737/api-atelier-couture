from datetime import date
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import Conflit, DonneesInvalides
from app.models.client import Client
from app.models.commande import (
    Commande,
    HistoriqueStatut,
    LigneCommande,
    Livraison,
    Paiement,
)
from app.models.mesure import Mesure
from app.schemas.commande import CommandeCreate


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
    db.flush()
    return commande


TRANSITIONS = {
    "en_attente": ["en_coupe", "annulee"],
    "en_coupe": ["en_couture", "annulee"],
    "en_couture": ["essayage", "terminee", "annulee"],
    "essayage": ["retouches", "terminee", "annulee"],
    "retouches": ["essayage", "terminee", "annulee"],
    "terminee": ["livree"],
    "livree": [],
    "annulee": [],
}


def changer_statut_commande(
    db: Session,
    commande: Commande,
    nouveau_statut: str,
    utilisateur_id: int,
    commentaire: str | None = None,
) -> Commande:
    ancien_statut = commande.statut

    if nouveau_statut not in TRANSITIONS:
        raise DonneesInvalides(f"Statut inconnu : {nouveau_statut}.")

    if nouveau_statut == ancien_statut:
        raise Conflit(f"La commande est déjà au statut {ancien_statut}.")

    if nouveau_statut == "livree":
        raise Conflit(
            "Le statut livree ne peut pas être posé ici : "
            "il résulte de la confirmation de livraison."
        )

    possibles = TRANSITIONS[ancien_statut]
    if nouveau_statut not in possibles:
        liste = ", ".join(sorted(possibles)) or "aucun"
        raise Conflit(
            f"Transition interdite : {ancien_statut} → {nouveau_statut}. "
            f"Statuts possibles : {liste}"
        )

    if (
        nouveau_statut == "annulee"
        and commande.montant_paye > 0
        and not (commentaire and commentaire.strip())
    ):
        raise DonneesInvalides(
            "Cette commande a reçu un acompte : indiquez dans le commentaire "
            "ce que devient l'argent (remboursement, avoir...)."
        )

    commande.statut = nouveau_statut
    db.add(
        HistoriqueStatut(
            commande_id=commande.id,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            commentaire=commentaire,
            utilisateur_id=utilisateur_id,
        )
    )
    db.flush()
    return commande