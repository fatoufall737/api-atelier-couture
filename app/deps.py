from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import AccesInterdit, NonAuthentifie
from app.models import Utilisateur
from app.security import decoder_jeton

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    jeton: Annotated[str | None, Depends(oauth2_scheme)], db: DbSession
) -> Utilisateur:
    if not jeton:
        raise NonAuthentifie("Authentification requise")
    try:
        utilisateur_id = int(decoder_jeton(jeton)["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise NonAuthentifie("Jeton invalide ou expiré")
    utilisateur = db.get(Utilisateur, utilisateur_id)
    # RG22 : un compte désactivé est refusé même avec un jeton encore valide
    if utilisateur is None or not utilisateur.actif:
        raise NonAuthentifie("Compte inexistant ou désactivé")
    return utilisateur


def exiger_roles(*roles: str):
    """L'administrateur est toujours autorisé."""

    def verifier(utilisateur: Annotated[Utilisateur, Depends(get_current_user)]) -> Utilisateur:
        if utilisateur.role != "admin" and utilisateur.role not in roles:
            raise AccesInterdit()
        return utilisateur

    return verifier


UtilisateurConnecte = Annotated[Utilisateur, Depends(get_current_user)]
Admin = Annotated[Utilisateur, Depends(exiger_roles())]
Accueil = Annotated[Utilisateur, Depends(exiger_roles("accueil"))]
Tailleur = Annotated[Utilisateur, Depends(exiger_roles("tailleur"))]