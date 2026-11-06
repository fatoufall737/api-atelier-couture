from sqlalchemy import select
from sqlalchemy.orm import Session

from app import security
from app.exceptions import NonAuthentifie
from app.models import Utilisateur

MESSAGE_ECHEC = "Identifiants incorrects"


def authentifier(db: Session, email: str, mot_de_passe: str) -> Utilisateur:
    """RG23 : même message 401 que l'e-mail soit inconnu ou le mot de passe faux."""
    utilisateur = db.scalar(select(Utilisateur).where(Utilisateur.email == email.strip().lower()))
    if utilisateur is None:
        security.verifier_mot_de_passe(mot_de_passe, security.HASH_FACTICE)
        raise NonAuthentifie(MESSAGE_ECHEC)
    if not security.verifier_mot_de_passe(mot_de_passe, utilisateur.mot_de_passe_hash):
        raise NonAuthentifie(MESSAGE_ECHEC)
    if not utilisateur.actif:
        raise NonAuthentifie(MESSAGE_ECHEC)
    return utilisateur