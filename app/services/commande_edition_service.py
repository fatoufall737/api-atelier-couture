from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import Conflit, DonneesInvalides, NonTrouve
from app.models.catalogue import TypeVetement
from app.models.commande import Commande, LigneCommande, Paiement
from app.models.mesure import Mesure

STATUTS_FINAUX = ("livree", "annulee")


def get_commande(db: Session, commande_id: int) -> Commande:
    commande = db.get(Commande, commande_id)
    if not commande:
        raise NonTrouve("Commande introuvable")
    return commande


def recalculer_montants(commande: Commande) -> None:
    """RG7 : total = somme(qte x prix) - remise ; le total ne passe jamais sous le payé."""
    somme = sum(l.quantite * l.prix_unitaire for l in commande.lignes)
    if commande.remise > somme:
        raise DonneesInvalides(
            f"La remise ({commande.remise} FCFA) dépasse la somme des prestations ({somme} FCFA)"
        )
    total = somme - commande.remise
    if total < commande.montant_paye:
        raise Conflit(
            f"Impossible : le nouveau total ({total} FCFA) serait inférieur "
            f"au montant déjà payé ({commande.montant_paye} FCFA)"
        )
    commande.montant_total = total


def _verifier_modifiable(commande: Commande) -> None:
    if commande.statut in STATUTS_FINAUX:
        raise Conflit(f"Commande {commande.statut} : elle n'est plus modifiable")


def _verifier_lignes_modifiables(commande: Commande) -> None:
    _verifier_modifiable(commande)
    if commande.statut != "en_attente":
        raise Conflit("Les lignes ne sont modifiables que tant que la commande est « en_attente »")


def modifier_commande(db: Session, commande_id: int, donnees: dict) -> Commande:
    commande = get_commande(db, commande_id)
    _verifier_modifiable(commande)

    if donnees.get("mesure_id") is not None:
        mesure = db.get(Mesure, donnees["mesure_id"])
        if not mesure:
            raise NonTrouve("Mesure introuvable")
        if mesure.client_id != commande.client_id:
            raise DonneesInvalides("Ces mesures n'appartiennent pas au client de la commande")

    if donnees.get("date_livraison_prevue") and donnees["date_livraison_prevue"] < commande.date_commande:
        raise DonneesInvalides("La date de livraison prévue ne peut pas précéder la date de commande")

    if "remise" in donnees and donnees["remise"] is None:
        donnees.pop("remise")
    if "date_livraison_prevue" in donnees and donnees["date_livraison_prevue"] is None:
        donnees.pop("date_livraison_prevue")

    for champ, valeur in donnees.items():
        setattr(commande, champ, valeur)
    recalculer_montants(commande)
    db.flush()
    return commande


def ajouter_ligne(db: Session, commande_id: int, donnees: dict) -> Commande:
    commande = get_commande(db, commande_id)
    _verifier_lignes_modifiables(commande)

    type_vetement = db.get(TypeVetement, donnees["type_vetement_id"])
    if not type_vetement:
        raise NonTrouve("Prestation introuvable dans le catalogue")
    if not type_vetement.actif:
        raise DonneesInvalides(f"La prestation « {type_vetement.nom} » n'est plus commandable")

    prix = donnees.get("prix_unitaire")
    commande.lignes.append(
        LigneCommande(
            type_vetement_id=type_vetement.id,
            description=donnees.get("description"),
            quantite=donnees["quantite"],
            prix_unitaire=type_vetement.prix_base if prix is None else prix,
        )
    )
    db.flush()
    recalculer_montants(commande)
    db.flush()
    return commande


def retirer_ligne(db: Session, commande_id: int, ligne_id: int) -> Commande:
    commande = get_commande(db, commande_id)
    ligne = next((l for l in commande.lignes if l.id == ligne_id), None)
    if not ligne:
        raise NonTrouve("Ligne introuvable dans cette commande")
    _verifier_lignes_modifiables(commande)
    if len(commande.lignes) <= 1:
        raise Conflit("Une commande doit garder au moins une ligne")

    commande.lignes.remove(ligne)
    db.delete(ligne)
    db.flush()
    recalculer_montants(commande)
    db.flush()
    return commande


def lister_paiements(db: Session, commande_id: int) -> list[Paiement]:
    get_commande(db, commande_id)
    return list(db.scalars(
        select(Paiement).where(Paiement.commande_id == commande_id).order_by(Paiement.id)
    ))


def annuler_paiement(db: Session, paiement_id: int) -> None:
    paiement = db.get(Paiement, paiement_id)
    if not paiement:
        raise NonTrouve("Paiement introuvable")
    commande = paiement.commande
    commande.paiements.remove(paiement)
    db.delete(paiement)
    db.flush()
    commande.montant_paye = sum(p.montant for p in commande.paiements)
    db.flush()


def encaisser_paiement(db: Session, commande_id: int, donnees: dict, utilisateur_id: int) -> Paiement:
    from datetime import date
    commande = get_commande(db, commande_id)
    if commande.statut == "annulee":
        raise Conflit("Impossible d'encaisser un paiement sur une commande annulee")
    date_paiement = donnees.get("date_paiement") or date.today()
    if date_paiement > date.today():
        raise DonneesInvalides("La date de paiement ne peut pas etre dans le futur")
    solde = commande.montant_total - commande.montant_paye
    if donnees["montant"] > solde:
        raise Conflit(
            f"Le paiement ({donnees['montant']} FCFA) depasse le solde restant ({solde} FCFA)"
        )
    paiement = Paiement(
        commande_id=commande.id,
        montant=donnees["montant"],
        mode=donnees["mode"],
        reference=donnees.get("reference"),
        date_paiement=date_paiement,
        enregistre_par_id=utilisateur_id,
    )
    commande.paiements.append(paiement)
    db.flush()
    commande.montant_paye = sum(x.montant for x in commande.paiements)
    db.flush()
    return paiement


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


def changer_statut(db: Session, commande_id: int, nouveau: str, commentaire, utilisateur) -> Commande:
    from app.exceptions import AccesInterdit
    from app.models.commande import HistoriqueStatut

    commande = get_commande(db, commande_id)
    ancien = commande.statut

    if nouveau == "annulee" and utilisateur.role == "tailleur":
        raise AccesInterdit("Le tailleur ne peut pas annuler une commande")
    if nouveau == ancien:
        raise Conflit(f"La commande est déjà au statut {ancien}")
    if nouveau == "livree":
        raise Conflit("Le statut livrée résulte de la confirmation de livraison")
    possibles = [x for x in TRANSITIONS[ancien] if x != "livree"]
    if nouveau not in possibles:
        liste = ", ".join(sorted(possibles)) or "aucun"
        raise Conflit(f"Transition interdite : {ancien} -> {nouveau}. Statuts possibles : {liste}")
    if nouveau == "annulee" and commande.montant_paye > 0 and not (commentaire or "").strip():
        raise DonneesInvalides(
            "Un commentaire est obligatoire pour annuler une commande ayant recu un acompte "
            "(remboursement, avoir...)"
        )

    commande.statut = nouveau
    commande.historique.append(HistoriqueStatut(
        ancien_statut=ancien, nouveau_statut=nouveau,
        commentaire=commentaire, utilisateur_id=utilisateur.id,
    ))
    db.flush()
    return commande
