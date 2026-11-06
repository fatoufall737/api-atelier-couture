from sqlalchemy import select
from sqlalchemy.orm import Session

from app import security
from app.exceptions import Conflit, NonTrouve
from app.models import Utilisateur
from app.schemas.utilisateur import UtilisateurCreate, UtilisateurUpdate


def creer(db: Session, data: UtilisateurCreate) -> Utilisateur:
    email = data.email.strip().lower()
    if db.scalar(select(Utilisateur.id).where(Utilisateur.email == email)):
        raise Conflit(f"Un compte existe déjà avec l'e-mail {email}")
    utilisateur = Utilisateur(
        email=email,
        nom_complet=data.nom_complet,
        mot_de_passe_hash=security.hasher_mot_de_passe(data.mot_de_passe),
        role=data.role,
    )
    db.add(utilisateur)
    db.flush()
    return utilisateur


def lister(db: Session) -> list[Utilisateur]:
    return list(db.scalars(select(Utilisateur).order_by(Utilisateur.nom_complet)))


def obtenir(db: Session, utilisateur_id: int) -> Utilisateur:
    utilisateur = db.get(Utilisateur, utilisateur_id)
    if utilisateur is None:
        raise NonTrouve(f"Utilisateur {utilisateur_id} introuvable")
    return utilisateur


def modifier(
    db: Session, cible: Utilisateur, data: UtilisateurUpdate, courant: Utilisateur
) -> Utilisateur:
    champs = data.model_dump(exclude_unset=True)

    # RG24 : un administrateur ne peut ni se désactiver ni se retirer son rôle
    if cible.id == courant.id:
        if champs.get("actif") is False:
            raise Conflit("Vous ne pouvez pas désactiver votre propre compte")
        if "role" in champs and champs["role"] != "admin":
            raise Conflit("Vous ne pouvez pas retirer votre propre rôle d'administrateur")

    # Le mot de passe est haché avant d'être enregistré (RG21)
    mot_de_passe = champs.pop("mot_de_passe", None)
    if mot_de_passe is not None:
        cible.mot_de_passe_hash = security.hasher_mot_de_passe(mot_de_passe)

    for nom, valeur in champs.items():
        if valeur is not None:
            setattr(cible, nom, valeur)
    db.flush()
    return cible