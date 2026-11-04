from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app import security
from app.deps import DbSession, UtilisateurConnecte
from app.schemas.auth import Token
from app.schemas.utilisateur import UtilisateurRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    utilisateur = auth_service.authentifier(db, form.username, form.password)
    jeton, expires_in = security.creer_jeton(utilisateur.id)
    return Token(access_token=jeton, expires_in=expires_in)


@router.get("/me", response_model=UtilisateurRead)
def moi(utilisateur: UtilisateurConnecte):
    return utilisateur